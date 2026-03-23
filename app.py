# app.py — نظام الوسائل العامة v3.0 — النسخة الضخمة

import streamlit as st
from config import APP_NAME, APP_VERSION, FACULTY_NAME, UNIVERSITY_NAME, ROLES, has_perm

st.set_page_config(
    page_title=f"{APP_NAME} | {FACULTY_NAME}",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700;900&display=swap');
*,[class*="css"]{font-family:'Tajawal',Tahoma,sans-serif!important;}
.stApp{direction:rtl;}

/* شريط جانبي */
[data-testid="stSidebar"]{
    background:linear-gradient(180deg,#0d0d1a 0%,#111827 60%,#1a1a2e 100%)!important;
    border-right:3px solid #e94560;
    border-left:none!important;
}
[data-testid="stSidebar"] *{color:#c8c8d0!important;}

/* أزرار التنقل */
[data-testid="stSidebar"] .stButton>button{
    border-radius:8px!important;text-align:right!important;
    font-size:.85rem!important;padding:8px 14px!important;
    transition:all .15s!important;width:100%!important;
    border:1px solid rgba(255,255,255,.07)!important;
    background:rgba(255,255,255,.03)!important;color:#bbb!important;
    margin-bottom:2px!important;
}
[data-testid="stSidebar"] .stButton>button:hover{
    background:rgba(233,69,96,.18)!important;
    border-color:rgba(233,69,96,.4)!important;color:white!important;
}
[data-testid="stSidebar"] .stButton>button[kind="primary"]{
    background:rgba(233,69,96,.22)!important;
    border-right:3px solid #e94560!important;color:white!important;
    font-weight:700!important;
}

/* رأس الصفحة */
.ph{background:linear-gradient(135deg,#0f0c29,#1a1a2e,#16213e);
    border-radius:14px;padding:18px 26px;color:white;margin-bottom:20px;
    border-right:5px solid #e94560;display:flex;align-items:center;gap:18px;}
.ph h1{margin:0;font-size:1.35rem;font-weight:900;}
.ph p{margin:3px 0 0;opacity:.68;font-size:.78rem;}

/* Metrics */
[data-testid="metric-container"]{
    background:white;border:1px solid #eaeaea;border-radius:12px;padding:14px;
    box-shadow:0 2px 8px rgba(0,0,0,.05);
}
/* Buttons */
.stButton>button[kind="primary"]{
    background:linear-gradient(135deg,#1a1a2e,#e94560)!important;
    color:white!important;border:none!important;border-radius:9px!important;
    font-weight:700!important;transition:all .2s!important;
}
.stButton>button[kind="primary"]:hover{transform:translateY(-2px)!important;
    box-shadow:0 6px 18px rgba(233,69,96,.35)!important;}

/* Tables */
[data-testid="stDataFrame"]{border-radius:12px!important;overflow:hidden!important;}
/* Tabs */
.stTabs [data-baseweb="tab"]{font-weight:600;font-size:.86rem;}
/* Forms */
[data-testid="stForm"]{background:#f8f9fa;border-radius:14px;padding:20px;border:1px solid #e9ecef;}
/* Expanders */
[data-testid="stExpander"]{border:1px solid #e9ecef!important;border-radius:10px!important;margin-bottom:6px!important;}
/* Alerts */
.stAlert{border-radius:10px!important;}

/* شعار الشريط */
.sl{text-align:center;padding:18px 12px 12px;border-bottom:1px solid rgba(255,255,255,.08);margin-bottom:8px;}
.sl-icon{font-size:2.5rem;}
.sl-title{font-size:.95rem;font-weight:900;color:white!important;margin:6px 0 2px;}
.sl-sub{font-size:.68rem;opacity:.5;}
.sl-ver{font-size:.65rem;opacity:.35;margin-top:2px;}
.role-tag{display:inline-block;background:rgba(233,69,96,.2);
    color:#f08090!important;border:1px solid rgba(233,69,96,.35);
    padding:3px 10px;border-radius:20px;font-size:.72rem;font-weight:600;margin-top:6px;}
.user-name{font-size:.8rem;opacity:.6;margin-top:4px;}

/* قسم التنقل */
.nav-section{font-size:.68rem;color:rgba(255,255,255,.35)!important;
    padding:8px 14px 3px;text-transform:uppercase;letter-spacing:1px;margin-top:4px;}
</style>
""", unsafe_allow_html=True)

# ── حالة الجلسة ────────────────────────────────────────────────────
if "user" not in st.session_state:  st.session_state.user = None
if "page" not in st.session_state:  st.session_state.page = "dashboard"

# ── تسجيل الدخول ───────────────────────────────────────────────────
def _login():
    _,center,_ = st.columns([1.3,2,1.3])
    with center:
        st.markdown("""
        <div style="background:white;border-radius:20px;
             box-shadow:0 24px 64px rgba(0,0,0,.14);overflow:hidden;margin-top:40px;">
            <div style="background:linear-gradient(135deg,#0f0c29,#1a1a2e,#16213e);
                 padding:36px 28px;text-align:center;color:white;">
                <div style="font-size:3.5rem">🏛️</div>
                <h2 style="margin:10px 0 4px;font-size:1.4rem;font-weight:900">نظام الوسائل العامة</h2>
                <div style="font-size:.68rem;opacity:.4;margin-bottom:6px">v"""+APP_VERSION+"""</div>
                <p style="margin:0;opacity:.7;font-size:.82rem;line-height:1.7">
                    كلية الحقوق والعلوم السياسية<br>
                    جامعة محمد البشير الإبراهيمي — برج بوعريريج
                </p>
            </div>
            <div style="padding:30px;">
        """, unsafe_allow_html=True)

        with st.form("login"):
            username = st.text_input("👤 اسم المستخدم")
            password = st.text_input("🔒 كلمة المرور", type="password")
            btn = st.form_submit_button("دخول →", type="primary", use_container_width=True)

        st.markdown("</div></div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center;margin-top:12px;color:#bbb;font-size:.76rem;'>"
                    "الحساب الافتراضي: <code>admin</code> / <code>admin123</code></div>", unsafe_allow_html=True)

        if btn:
            if not username or not password:
                st.warning("⚠️ أدخل بيانات الدخول")
                return
            with st.spinner("جاري التحقق..."):
                try:
                    from utils.sheets import authenticate, initialize_sheets
                    initialize_sheets()
                    user = authenticate(username.strip(), password)
                    if user:
                        st.session_state.user = user
                        st.session_state.page = "dashboard"
                        st.rerun()
                    else:
                        st.error("❌ بيانات الدخول غير صحيحة")
                except Exception as e:
                    st.error(f"❌ خطأ في الاتصال: {e}")

# ── الشريط الجانبي ─────────────────────────────────────────────────
NAV = [
    # (key, icon, label, perm, section)
    ("dashboard",  "🏠", "لوحة التحكم",         "*",                  "رئيسي"),
    ("catalog",    "📦", "كتالوج المنتجات",      "catalog",            "المخزون"),
    ("receiving",  "📥", "الاستلام والشراء",     "stock_in",           "المخزون"),
    ("transfers",  "📋", "سندات التحويل",        "transfers",          "التحويل"),
    ("inventory",  "🗂️", "الجرد الدوري",         "inventory",          "المخزون"),
    ("suppliers",  "🏭", "الموردون",             "suppliers",          "الإدارة"),
    ("offices",    "🏢", "المكاتب والمسؤولون",   "catalog",            "الإدارة"),
    ("reports",    "📊", "التقارير",             "reports",            "التحليل"),
    ("users",      "👥", "المستخدمون",           "users",              "النظام"),
]

PERM_FALLBACK = {  # صلاحيات بديلة للتحقق
    "catalog":    ["catalog","catalog_view","products"],
    "stock_in":   ["stock_in"],
    "transfers":  ["transfers","request_transfer","execute_transfers"],
    "inventory":  ["inventory"],
    "suppliers":  ["suppliers"],
    "reports":    ["reports"],
    "users":      ["users","مسؤول_وسائل"],
    "*":          ["*"],
}

def _can_access(user, perm):
    if perm == "*": return True
    role_perms = ROLES.get(user["role"],{}).get("permissions",[])
    if "*" in role_perms: return True
    alts = PERM_FALLBACK.get(perm,[perm])
    return any(p in role_perms for p in alts)

def _sidebar():
    user = st.session_state.user
    role = user["role"]
    with st.sidebar:
        st.markdown(f"""
        <div class="sl">
            <div class="sl-icon">🏛️</div>
            <div class="sl-title">{APP_NAME}</div>
            <div class="sl-sub">{FACULTY_NAME}</div>
            <div class="sl-ver">v{APP_VERSION}</div>
            <div class="role-tag">{ROLES[role]['icon']} {ROLES[role]['label']}</div>
            <div class="user-name">{user['full_name']}</div>
        </div>
        """, unsafe_allow_html=True)

        current_section = ""
        for key,icon,label,perm,section in NAV:
            if not _can_access(user, perm): continue
            if section != current_section:
                st.markdown(f'<div class="nav-section">{section}</div>', unsafe_allow_html=True)
                current_section = section
            is_active = st.session_state.page == key
            if st.button(f"{icon}  {label}", key=f"nav_{key}", use_container_width=True,
                         type="primary" if is_active else "secondary"):
                st.session_state.page = key
                st.rerun()

        st.markdown("<hr style='border-color:rgba(255,255,255,.08);margin:14px 0;'>", unsafe_allow_html=True)
        if st.button("🚪  تسجيل الخروج", use_container_width=True):
            st.session_state.user = None
            st.session_state.page = "dashboard"
            st.rerun()

# ── رأس الصفحة ─────────────────────────────────────────────────────
PAGE_META = {
    "dashboard": ("لوحة التحكم",        "🏠"),
    "catalog":   ("كتالوج المنتجات",    "📦"),
    "receiving": ("الاستلام والشراء",   "📥"),
    "transfers": ("سندات التحويل",      "📋"),
    "inventory": ("الجرد الدوري",       "🗂️"),
    "suppliers": ("الموردون",           "🏭"),
    "offices":   ("المكاتب والمسؤولون","🏢"),
    "reports":   ("التقارير",          "📊"),
    "users":     ("إدارة المستخدمين",  "👥"),
}

def _header(title, icon):
    user = st.session_state.user
    role = user["role"]
    st.markdown(f"""
    <div class="ph">
        <div style="font-size:2.2rem">{icon}</div>
        <div>
            <h1>{title}</h1>
            <p>{ROLES[role]['label']} — {user.get('department','')} | {FACULTY_NAME}</p>
        </div>
    </div>""", unsafe_allow_html=True)

# ── توجيه ──────────────────────────────────────────────────────────
def _route():
    page = st.session_state.page
    user = st.session_state.user
    title, icon = PAGE_META.get(page, ("لوحة التحكم","🏠"))
    _header(title, icon)

    if page == "dashboard":
        from pages.dashboard  import show_dashboard;  show_dashboard()
    elif page == "catalog":
        from pages.catalog    import show_catalog;    show_catalog()
    elif page == "receiving":
        from pages.receiving  import show_receiving;  show_receiving()
    elif page == "transfers":
        from pages.transfers  import show_transfers;  show_transfers()
    elif page == "inventory":
        from pages.inventory  import show_inventory;  show_inventory()
    elif page == "suppliers":
        from pages.suppliers  import show_suppliers;  show_suppliers()
    elif page == "offices":
        from pages.offices    import show_offices;    show_offices()
    elif page == "reports":
        from pages.reports    import show_reports;    show_reports()
    elif page == "users":
        from pages.users      import show_users;      show_users()
    else:
        from pages.dashboard  import show_dashboard;  show_dashboard()

# ── نقطة الدخول ────────────────────────────────────────────────────
def main():
    if st.session_state.user is None:
        _login()
    else:
        _sidebar()
        _route()

main()
