# pages/catalog.py — كتالوج المنتجات الكامل

import streamlit as st
import pandas as pd
from datetime import datetime
from utils.sheets import read_df, append_row, update_row, gen_id, get_stock_df
from config import has_perm


def show_catalog():
    user = st.session_state.user
    st.markdown("## 📦 كتالوج المنتجات والمواد")

    tabs = st.tabs([
        "📋 المنتجات",
        "🏷️ فئات المنتجات",
        "📐 وحدات القياس",
        "📊 حالة المخزون",
        "🔄 سجل الحركات",
    ])
    with tabs[0]: _products_tab(user)
    with tabs[1]: _categories_tab(user)
    with tabs[2]: _units_tab(user)
    with tabs[3]: _stock_tab()
    with tabs[4]: _movements_tab()


# ══════════════════════════════════════════════
#  المنتجات
# ══════════════════════════════════════════════
def _products_tab(user):
    st.markdown("### 📋 قائمة المنتجات")

    # جلب البيانات
    products_df  = read_df("products")
    categories_df= read_df("categories")
    units_df     = read_df("units")
    stock_df     = get_stock_df()

    active_cats  = categories_df[categories_df["active"].astype(str).str.strip().str.upper()=="TRUE"] if not categories_df.empty else pd.DataFrame()
    active_units = units_df[units_df["active"].astype(str).str.strip().str.upper()=="TRUE"] if not units_df.empty else pd.DataFrame()

    cat_names  = list(active_cats["name"])  if not active_cats.empty  else []
    unit_names = list(active_units["name"]) if not active_units.empty else []
    cat_id_map = dict(zip(active_cats["name"], active_cats["id"]))   if not active_cats.empty  else {}
    unit_id_map= dict(zip(active_units["name"],active_units["id"]))  if not active_units.empty else {}
    unit_sym_map=dict(zip(active_units["name"],active_units["symbol"]))if not active_units.empty else {}

    # ── إضافة منتج ───────────────────────────────────────
    with st.expander("➕ إضافة منتج جديد", expanded=False):
        with st.form("add_product", clear_on_submit=True):
            c1,c2,c3 = st.columns(3)
            with c1:
                name    = st.text_input("اسم المنتج (عربي) ★")
                name_fr = st.text_input("Désignation (Français)")
                code    = st.text_input("الرمز / Code ★", placeholder="PAPER-A4-80G")
            with c2:
                cat_sel  = st.selectbox("الفئة ★", ["-- اختر --"] + cat_names)
                unit_sel = st.selectbox("وحدة القياس ★", ["-- اختر --"] + unit_names)
                brand    = st.text_input("العلامة التجارية / Marque")
                model    = st.text_input("الموديل / Modèle")
            with c3:
                min_stock  = st.number_input("حد التنبيه الأدنى ★", min_value=0.0, value=5.0, step=1.0)
                max_stock  = st.number_input("الحد الأقصى للمخزون", min_value=0.0, value=100.0, step=1.0)
                reorder_qty= st.number_input("كمية إعادة الطلب", min_value=0.0, value=20.0, step=1.0)
            desc  = st.text_area("الوصف / Description", height=60)
            specs = st.text_area("المواصفات التقنية", height=60)

            if st.form_submit_button("✅ إضافة المنتج", type="primary", use_container_width=True):
                errs = []
                if not name.strip(): errs.append("اسم المنتج مطلوب")
                if not code.strip(): errs.append("الرمز مطلوب")
                if cat_sel == "-- اختر --": errs.append("اختر الفئة")
                if unit_sel == "-- اختر --": errs.append("اختر وحدة القياس")
                # تحقق من تفرد الرمز
                if not products_df.empty and code.strip() in list(products_df.get("code",[])):
                    errs.append(f"الرمز «{code}» موجود مسبقاً")
                if errs:
                    for e in errs: st.error(f"❌ {e}")
                else:
                    try:
                        pid = gen_id()
                        append_row("products", {
                            "id": pid, "code": code.strip().upper(),
                            "name": name.strip(), "name_fr": name_fr.strip(),
                            "category_id": cat_id_map.get(cat_sel,""),
                            "category_name": cat_sel,
                            "unit_id": unit_id_map.get(unit_sel,""),
                            "unit_name": unit_sel,
                            "unit_symbol": unit_sym_map.get(unit_sel,""),
                            "min_stock": min_stock, "max_stock": max_stock,
                            "reorder_qty": reorder_qty,
                            "description": desc.strip(),
                            "specifications": specs.strip(),
                            "brand": brand.strip(), "model": model.strip(),
                            "active": "True",
                            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "created_by": user["full_name"],
                        })
                        st.success(f"✅ تمت إضافة: **{name}** | الرمز: `{code.upper()}`")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ {e}")

    # ── البحث والتصفية ────────────────────────────────────
    st.markdown("---")
    fc1,fc2,fc3,fc4 = st.columns([3,2,2,1])
    with fc1: search    = st.text_input("🔍 بحث باسم المنتج أو الرمز")
    with fc2: cat_filt  = st.selectbox("الفئة",["الكل"]+cat_names, key="pf_cat")
    with fc3:
        stock_filt = st.selectbox("حالة المخزون",
            ["الكل","🔴 نفد","🟠 منخفض","🟡 متوسط","🟢 جيد"], key="pf_stock")
    with fc4: show_inactive = st.checkbox("عرض المعطَّل")

    if not products_df.empty:
        df = products_df.copy()
        if not show_inactive:
            df = df[df["active"].astype(str).str.strip().str.upper()=="TRUE"]
        if search:
            df = df[
                df["name"].str.contains(search, case=False, na=False) |
                df["code"].str.contains(search, case=False, na=False) |
                df.get("name_fr",pd.Series()).str.contains(search, case=False, na=False)
            ]
        if cat_filt != "الكل":
            df = df[df["category_name"]==cat_filt]

        # إضافة بيانات المخزون
        if not stock_df.empty:
            df = df.merge(
                stock_df[["product_id","quantity","available_qty"]],
                left_on="id", right_on="product_id", how="left"
            )
            df["quantity"]      = df.get("quantity",0).fillna(0)
            df["available_qty"] = df.get("available_qty",0).fillna(0)
        else:
            df["quantity"] = 0
            df["available_qty"] = 0

        df["min_stock"] = df["min_stock"].astype(float)
        df["الحالة"] = df.apply(lambda r:
            "🔴 نفد"    if r["quantity"]==0 else
            "🟠 منخفض"  if r["quantity"]<=r["min_stock"] else
            "🟡 متوسط"  if r["quantity"]<=r["min_stock"]*1.5 else
            "🟢 جيد", axis=1
        )

        if stock_filt != "الكل":
            word = stock_filt.split()[1]
            df = df[df["الحالة"].str.contains(word, na=False)]

        # عرض الجدول
        show_cols = {
            "code":"الرمز","name":"الاسم","name_fr":"بالفرنسية",
            "category_name":"الفئة","unit_name":"الوحدة","brand":"الماركة",
            "quantity":"الكمية","min_stock":"الحد الأدنى","الحالة":"الحالة",
        }
        avail = {k:v for k,v in show_cols.items() if k in df.columns or k=="الحالة"}
        st.dataframe(
            df[[c for c in avail.keys() if c in df.columns]].rename(columns=avail),
            use_container_width=True, hide_index=True,
        )
        st.caption(f"عدد النتائج: **{len(df)}** منتج")

        # ── تعديل منتج ───────────────────────────────────
        st.markdown("---")
        st.markdown("#### ✏️ تعديل منتج")
        if not df.empty:
            prod_options = dict(zip(df["code"]+" — "+df["name"], df["id"]))
            sel_label = st.selectbox("اختر المنتج", list(prod_options.keys()), key="edit_prod_sel")
            sel_id    = prod_options.get(sel_label,"")
            if sel_id:
                prod_row = df[df["id"]==sel_id].iloc[0].to_dict()
                with st.form("edit_product"):
                    ec1,ec2 = st.columns(2)
                    with ec1:
                        new_name = st.text_input("الاسم", value=prod_row.get("name",""))
                        new_min  = st.number_input("حد التنبيه", value=float(prod_row.get("min_stock",5)), min_value=0.0)
                        new_max  = st.number_input("الحد الأقصى", value=float(prod_row.get("max_stock",100)), min_value=0.0)
                    with ec2:
                        new_brand= st.text_input("الماركة", value=prod_row.get("brand",""))
                        new_desc = st.text_area("الوصف", value=prod_row.get("description",""), height=80)
                        new_active = st.checkbox("نشط", value=str(prod_row.get("active","True"))=="True")
                    if st.form_submit_button("💾 حفظ التعديلات", type="primary"):
                        update_row("products", sel_id, {
                            "name": new_name, "min_stock": new_min,
                            "max_stock": new_max, "brand": new_brand,
                            "description": new_desc,
                            "active": str(new_active),
                        })
                        st.success("✅ تم حفظ التعديلات")
                        st.rerun()
    else:
        st.info("لا توجد منتجات بعد — ابدأ بإضافة المنتجات.")


# ══════════════════════════════════════════════
#  فئات المنتجات
# ══════════════════════════════════════════════
def _categories_tab(user):
    st.markdown("### 🏷️ إدارة فئات المنتجات")
    c1,c2 = st.columns([1,2])

    with c1:
        st.markdown("#### ➕ فئة جديدة")
        with st.form("add_cat", clear_on_submit=True):
            cname = st.text_input("اسم الفئة (عربي) ★")
            cfr   = st.text_input("Nom (Français)")
            cicon = st.text_input("أيقونة Emoji", value="📦", max_chars=4)
            cdesc = st.text_area("وصف", height=60)
            if st.form_submit_button("✅ إضافة", type="primary", use_container_width=True):
                if not cname.strip():
                    st.error("الاسم مطلوب")
                else:
                    try:
                        append_row("categories", {
                            "id": gen_id(), "name": cname.strip(),
                            "name_fr": cfr.strip(), "description": cdesc.strip(),
                            "icon": cicon, "active": "True",
                            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        })
                        st.success(f"✅ {cicon} {cname}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ {e}")

    with c2:
        st.markdown("#### 📋 قائمة الفئات")
        df = read_df("categories")
        if df.empty:
            st.info("لا توجد فئات")
        else:
            active = df[df["active"].astype(str).str.strip().str.upper()=="TRUE"]
            # إضافة عدد المنتجات لكل فئة
            prods = read_df("products")
            if not prods.empty:
                counts = prods[prods["active"].astype(str).str.strip().str.upper()=="TRUE"]["category_name"].value_counts().to_dict()
                active = active.copy()
                active["عدد المنتجات"] = active["name"].map(lambda n: counts.get(n,0))

            show = {c:c for c in ["icon","name","name_fr","عدد المنتجات"] if c in active.columns}
            rename = {"icon":"","name":"الفئة","name_fr":"بالفرنسية"}
            st.dataframe(active[list(show)].rename(columns=rename),
                         use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════
#  وحدات القياس
# ══════════════════════════════════════════════
def _units_tab(user):
    st.markdown("### 📐 وحدات القياس")
    c1,c2 = st.columns([1,2])

    with c1:
        st.markdown("#### ➕ وحدة جديدة")
        with st.form("add_unit", clear_on_submit=True):
            uname  = st.text_input("الاسم (عربي) ★")
            ufr    = st.text_input("Nom (Français)")
            usym   = st.text_input("الرمز ★", max_chars=8, placeholder="kg")
            if st.form_submit_button("✅ إضافة", type="primary", use_container_width=True):
                if not uname.strip() or not usym.strip():
                    st.error("الاسم والرمز مطلوبان")
                else:
                    append_row("units", {
                        "id": gen_id(), "name": uname.strip(),
                        "name_fr": ufr.strip(), "symbol": usym.strip(),
                        "active": "True",
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    })
                    st.success(f"✅ {uname} ({usym})")
                    st.rerun()

    with c2:
        st.markdown("#### 📋 الوحدات الحالية")
        df = read_df("units")
        if not df.empty:
            active = df[df["active"].astype(str).str.strip().str.upper()=="TRUE"]
            st.dataframe(
                active[["name","name_fr","symbol"]].rename(columns={
                    "name":"الاسم","name_fr":"بالفرنسية","symbol":"الرمز"
                }),
                use_container_width=True, hide_index=True
            )


# ══════════════════════════════════════════════
#  حالة المخزون
# ══════════════════════════════════════════════
def _stock_tab():
    st.markdown("### 📊 حالة المخزون الكاملة")
    stock_df    = get_stock_df()
    products_df = read_df("products")

    if stock_df.empty or products_df.empty:
        st.info("لا توجد بيانات مخزون بعد")
        return

    active = products_df[products_df["active"].astype(str).str.strip().str.upper()=="TRUE"]
    merged = active.merge(
        stock_df[["product_id","quantity","available_qty","last_in_date","last_out_date","last_updated"]],
        left_on="id", right_on="product_id", how="left"
    )
    merged["quantity"]      = merged.get("quantity",0).fillna(0)
    merged["available_qty"] = merged.get("available_qty",0).fillna(0)
    merged["min_stock"]     = merged["min_stock"].astype(float)

    merged["الحالة"] = merged.apply(lambda r:
        "🔴 نفد"   if r["quantity"]==0 else
        "🟠 منخفض" if r["quantity"]<=r["min_stock"] else
        "🟡 متوسط" if r["quantity"]<=r["min_stock"]*1.5 else
        "🟢 جيد", axis=1
    )

    # إحصاءات
    s1,s2,s3,s4,s5 = st.columns(5)
    s1.metric("إجمالي المنتجات", len(merged))
    s2.metric("🟢 جيد", len(merged[merged["الحالة"]=="🟢 جيد"]))
    s3.metric("🟡 متوسط", len(merged[merged["الحالة"]=="🟡 متوسط"]))
    s4.metric("🟠 منخفض", len(merged[merged["الحالة"]=="🟠 منخفض"]))
    s5.metric("🔴 نفد", len(merged[merged["الحالة"]=="🔴 نفد"]))

    st.divider()
    filt = st.radio("عرض", ["الكل","🔴 نفد","🟠 منخفض","🟡 متوسط","🟢 جيد"], horizontal=True)
    if filt != "الكل":
        merged = merged[merged["الحالة"].str.contains(filt.split()[1], na=False)]

    show = {
        "code":"الرمز","name":"المنتج","category_name":"الفئة",
        "quantity":"الكمية","available_qty":"المتاح","unit_name":"الوحدة",
        "min_stock":"الحد الأدنى","الحالة":"الحالة",
        "last_updated":"آخر تحديث",
    }
    avail = {k:v for k,v in show.items() if k in merged.columns or k=="الحالة"}
    st.dataframe(merged[[c for c in avail if c in merged.columns]].rename(columns=avail),
                 use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════
#  سجل الحركات
# ══════════════════════════════════════════════
def _movements_tab():
    st.markdown("### 🔄 سجل حركات المخزن")
    df = read_df("stock_movements")
    if df.empty:
        st.info("لا توجد حركات بعد")
        return

    fc1,fc2,fc3 = st.columns(3)
    with fc1: tf = st.selectbox("النوع",["الكل","📥 دخول","📤 خروج"])
    with fc2: search = st.text_input("🔍 بحث")
    with fc3: ref_type = st.selectbox("نوع العملية",["الكل","استلام بضاعة","سند تحويل","جرد"])

    d = df.copy()
    if tf == "📥 دخول":   d = d[d.get("direction",d.get("type",""))=="in"]
    elif tf == "📤 خروج": d = d[d.get("direction",d.get("type",""))=="out"]
    if search:
        d = d[
            d["product_name"].str.contains(search, case=False, na=False) |
            d.get("reference_number", d.get("reference","")).str.contains(search, case=False, na=False)
        ]
    if ref_type != "الكل":
        rt_map = {"استلام بضاعة":"invoice","سند تحويل":"transfer","جرد":"inventory"}
        rt = rt_map.get(ref_type,"")
        if rt and "reference_type" in d.columns:
            d = d[d["reference_type"]==rt]

    dir_col = "direction" if "direction" in d.columns else "type"
    d["النوع"] = d[dir_col].map({"in":"📥 دخول","out":"📤 خروج"})
    ref_col = "reference_number" if "reference_number" in d.columns else "reference"

    show = ["date","النوع","product_name","quantity","unit_name",ref_col,"notes"]
    avail= [c for c in show if c in d.columns]
    rename = {"date":"التاريخ","product_name":"المادة","quantity":"الكمية",
              "unit_name":"الوحدة","notes":"ملاحظات"}
    rename[ref_col] = "المرجع"
    st.dataframe(d[avail][::-1].rename(columns=rename), use_container_width=True, hide_index=True)
    st.caption(f"إجمالي الحركات: **{len(d)}**")
