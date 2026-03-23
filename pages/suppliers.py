# pages/suppliers.py — إدارة الموردين الكاملة

import streamlit as st
import pandas as pd
from datetime import datetime
from utils.sheets import read_df, append_row, update_row, gen_id


SUPPLIER_TYPES = ["مؤسسة عمومية","شركة خاصة","مؤسسة صغيرة","تاجر تجزئة","مستورد","أخرى"]
WILAYAS = [
    "01 - أدرار","02 - الشلف","03 - الأغواط","04 - أم البواقي","05 - باتنة",
    "06 - بجاية","07 - بسكرة","08 - بشار","09 - البليدة","10 - البويرة",
    "11 - تمنراست","12 - تبسة","13 - تلمسان","14 - تيارت","15 - تيزي وزو",
    "16 - الجزائر","17 - الجلفة","18 - جيجل","19 - سطيف","20 - سعيدة",
    "21 - سكيكدة","22 - سيدي بلعباس","23 - عنابة","24 - قالمة","25 - قسنطينة",
    "26 - المدية","27 - مستغانم","28 - المسيلة","29 - معسكر","30 - ورقلة",
    "31 - وهران","32 - البيض","33 - إليزي","34 - برج بوعريريج","35 - بومرداس",
    "36 - الطارف","37 - تندوف","38 - تيسمسيلت","39 - الوادي","40 - خنشلة",
    "41 - سوق أهراس","42 - تيبازة","43 - ميلة","44 - عين الدفلى","45 - النعامة",
    "46 - عين تموشنت","47 - غرداية","48 - غليزان","49 - المغير","50 - المنيعة",
    "51 - أولاد جلال","52 - برج باجي مختار","53 - بني عباس","54 - تيميمون",
    "55 - تقرت","56 - جانت","57 - عين صالح","58 - عين قزام",
]
RATINGS = ["⭐ ضعيف","⭐⭐ مقبول","⭐⭐⭐ جيد","⭐⭐⭐⭐ جيد جداً","⭐⭐⭐⭐⭐ ممتاز"]
PAYMENT_TERMS = ["نقداً","30 يوم","60 يوم","90 يوم","دفع مسبق","اعتماد مستندي"]


def show_suppliers():
    st.markdown("## 🏭 إدارة الموردين")
    tabs = st.tabs([
        "📋 قائمة الموردين",
        "➕ إضافة مورد",
        "📞 جهات الاتصال",
        "📊 إحصاءات الموردين",
    ])
    with tabs[0]: _list_suppliers()
    with tabs[1]: _add_supplier()
    with tabs[2]: _contacts()
    with tabs[3]: _stats()


# ══════════════════════════════════════════════
#  قائمة الموردين
# ══════════════════════════════════════════════
def _list_suppliers():
    st.markdown("### 📋 الموردون المسجلون")
    df = read_df("suppliers")

    fc1,fc2,fc3 = st.columns(3)
    with fc1: search = st.text_input("🔍 بحث")
    with fc2: type_f = st.selectbox("النوع",["الكل"]+SUPPLIER_TYPES)
    with fc3: rating_f = st.selectbox("التقييم",["الكل"]+RATINGS)

    if df.empty:
        st.info("لا يوجد موردون مسجلون بعد")
        return

    d = df[df["active"].astype(str)=="True"].copy()
    if search:
        d = d[
            d["name"].str.contains(search, case=False, na=False) |
            d.get("nif",pd.Series()).str.contains(search, case=False, na=False) |
            d.get("phone",pd.Series()).str.contains(search, case=False, na=False)
        ]
    if type_f  != "الكل": d = d[d["type"]==type_f]
    if rating_f!= "الكل": d = d[d["rating"]==rating_f]

    # بطاقات للموردين المتميزين
    top = d[d["rating"].str.contains("⭐⭐⭐⭐⭐", na=False)] if not d.empty else pd.DataFrame()
    if not top.empty:
        st.markdown("##### 🌟 الموردون الممتازون")
        cols = st.columns(min(len(top),4))
        for i,(_, row) in enumerate(top.iterrows()):
            if i < 4:
                with cols[i]:
                    st.markdown(f"""
                    <div style="background:linear-gradient(135deg,#ffd700,#ffa500);
                         border-radius:10px;padding:12px;text-align:center;margin-bottom:8px;">
                        <div style="font-size:1.5rem">🏅</div>
                        <div style="font-weight:800;font-size:.9rem">{row.get('name','')}</div>
                        <div style="font-size:.75rem;opacity:.8">{row.get('wilaya','')}</div>
                    </div>""", unsafe_allow_html=True)
        st.markdown("---")

    # الجدول الرئيسي
    show = {
        "code":"الرمز","name":"الاسم","type":"النوع",
        "phone":"الهاتف","wilaya":"الولاية",
        "nif":"NIF","payment_terms":"شروط الدفع","rating":"التقييم",
    }
    avail = {k:v for k,v in show.items() if k in d.columns}
    st.dataframe(d[[c for c in avail if c in d.columns]].rename(columns=avail),
                 use_container_width=True, hide_index=True)
    st.caption(f"إجمالي: **{len(d)}** مورد")

    # تفاصيل مورد
    st.divider()
    st.markdown("#### 🔍 تفاصيل مورد")
    if not d.empty:
        sup_opts = dict(zip(d.get("code",d.index.astype(str))+"  —  "+d["name"], d["id"]))
        sel_lbl  = st.selectbox("اختر المورد", list(sup_opts.keys()))
        sel_id   = sup_opts.get(sel_lbl,"")
        if sel_id:
            r = d[d["id"]==sel_id].iloc[0].to_dict()
            dc1,dc2,dc3 = st.columns(3)
            with dc1:
                st.markdown(f"**الاسم:** {r.get('name','')}")
                st.markdown(f"**النوع:** {r.get('type','')}")
                st.markdown(f"**الهاتف:** {r.get('phone','')}")
                st.markdown(f"**البريد:** {r.get('email','')}")
            with dc2:
                st.markdown(f"**NIF:** {r.get('nif','')}")
                st.markdown(f"**NIS:** {r.get('nis','')}")
                st.markdown(f"**RC:** {r.get('rc','')}")
                st.markdown(f"**الولاية:** {r.get('wilaya','')}")
            with dc3:
                st.markdown(f"**البنك:** {r.get('bank_name','')}")
                st.markdown(f"**الحساب:** {r.get('bank_account','')}")
                st.markdown(f"**شروط الدفع:** {r.get('payment_terms','')}")
                st.markdown(f"**التسليم:** {r.get('delivery_days','')} يوم")
            st.markdown(f"**ملاحظات:** {r.get('notes','—')}")

            # تعديل سريع
            with st.expander("✏️ تعديل المورد"):
                with st.form(f"edit_sup_{sel_id}"):
                    e1,e2 = st.columns(2)
                    with e1:
                        new_phone   = st.text_input("الهاتف", value=r.get("phone",""))
                        new_email   = st.text_input("البريد", value=r.get("email",""))
                        new_rating  = st.selectbox("التقييم", RATINGS,
                                       index=RATINGS.index(r.get("rating",RATINGS[2])) if r.get("rating") in RATINGS else 2)
                    with e2:
                        new_terms   = st.selectbox("شروط الدفع", PAYMENT_TERMS,
                                       index=PAYMENT_TERMS.index(r.get("payment_terms",PAYMENT_TERMS[0])) if r.get("payment_terms") in PAYMENT_TERMS else 0)
                        new_notes   = st.text_area("ملاحظات", value=r.get("notes",""), height=80)
                        new_active  = st.checkbox("نشط", value=str(r.get("active","True"))=="True")
                    if st.form_submit_button("💾 حفظ", type="primary"):
                        update_row("suppliers", sel_id, {
                            "phone": new_phone, "email": new_email,
                            "rating": new_rating, "payment_terms": new_terms,
                            "notes": new_notes, "active": str(new_active),
                        })
                        st.success("✅ تم الحفظ")
                        st.rerun()


# ══════════════════════════════════════════════
#  إضافة مورد
# ══════════════════════════════════════════════
def _add_supplier():
    st.markdown("### ➕ تسجيل مورد جديد")
    user = st.session_state.user

    with st.form("add_supplier", clear_on_submit=True):
        st.markdown("#### معلومات أساسية")
        r1c1, r1c2, r1c3 = st.columns(3)
        with r1c1:
            code    = st.text_input("رمز المورد ★", placeholder="SUP-001")
            name    = st.text_input("اسم المورد (عربي) ★")
            name_fr = st.text_input("Raison Sociale (Français)")
            sup_type= st.selectbox("النوع ★", SUPPLIER_TYPES)
        with r1c2:
            phone   = st.text_input("الهاتف الرئيسي ★")
            phone2  = st.text_input("هاتف ثانوي")
            email   = st.text_input("البريد الإلكتروني")
            fax     = st.text_input("الفاكس")
        with r1c3:
            wilaya  = st.selectbox("الولاية ★", WILAYAS)
            address = st.text_area("العنوان الكامل", height=80)
            rating  = st.selectbox("التقييم المبدئي", RATINGS, index=2)

        st.markdown("---")
        st.markdown("#### المعلومات القانونية والمالية")
        r2c1, r2c2, r2c3 = st.columns(3)
        with r2c1:
            nif          = st.text_input("رقم التعريف الجبائي NIF")
            nis          = st.text_input("رقم التسجيل الإحصائي NIS")
            rc           = st.text_input("رقم السجل التجاري RC")
        with r2c2:
            bank_name    = st.text_input("البنك")
            bank_account = st.text_input("رقم الحساب البنكي")
        with r2c3:
            payment_terms= st.selectbox("شروط الدفع", PAYMENT_TERMS)
            delivery_days= st.number_input("مدة التسليم (أيام)", min_value=0, value=7)
            notes        = st.text_area("ملاحظات", height=70)

        submitted = st.form_submit_button("✅ تسجيل المورد", type="primary", use_container_width=True)

    if submitted:
        errs = []
        if not name.strip():  errs.append("اسم المورد مطلوب")
        if not phone.strip(): errs.append("الهاتف مطلوب")
        if not code.strip():  errs.append("الرمز مطلوب")
        # تحقق تفرد الرمز
        existing = read_df("suppliers")
        if not existing.empty and code.strip() in list(existing.get("code",[])):
            errs.append(f"الرمز «{code}» مستخدم مسبقاً")
        if errs:
            for e in errs: st.error(f"❌ {e}")
            return
        try:
            append_row("suppliers", {
                "id": gen_id(), "code": code.strip().upper(),
                "name": name.strip(), "name_fr": name_fr.strip(),
                "type": sup_type,
                "phone": phone.strip(), "phone2": phone2.strip(),
                "email": email.strip(), "fax": fax.strip(),
                "address": address.strip(), "wilaya": wilaya,
                "nif": nif.strip(), "nis": nis.strip(), "rc": rc.strip(),
                "bank_account": bank_account.strip(), "bank_name": bank_name.strip(),
                "payment_terms": payment_terms,
                "delivery_days": delivery_days,
                "rating": rating, "notes": notes.strip(),
                "active": "True",
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "created_by": user["full_name"],
            })
            st.success(f"✅ تم تسجيل المورد: **{name}** | الرمز: `{code.upper()}`")
        except Exception as e:
            st.error(f"❌ {e}")


# ══════════════════════════════════════════════
#  جهات الاتصال
# ══════════════════════════════════════════════
def _contacts():
    st.markdown("### 📞 جهات اتصال الموردين")
    suppliers_df = read_df("suppliers")
    contacts_df  = read_df("supplier_contacts")

    c1,c2 = st.columns([1,2])
    with c1:
        st.markdown("#### ➕ إضافة جهة اتصال")
        active_sups = suppliers_df[suppliers_df["active"].astype(str)=="True"] if not suppliers_df.empty else pd.DataFrame()
        sup_opts = dict(zip(active_sups["name"], active_sups["id"])) if not active_sups.empty else {}

        with st.form("add_contact", clear_on_submit=True):
            sel_sup = st.selectbox("المورد ★", ["-- اختر --"]+list(sup_opts.keys()))
            fname   = st.text_input("الاسم الكامل ★")
            pos     = st.text_input("المنصب / الصفة")
            cphone  = st.text_input("الهاتف")
            cemail  = st.text_input("البريد")
            cnotes  = st.text_input("ملاحظات")
            if st.form_submit_button("➕ إضافة", type="primary", use_container_width=True):
                if sel_sup == "-- اختر --" or not fname.strip():
                    st.error("المورد والاسم مطلوبان")
                else:
                    append_row("supplier_contacts", {
                        "id": gen_id(),
                        "supplier_id":   sup_opts.get(sel_sup,""),
                        "supplier_name": sel_sup,
                        "full_name":     fname.strip(),
                        "position":      pos.strip(),
                        "phone":         cphone.strip(),
                        "email":         cemail.strip(),
                        "notes":         cnotes.strip(),
                        "active":        "True",
                    })
                    st.success(f"✅ {fname}")
                    st.rerun()

    with c2:
        st.markdown("#### 📋 دليل جهات الاتصال")
        if contacts_df.empty:
            st.info("لا توجد جهات اتصال")
        else:
            active_c = contacts_df[contacts_df["active"].astype(str)=="True"]
            search_c = st.text_input("🔍 بحث")
            if search_c:
                active_c = active_c[
                    active_c["full_name"].str.contains(search_c, case=False, na=False) |
                    active_c["supplier_name"].str.contains(search_c, case=False, na=False)
                ]
            show = ["supplier_name","full_name","position","phone","email"]
            avail = [c for c in show if c in active_c.columns]
            rename = {"supplier_name":"المورد","full_name":"الاسم",
                      "position":"المنصب","phone":"الهاتف","email":"البريد"}
            st.dataframe(active_c[avail].rename(columns=rename),
                         use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════
#  إحصاءات الموردين
# ══════════════════════════════════════════════
def _stats():
    st.markdown("### 📊 إحصاءات الموردين")
    df = read_df("suppliers")
    if df.empty:
        st.info("لا توجد بيانات")
        return
    active = df[df["active"].astype(str)=="True"]
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("**التوزيع حسب النوع**")
        if "type" in active.columns:
            st.bar_chart(active["type"].value_counts())
    with c2:
        st.markdown("**التوزيع حسب التقييم**")
        if "rating" in active.columns:
            st.bar_chart(active["rating"].value_counts())

    st.markdown("**التوزيع حسب الولاية**")
    if "wilaya" in active.columns:
        st.bar_chart(active["wilaya"].value_counts().head(10))
