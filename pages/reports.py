# pages/reports.py — التقارير والإحصاءات الشاملة
import streamlit as st, pandas as pd
from datetime import datetime, timedelta
from utils.sheets import read_df, get_stock_df

def show_reports():
    st.markdown("## 📊 التقارير والإحصاءات")
    tabs=st.tabs(["📦 تقرير المخزون","🔄 تقرير الحركات",
                  "📋 تقرير السندات","🏭 تقرير الموردين","📈 لوحة الأداء"])
    with tabs[0]: _stock_report()
    with tabs[1]: _movements_report()
    with tabs[2]: _transfers_report()
    with tabs[3]: _suppliers_report()
    with tabs[4]: _kpi_dashboard()

def _stock_report():
    st.markdown("### 📦 تقرير المخزون الحالي")
    stock_df=get_stock_df()
    products_df=read_df("products")
    if stock_df.empty or products_df.empty: st.info("لا بيانات"); return
    active=products_df[products_df["active"].astype(str).str.strip().str.upper()=="TRUE"]
    merged=active.merge(stock_df[["product_id","quantity","last_updated"]],
                        left_on="id",right_on="product_id",how="left")
    merged["quantity"]=pd.to_numeric(merged.get("quantity",0),errors="coerce").fillna(0)
    merged["min_stock"]=pd.to_numeric(merged["min_stock"],errors="coerce").fillna(0)

    # إحصاءات
    total_val=0  # لو كان لدينا تكلفة
    c1,c2,c3,c4=st.columns(4)
    c1.metric("إجمالي المنتجات النشطة",len(active))
    c2.metric("منتجات بمخزون نفد",len(merged[merged["quantity"]==0]))
    c3.metric("منتجات تحت الحد الأدنى",len(merged[merged["quantity"]<=merged["min_stock"]]))
    c4.metric("إجمالي الكميات",f"{merged['quantity'].sum():,.0f}")

    st.divider()
    # تحليل بالفئة
    if "category_name" in merged.columns:
        st.markdown("#### توزيع الكميات بالفئة")
        cat_agg=merged.groupby("category_name")["quantity"].sum().sort_values(ascending=False)
        st.bar_chart(cat_agg)

    # جدول كامل
    st.markdown("#### جدول المخزون الكامل")
    merged["الحالة"]=merged.apply(lambda r:
        "🔴 نفد" if r["quantity"]==0 else
        "🟠 منخفض" if r["quantity"]<=r["min_stock"] else "🟢 جيد",axis=1)
    show=["code","name","category_name","quantity","min_stock","unit_name","الحالة","last_updated"]
    avail=[c for c in show if c in merged.columns]
    rename={"code":"الرمز","name":"المنتج","category_name":"الفئة","quantity":"الكمية",
            "min_stock":"الحد الأدنى","unit_name":"الوحدة","last_updated":"آخر تحديث"}
    st.dataframe(merged[avail].rename(columns=rename),use_container_width=True,hide_index=True)

    # تصدير
    csv=merged[avail].rename(columns=rename).to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ تصدير CSV",data=csv,file_name=f"مخزون_{datetime.now().strftime('%Y%m%d')}.csv",mime="text/csv")

def _movements_report():
    st.markdown("### 🔄 تقرير حركات المخزن")
    df=read_df("stock_movements")
    if df.empty: st.info("لا بيانات"); return

    # فلتر التاريخ
    fc1,fc2=st.columns(2)
    with fc1: d_from=st.date_input("من تاريخ",value=datetime.now()-timedelta(days=30))
    with fc2: d_to  =st.date_input("إلى تاريخ",value=datetime.now())

    d=df.copy()
    d["date_only"]=pd.to_datetime(d["date"],errors="coerce").dt.date
    d=d[(d["date_only"]>=d_from)&(d["date_only"]<=d_to)]

    dir_col="direction" if "direction" in d.columns else "type"
    ins =d[d[dir_col]=="in"]
    outs=d[d[dir_col]=="out"]

    c1,c2,c3=st.columns(3)
    c1.metric("إجمالي الحركات",len(d))
    c2.metric("📥 عمليات دخول",len(ins))
    c3.metric("📤 عمليات خروج",len(outs))

    st.markdown("#### الحركات اليومية")
    if not d.empty:
        daily=d.groupby(["date_only",dir_col]).size().unstack(fill_value=0)
        st.bar_chart(daily)

    st.markdown("#### أكثر المواد حركةً")
    if not d.empty:
        top=d["product_name"].value_counts().head(10)
        st.bar_chart(top)

    csv=d.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ تصدير CSV",data=csv,file_name=f"حركات_{datetime.now().strftime('%Y%m%d')}.csv",mime="text/csv")

def _transfers_report():
    st.markdown("### 📋 تقرير سندات التحويل")
    from config import TRANSFER_STATUS
    df=read_df("transfers")
    if df.empty: st.info("لا بيانات"); return

    c1,c2,c3,c4,c5=st.columns(5)
    c1.metric("إجمالي السندات",len(df))
    c2.metric("⏳ معلق",len(df[df["status"]=="pending"]))
    c3.metric("✅ موافق",len(df[df["status"]=="approved"]))
    c4.metric("🚚 منفَّذ",len(df[df["status"]=="executed"]))
    c5.metric("📬 مستلَم",len(df[df["status"]=="received"]))

    c6,c7=st.columns(2)
    with c6:
        st.markdown("**الطلبات حسب المصلحة**")
        st.bar_chart(df["requesting_dept"].value_counts())
    with c7:
        st.markdown("**الطلبات حسب الحالة**")
        st.bar_chart(df["status"].map(lambda s:TRANSFER_STATUS.get(s,{}).get("label",s)).value_counts())

def _suppliers_report():
    st.markdown("### 🏭 تقرير الموردين")
    df=read_df("suppliers")
    inv=read_df("invoices")
    if df.empty: st.info("لا بيانات"); return
    active=df[df["active"].astype(str).str.strip().str.upper()=="TRUE"]
    c1,c2=st.columns(2)
    with c1:
        st.markdown("**التوزيع بالولاية**")
        if "wilaya" in active.columns:
            st.bar_chart(active["wilaya"].value_counts().head(10))
    with c2:
        st.markdown("**التوزيع بالتقييم**")
        if "rating" in active.columns:
            st.bar_chart(active["rating"].value_counts())
    if not inv.empty:
        st.markdown("**أكثر الموردين فواتير**")
        top_sup=inv["supplier_name"].value_counts().head(10)
        st.bar_chart(top_sup)
        total=pd.to_numeric(inv["total_amount"],errors="coerce").sum()
        st.metric("إجمالي قيمة المشتريات",f"{total:,.0f} دج")

def _kpi_dashboard():
    st.markdown("### 📈 لوحة مؤشرات الأداء KPI")
    stock_df=get_stock_df()
    products_df=read_df("products")
    transfers_df=read_df("transfers")
    movements_df=read_df("stock_movements")

    active=products_df[products_df["active"].astype(str).str.strip().str.upper()=="TRUE"] if not products_df.empty else pd.DataFrame()

    # KPI cards
    kpis=[
        ("معدل نفاد المخزون",
         f"{(len(stock_df[stock_df['quantity'].astype(float)==0])/max(len(active),1)*100):.1f}%" if not stock_df.empty else "0%",
         "نسبة المنتجات بمخزون صفر","#ef4444"),
        ("نسبة السندات المكتملة",
         f"{(len(transfers_df[transfers_df['status']=='received'])/max(len(transfers_df),1)*100):.1f}%" if not transfers_df.empty else "0%",
         "السندات المستلمة / الإجمالي","#10b981"),
        ("متوسط الحركات اليومية",
         f"{len(movements_df)/max((datetime.now()-datetime(datetime.now().year,1,1)).days,1):.1f}" if not movements_df.empty else "0",
         "حركة / يوم","#3b82f6"),
        ("عدد المنتجات النشطة",
         str(len(active)),
         "منتج مسجَّل ونشط","#8b5cf6"),
    ]
    cols=st.columns(4)
    for i,(title,val,desc,color) in enumerate(kpis):
        with cols[i]:
            st.markdown(f"""
            <div style="background:white;border:1px solid #e9ecef;border-radius:12px;
                 padding:20px;text-align:center;border-top:4px solid {color};">
                <div style="font-size:2rem;font-weight:900;color:{color}">{val}</div>
                <div style="font-size:.85rem;font-weight:700;color:#333;margin-top:4px">{title}</div>
                <div style="font-size:.72rem;color:#888;margin-top:2px">{desc}</div>
            </div>""",unsafe_allow_html=True)
