# pages/offices.py — إدارة المكاتب والمحلات والمسؤولين

import streamlit as st
import pandas as pd
from datetime import datetime
from utils.sheets import read_df, append_row, update_row, gen_id
from config import OFFICE_TYPES, DEFAULT_DEPARTMENTS


def show_offices():
    st.markdown("## 🏢 المكاتب والمحلات والمسؤولون")
    tabs = st.tabs([
        "🏢 المكاتب والمحلات",
        "➕ إضافة مكتب",
        "👔 المسؤولون",
        "➕ تعيين مسؤول",
        "🗺️ خريطة الكلية",
    ])
    with tabs[0]: _list_offices()
    with tabs[1]: _add_office()
    with tabs[2]: _list_managers()
    with tabs[3]: _assign_manager()
    with tabs[4]: _map_view()


# ══════════════════════════════════════════════
#  قائمة المكاتب
# ══════════════════════════════════════════════
def _list_offices():
    st.markdown("### 🏢 قائمة المكاتب والمحلات")
    df = read_df("offices")
    managers_df = read_df("office_managers")

    fc1,fc2,fc3 = st.columns(3)
    with fc1: search  = st.text_input("🔍 بحث")
    with fc2: type_f  = st.selectbox("النوع", ["الكل"]+OFFICE_TYPES)
    with fc3: floor_f = st.selectbox("الطابق", ["الكل","الطابق الأرضي","الطابق الأول","الطابق الثاني","الطابق الثالث"])

    if df.empty:
        st.info("لا توجد مكاتب مسجلة بعد")
        return

    d = df[df["active"].astype(str)=="True"].copy()
    if search:
        d = d[
            d["name"].str.contains(search, case=False, na=False) |
            d.get("code",pd.Series()).str.contains(search, case=False, na=False)
        ]
    if type_f  != "الكل": d = d[d["type"]==type_f]
    if floor_f != "الكل": d = d[d.get("floor","").str.contains(floor_f.replace("الطابق ",""), case=False, na=False)]

    # إضافة المسؤول الحالي
    if not managers_df.empty:
        current = managers_df[managers_df["is_current"].astype(str)=="True"]
        mgr_map = dict(zip(current["office_id"], current["manager_name"]))
        d["المسؤول الحالي"] = d["id"].map(lambda x: mgr_map.get(str(x),"—"))
    else:
        d["المسؤول الحالي"] = "—"

    # بطاقات إحصائية
    s1,s2,s3,s4 = st.columns(4)
    type_counts = d["type"].value_counts().to_dict() if not d.empty else {}
    s1.metric("إجمالي", len(d))
    s2.metric("مكاتب إدارية", type_counts.get("مكتب إداري",0))
    s3.metric("مصالح", type_counts.get("مصلحة",0))
    s4.metric("قاعات", type_counts.get("قاعة دراسية",0)+type_counts.get("قاعة محاضرات",0))

    st.divider()

    show = {
        "code":"الرمز","name":"الاسم","name_fr":"بالفرنسية",
        "type":"النوع","floor":"الطابق","building":"المبنى",
        "phone":"الهاتف","المسؤول الحالي":"المسؤول",
    }
    avail = {k:v for k,v in show.items() if k in d.columns or k=="المسؤول الحالي"}
    st.dataframe(d[[c for c in avail if c in d.columns]].rename(columns=avail),
                 use_container_width=True, hide_index=True)
    st.caption(f"عدد المكاتب: **{len(d)}**")

    # تفاصيل مكتب
    st.divider()
    st.markdown("#### 🔍 بطاقة المكتب")
    if not d.empty:
        opts = dict(zip(d.get("code","")+"  —  "+d["name"], d["id"]))
        sel_lbl = st.selectbox("اختر المكتب", list(opts.keys()), key="office_detail_sel")
        sel_id  = opts.get(sel_lbl,"")
        if sel_id:
            row = d[d["id"]==sel_id].iloc[0].to_dict()
            oc1,oc2 = st.columns(2)
            with oc1:
                st.markdown(f"""
                <div style="background:#f8f9fa;border-radius:12px;padding:16px;border-right:4px solid #1a1a2e;">
                    <h4 style="margin:0">🏢 {row.get('name','')}</h4>
                    <p style="color:#666;font-size:.85rem">{row.get('name_fr','')}</p>
                    <hr style="border-color:#eee">
                    <p><strong>الرمز:</strong> {row.get('code','')}</p>
                    <p><strong>النوع:</strong> {row.get('type','')}</p>
                    <p><strong>الطابق:</strong> {row.get('floor','')}</p>
                    <p><strong>المبنى:</strong> {row.get('building','')}</p>
                    <p><strong>المساحة:</strong> {row.get('surface','')} م²</p>
                    <p><strong>الطاقة الاستيعابية:</strong> {row.get('capacity','')} شخص</p>
                </div>""", unsafe_allow_html=True)
            with oc2:
                # المسؤول الحالي
                if not managers_df.empty:
                    curr_mgr = managers_df[
                        (managers_df["office_id"].astype(str)==str(sel_id)) &
                        (managers_df["is_current"].astype(str)=="True")
                    ]
                    if not curr_mgr.empty:
                        m = curr_mgr.iloc[0].to_dict()
                        st.markdown(f"""
                        <div style="background:linear-gradient(135deg,#1a1a2e,#0f3460);
                             color:white;border-radius:12px;padding:16px;margin-bottom:12px;">
                            <div style="font-size:.75rem;opacity:.7;margin-bottom:4px;">👔 المسؤول الحالي</div>
                            <div style="font-size:1.1rem;font-weight:800">{m.get('manager_name','')}</div>
                            <div style="font-size:.8rem;opacity:.8">{m.get('manager_title','')}</div>
                            <hr style="border-color:rgba(255,255,255,.2);margin:8px 0">
                            <div style="font-size:.82rem">📞 {m.get('manager_phone','')}</div>
                            <div style="font-size:.82rem">📧 {m.get('manager_email','')}</div>
                            <div style="font-size:.75rem;opacity:.6;margin-top:6px">منذ: {m.get('start_date','')}</div>
                        </div>""", unsafe_allow_html=True)

                        # تاريخ المسؤولين
                        all_mgrs = managers_df[managers_df["office_id"].astype(str)==str(sel_id)]
                        if len(all_mgrs) > 1:
                            st.markdown("**تاريخ المسؤولين:**")
                            st.dataframe(all_mgrs[["manager_name","manager_title","start_date","end_date"]].rename(columns={
                                "manager_name":"الاسم","manager_title":"الصفة",
                                "start_date":"من","end_date":"إلى"
                            }), use_container_width=True, hide_index=True)
                    else:
                        st.warning("⚠️ لا يوجد مسؤول حالي معيَّن لهذا المكتب")


# ══════════════════════════════════════════════
#  إضافة مكتب
# ══════════════════════════════════════════════
def _add_office():
    st.markdown("### ➕ إضافة مكتب / محل / قاعة")
    with st.form("add_office", clear_on_submit=True):
        oc1,oc2,oc3 = st.columns(3)
        with oc1:
            code    = st.text_input("الرمز ★", placeholder="OFF-010")
            name    = st.text_input("الاسم (عربي) ★")
            name_fr = st.text_input("Nom (Français)")
            otype   = st.selectbox("النوع ★", OFFICE_TYPES)
        with oc2:
            floor    = st.selectbox("الطابق ★", ["الطابق الأرضي","الطابق الأول","الطابق الثاني","الطابق الثالث","أخرى"])
            building = st.text_input("المبنى / الجناح", placeholder="مثال: A, B, الجناح الشمالي")
            surface  = st.number_input("المساحة (م²)", min_value=0.0, value=20.0)
            capacity = st.number_input("الطاقة الاستيعابية", min_value=0, value=10)
        with oc3:
            phone    = st.text_input("رقم الهاتف")
            email    = st.text_input("البريد الإلكتروني")
            dept     = st.selectbox("المصلحة المرتبطة", DEFAULT_DEPARTMENTS)
            notes    = st.text_area("ملاحظات", height=80)

        submitted = st.form_submit_button("✅ إضافة", type="primary", use_container_width=True)

    if submitted:
        errs = []
        if not code.strip(): errs.append("الرمز مطلوب")
        if not name.strip(): errs.append("الاسم مطلوب")
        existing = read_df("offices")
        if not existing.empty and code.strip() in list(existing.get("code",[])):
            errs.append(f"الرمز «{code}» مستخدم مسبقاً")
        if errs:
            for e in errs: st.error(f"❌ {e}")
            return
        try:
            append_row("offices", {
                "id":gen_id(),"code":code.strip().upper(),"name":name.strip(),
                "name_fr":name_fr.strip(),"type":otype,"floor":floor,
                "building":building.strip(),"surface":surface,"capacity":capacity,
                "phone":phone.strip(),"email":email.strip(),"department":dept,
                "notes":notes.strip(),"active":"True",
                "created_at":datetime.now().strftime("%Y-%m-%d %H:%M"),
            })
            st.success(f"✅ تمت إضافة: **{name}** (الرمز: {code.upper()})")
        except Exception as e:
            st.error(f"❌ {e}")


# ══════════════════════════════════════════════
#  قائمة المسؤولين
# ══════════════════════════════════════════════
def _list_managers():
    st.markdown("### 👔 مسؤولو المكاتب والمصالح")
    managers_df = read_df("office_managers")
    offices_df  = read_df("offices")

    if managers_df.empty:
        st.info("لا يوجد مسؤولون مسجلون بعد")
        return

    # فقط الحاليون
    show_all = st.checkbox("عرض الجميع (بما فيهم السابقون)")
    d = managers_df.copy() if show_all else managers_df[managers_df["is_current"].astype(str)=="True"].copy()

    search_m = st.text_input("🔍 بحث باسم المسؤول أو المكتب")
    if search_m:
        d = d[
            d["manager_name"].str.contains(search_m, case=False, na=False) |
            d["office_name"].str.contains(search_m, case=False, na=False)
        ]

    # بطاقات للمسؤولين الحاليين
    current = d[d["is_current"].astype(str)=="True"] if not d.empty else pd.DataFrame()
    if not current.empty:
        st.markdown("#### المسؤولون الحاليون")
        cols = st.columns(min(3, len(current)))
        for i,(_, m) in enumerate(current.iterrows()):
            if i < len(cols):
                with cols[i % len(cols)]:
                    st.markdown(f"""
                    <div style="background:white;border:1px solid #e9ecef;border-radius:12px;
                         padding:16px;margin-bottom:8px;border-top:3px solid #1a1a2e;">
                        <div style="font-weight:800;font-size:.95rem;color:#1a1a2e">
                            👔 {m.get('manager_name','')}
                        </div>
                        <div style="font-size:.8rem;color:#666">{m.get('manager_title','')}</div>
                        <hr style="border-color:#f0f0f0;margin:8px 0">
                        <div style="font-size:.82rem">🏢 {m.get('office_name','')}</div>
                        <div style="font-size:.8rem;color:#888">رمز: {m.get('office_code','')}</div>
                        <div style="font-size:.8rem;margin-top:6px">📞 {m.get('manager_phone','—')}</div>
                        <div style="font-size:.78rem;color:#aaa;margin-top:4px">منذ: {m.get('start_date','')}</div>
                    </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### قائمة كاملة")
    show = ["office_code","office_name","manager_name","manager_title",
            "manager_phone","manager_email","start_date","is_current"]
    avail = [c for c in show if c in d.columns]
    rename = {"office_code":"رمز المكتب","office_name":"المكتب",
              "manager_name":"المسؤول","manager_title":"الصفة",
              "manager_phone":"الهاتف","manager_email":"البريد",
              "start_date":"من","is_current":"حالي؟"}
    st.dataframe(d[avail].rename(columns=rename), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════
#  تعيين مسؤول
# ══════════════════════════════════════════════
def _assign_manager():
    st.markdown("### ➕ تعيين مسؤول لمكتب")
    offices_df = read_df("offices")
    if offices_df.empty:
        st.warning("أضف مكاتب أولاً")
        return

    active_offices = offices_df[offices_df["active"].astype(str)=="True"]
    office_opts = dict(zip(
        active_offices.get("code","")+"  —  "+active_offices["name"],
        active_offices["id"]
    ))
    office_name_map = dict(zip(active_offices["id"], active_offices["name"]))
    office_code_map = dict(zip(active_offices["id"], active_offices.get("code",active_offices["id"])))

    with st.form("assign_manager", clear_on_submit=True):
        mc1,mc2 = st.columns(2)
        with mc1:
            sel_office = st.selectbox("المكتب ★", ["-- اختر --"]+list(office_opts.keys()))
            mgr_name   = st.text_input("اسم المسؤول ★")
            mgr_title  = st.text_input("الصفة / المنصب ★", placeholder="رئيس مصلحة، أمين المكتبة...")
        with mc2:
            mgr_phone  = st.text_input("رقم الهاتف")
            mgr_email  = st.text_input("البريد الإلكتروني")
            start_date = st.date_input("تاريخ التعيين ★", value=datetime.now().date())
            notes      = st.text_input("ملاحظات")

        st.info("💡 سيُنهى تلقائياً تعيين المسؤول الحالي عند إضافة مسؤول جديد")
        submitted = st.form_submit_button("✅ تعيين المسؤول", type="primary", use_container_width=True)

    if submitted:
        if sel_office == "-- اختر --" or not mgr_name.strip() or not mgr_title.strip():
            st.error("❌ المكتب والاسم والصفة مطلوبة")
            return
        try:
            office_id = office_opts.get(sel_office,"")

            # إنهاء تعيين المسؤول الحالي
            managers_df = read_df("office_managers")
            if not managers_df.empty:
                current = managers_df[
                    (managers_df["office_id"].astype(str)==str(office_id)) &
                    (managers_df["is_current"].astype(str)=="True")
                ]
                for _, old in current.iterrows():
                    update_row("office_managers", old["id"], {
                        "is_current": "False",
                        "end_date": str(start_date),
                    })

            # إضافة المسؤول الجديد
            append_row("office_managers", {
                "id":           gen_id(),
                "office_id":    office_id,
                "office_name":  office_name_map.get(office_id,""),
                "office_code":  office_code_map.get(office_id,""),
                "manager_name": mgr_name.strip(),
                "manager_title":mgr_title.strip(),
                "manager_phone":mgr_phone.strip(),
                "manager_email":mgr_email.strip(),
                "start_date":   str(start_date),
                "end_date":     "",
                "is_current":   "True",
                "notes":        notes.strip(),
            })
            st.success(f"✅ تم تعيين **{mgr_name}** مسؤولاً عن **{office_name_map.get(office_id,'')}**")
        except Exception as e:
            st.error(f"❌ {e}")


# ══════════════════════════════════════════════
#  خريطة الكلية (تخطيطية)
# ══════════════════════════════════════════════
def _map_view():
    st.markdown("### 🗺️ المخطط التنظيمي للكلية")
    offices_df  = read_df("offices")
    managers_df = read_df("office_managers")

    if offices_df.empty:
        st.info("أضف مكاتب لعرض المخطط")
        return

    active = offices_df[offices_df["active"].astype(str)=="True"]
    mgr_map = {}
    if not managers_df.empty:
        curr = managers_df[managers_df["is_current"].astype(str)=="True"]
        mgr_map = dict(zip(curr["office_id"].astype(str), curr["manager_name"]))

    # تجميع حسب الطابق
    floors = active["floor"].unique() if "floor" in active.columns else ["الطابق الأرضي"]
    type_colors = {
        "مكتب إداري": "#3b82f6",
        "مصلحة": "#10b981",
        "قاعة دراسية": "#f59e0b",
        "قاعة محاضرات": "#8b5cf6",
        "مخزن": "#6b7280",
        "مكتبة": "#ec4899",
        "مختبر / ورشة": "#f97316",
        "مرافق مشتركة": "#14b8a6",
    }

    for floor in sorted(floors):
        floor_offices = active[active["floor"]==floor] if "floor" in active.columns else active
        if floor_offices.empty:
            continue
        st.markdown(f"#### 🏗️ {floor}")
        cols = st.columns(min(4, len(floor_offices)))
        for i,(_, office) in enumerate(floor_offices.iterrows()):
            with cols[i % min(4, len(floor_offices))]:
                color = type_colors.get(office.get("type",""), "#6b7280")
                mgr   = mgr_map.get(str(office["id"]), "غير معيَّن")
                mgr_style = "color:#e94560;font-weight:700" if mgr=="غير معيَّن" else ""
                st.markdown(f"""
                <div style="background:white;border:1px solid #e9ecef;border-radius:10px;
                     padding:12px;margin-bottom:8px;border-top:3px solid {color};">
                    <div style="font-weight:800;font-size:.88rem">{office.get('name','')}</div>
                    <div style="font-size:.7rem;color:#666">{office.get('code','')}</div>
                    <div style="background:{color}22;color:{color};border-radius:20px;
                         padding:2px 8px;font-size:.7rem;display:inline-block;margin:4px 0">
                        {office.get('type','')}
                    </div>
                    <div style="font-size:.75rem;{mgr_style};margin-top:4px">👔 {mgr}</div>
                </div>""", unsafe_allow_html=True)
