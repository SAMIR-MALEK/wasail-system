# pages/inventory.py
import streamlit as st, pandas as pd
from datetime import datetime
from utils.sheets import read_df, append_row, gen_id, get_stock_df, next_inventory_number

def show_inventory():
    st.markdown("## 📋 الجرد الدوري للمخزن")
    tabs = st.tabs(["➕ جلسة جرد جديدة","📂 سجل الجرد"])
    with tabs[0]: _new()
    with tabs[1]: _history()

def _new():
    st.markdown("### ➕ بدء جلسة جرد")
    products_df = read_df("products")
    stock_df    = get_stock_df()
    active      = products_df[products_df["active"].astype(str).str.strip().str.upper()=="TRUE"] if not products_df.empty else pd.DataFrame()
    if active.empty: st.warning("لا منتجات"); return

    from config import DEFAULT_CATEGORIES
    cats_df = read_df("categories")
    cat_list = list(cats_df[cats_df["active"].astype(str).str.strip().str.upper()=="TRUE"]["name"]) if not cats_df.empty else DEFAULT_CATEGORIES
    cat = st.selectbox("تصفية بالفئة", ["الكل"]+cat_list)
    scope = st.selectbox("نطاق الجرد", ["جرد شامل","جرد فئة","جرد عينة"])
    prods = active if cat=="الكل" else active[active["category_name"]==cat]
    st.info(f"📦 **{len(prods)}** منتج")
    st.divider()

    rows = []
    for _,p in prods.iterrows():
        pid = str(p.get("id",""))
        r   = stock_df[stock_df["product_id"].astype(str)==pid]
        theo= float(r.iloc[0]["quantity"]) if not r.empty else 0.0
        ic1,ic2,ic3,ic4,ic5 = st.columns([3,1,1,1,2])
        with ic1: st.markdown(f"**{p.get('name','')}**")
        with ic2: st.markdown(f"<small>رمز: {p.get('code','')}</small>",unsafe_allow_html=True)
        with ic3: st.markdown(f"🔵 **{theo:.0f}**")
        with ic4:
            actual = st.number_input("فعلي", min_value=0.0, value=theo,
                                     key=f"inv_{pid}", label_visibility="collapsed")
        with ic5:
            diff=actual-theo
            color="🟢" if diff==0 else ("🔴" if diff<0 else "🟡")
            st.markdown(f"{color} **{diff:+.0f}** {p.get('unit_name',p.get('unit',''))}")
        rows.append({"product_id":pid,"product_name":p.get("name",""),
                     "product_code":p.get("code",""),"unit_name":p.get("unit_name",""),
                     "theoretical_qty":theo,"actual_qty":actual,"difference":actual-theo})

    st.divider()
    notes = st.text_area("ملاحظات الجرد")
    validator = st.text_input("سيُعتمد بواسطة (الاسم)")
    if st.button("💾 حفظ نتائج الجرد", type="primary", use_container_width=True):
        try:
            inv_id = gen_id()
            inv_num= next_inventory_number()
            now    = datetime.now().strftime("%Y-%m-%d %H:%M")
            df_r   = pd.DataFrame(rows)
            diffs  = df_r[df_r["difference"]!=0]
            append_row("inventory",{
                "id":inv_id,"number":inv_num,"date":now,"type":"عادي","scope":scope,
                "conducted_by":st.session_state.user["full_name"],
                "conducted_by_id":st.session_state.user["id"],
                "validated_by":validator,"validated_at":"",
                "status":"completed","started_at":now,"finished_at":now,
                "total_items":len(rows),"items_ok":len(df_r[df_r["difference"]==0]),
                "items_shortage":len(df_r[df_r["difference"]<0]),
                "items_surplus":len(df_r[df_r["difference"]>0]),
                "notes":notes,
            })
            for item in rows:
                append_row("inventory_items",{
                    "id":gen_id(),"inventory_id":inv_id,"inventory_number":inv_num,
                    **item,"unit_cost":"","difference_value":"","location":"المخزن الرئيسي",
                    "notes":"","counted_by":st.session_state.user["full_name"],
                })
            st.success(f"✅ تم حفظ الجرد | رقم: **{inv_num}**")
            if not diffs.empty:
                st.warning(f"⚠️ **{len(diffs)}** منتج بفارق:")
                d2=diffs[["product_name","unit_name","theoretical_qty","actual_qty","difference"]].copy()
                d2.columns=["المنتج","الوحدة","النظري","الفعلي","الفرق"]
                d2["الفرق"]=d2["الفرق"].astype(float).map(lambda x:f"{x:+.0f}")
                st.dataframe(d2,use_container_width=True,hide_index=True)
            else:
                st.success("🎉 لا فوارق!")
        except Exception as e:
            st.error(f"❌ {e}")

def _history():
    st.markdown("### 📂 سجل جلسات الجرد")
    df = read_df("inventory")
    if df.empty: st.info("لا توجد جلسات جرد بعد"); return
    items_df = read_df("inventory_items")
    for _,inv in df[::-1].iterrows():
        with st.expander(f"📋 {inv.get('number','')}  ·  {inv.get('date','')}  ·  {inv.get('conducted_by','')}"):
            s1,s2,s3,s4=st.columns(4)
            s1.metric("إجمالي المنتجات",inv.get("total_items",0))
            s2.metric("✅ مطابق",inv.get("items_ok",0))
            s3.metric("🔴 عجز",inv.get("items_shortage",0))
            s4.metric("🟡 فائض",inv.get("items_surplus",0))
            ti = items_df[items_df["inventory_id"].astype(str)==str(inv["id"])] if not items_df.empty else pd.DataFrame()
            if not ti.empty:
                d=ti[["product_name","unit_name","theoretical_qty","actual_qty","difference"]].copy()
                d.columns=["المنتج","الوحدة","النظري","الفعلي","الفرق"]
                d["الفرق"]=d["الفرق"].astype(float).map(lambda x:f"{x:+.0f}")
                st.dataframe(d,use_container_width=True,hide_index=True)
            if inv.get("notes"): st.markdown(f"**ملاحظات:** {inv['notes']}")
