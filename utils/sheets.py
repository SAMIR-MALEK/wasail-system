# utils/sheets.py

import gspread, streamlit as st, pandas as pd
from google.oauth2.service_account import Credentials
from config import SHEETS, COLUMNS
import hashlib, uuid
from datetime import datetime

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# ── اتصال ────────────────────────────────────────────────────────────
@st.cache_resource(ttl=300)
def _client():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES
    )
    return gspread.authorize(creds)

def _ss():
    return _client().open_by_key(st.secrets["spreadsheet_id"])

def _ws(key: str):
    return _ss().worksheet(SHEETS[key])

# ── CRUD أساسي ───────────────────────────────────────────────────────
def read_df(key: str) -> pd.DataFrame:
    try:
        data = _ws(key).get_all_records()
        if not data:
            return pd.DataFrame(columns=COLUMNS.get(key, []))
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"خطأ قراءة «{SHEETS.get(key,key)}»: {e}")
        return pd.DataFrame(columns=COLUMNS.get(key, []))

def append_row(key: str, data: dict):
    ws  = _ws(key)
    row = [str(data.get(c, "")) for c in COLUMNS[key]]
    ws.append_row(row, value_input_option="USER_ENTERED")

def update_row(key: str, row_id: str, updates: dict):
    ws   = _ws(key)
    cols = COLUMNS[key]
    rows = ws.get_all_records()
    for i, row in enumerate(rows):
        if str(row.get("id")) == str(row_id):
            rn = i + 2
            for col, val in updates.items():
                if col in cols:
                    ws.update_cell(rn, cols.index(col)+1, str(val))
            return True
    return False

def delete_row(key: str, row_id: str):
    """تعطيل سجل (soft delete)"""
    update_row(key, row_id, {"active": "False"})

def get_row(key: str, row_id: str) -> dict:
    df = read_df(key)
    if df.empty:
        return {}
    r = df[df["id"].astype(str) == str(row_id)]
    return r.iloc[0].to_dict() if not r.empty else {}

# ── المخزون ──────────────────────────────────────────────────────────
def get_stock_df() -> pd.DataFrame:
    return read_df("stock")

def get_product_stock(product_id: str) -> float:
    df = get_stock_df()
    if df.empty: return 0.0
    r = df[df["product_id"].astype(str) == str(product_id)]
    return float(r.iloc[0]["quantity"]) if not r.empty else 0.0

def update_stock(product_id: str, product_code: str, product_name: str,
                 unit_name: str, delta: float,
                 direction: str = "in") -> float:
    ws   = _ws("stock")
    rows = ws.get_all_records()
    now  = _now()
    for i, row in enumerate(rows):
        if str(row.get("product_id")) == str(product_id):
            new_qty = max(0.0, float(row.get("quantity", 0)) + delta)
            avail   = max(0.0, new_qty - float(row.get("reserved_qty", 0)))
            rn = i + 2
            ws.update_cell(rn, COLUMNS["stock"].index("quantity")+1, new_qty)
            ws.update_cell(rn, COLUMNS["stock"].index("available_qty")+1, avail)
            ws.update_cell(rn, COLUMNS["stock"].index("last_updated")+1, now)
            if direction == "in":
                ws.update_cell(rn, COLUMNS["stock"].index("last_in_date")+1, now)
            else:
                ws.update_cell(rn, COLUMNS["stock"].index("last_out_date")+1, now)
            return new_qty
    # منتج جديد في المخزون
    qty = max(0.0, delta)
    ws.append_row([
        product_id, product_code, product_name, unit_name,
        qty, 0, qty,
        now if direction=="in" else "",
        "" if direction=="in" else now,
        now,
    ])
    return qty

# ── ترقيم تسلسلي ─────────────────────────────────────────────────────
def _seq_num(key: str, col: str, prefix: str) -> str:
    df   = read_df(key)
    year = datetime.now().year
    pfx  = f"{prefix}-{year}-"
    if df.empty:
        return f"{pfx}001"
    yr = df[df[col].str.contains(str(year), na=False)] if col in df.columns else pd.DataFrame()
    if yr.empty:
        return f"{pfx}001"
    try:
        mx = yr[col].str.extract(r"(\d+)$").astype(int).max().iloc[0]
        return f"{pfx}{str(mx+1).zfill(3)}"
    except Exception:
        return f"{pfx}001"

def next_transfer_number()      : return _seq_num("transfers",       "number", "ST")
def next_purchase_order_number(): return _seq_num("purchase_orders",  "number", "BC")
def next_invoice_number()       : return _seq_num("invoices",         "number", "FAC")
def next_inventory_number()     : return _seq_num("inventory",        "number", "INV")

# ── ID مولَّد ─────────────────────────────────────────────────────────
def gen_id() -> str:
    return str(uuid.uuid4())[:8].upper()

def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")

# ── تسجيل النشاط ──────────────────────────────────────────────────────
def log_activity(user: dict, action: str, module: str,
                 ref_id: str = "", ref_num: str = "", details: str = ""):
    try:
        append_row("activity_log", {
            "id":              gen_id(),
            "datetime":        _now(),
            "user_id":         user.get("id",""),
            "user_name":       user.get("full_name",""),
            "action":          action,
            "module":          module,
            "reference_id":    ref_id,
            "reference_number":ref_num,
            "details":         details,
            "ip_address":      "",
        })
    except Exception:
        pass  # لا نوقف العملية بسبب فشل التسجيل

# ── المصادقة ──────────────────────────────────────────────────────────
def hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate(username: str, password: str):
    import streamlit as st
    df = read_df("users")
    if df.empty:
        st.error("DEBUG: الجدول فارغ")
        return None
    h = hash_pw(password)
    # debug
    st.warning(f"DEBUG — صفوف: {len(df)}")
    st.warning(f"DEBUG — أعمدة: {list(df.columns)}")
    if not df.empty:
        row = df.iloc[0]
        st.warning(f"DEBUG — username في Sheet: [{row.get('username','')}]")
        st.warning(f"DEBUG — hash في Sheet: [{str(row.get('password_hash',''))[:20]}...]")
        st.warning(f"DEBUG — hash المحسوب:   [{h[:20]}...]")
        st.warning(f"DEBUG — active: [{row.get('active','')}]")
    r = df[
        (df["username"] == username) &
        (df["password_hash"] == h) &
        (df["active"].astype(str).str.strip().str.upper() == "TRUE")
    ]
    if r.empty: return None
    user = r.iloc[0].to_dict()
    update_row("users", user["id"], {"last_login": _now()})
    return user

# ── تهيئة الأوراق ─────────────────────────────────────────────────────
def initialize_sheets():
    ss       = _ss()
    existing = [ws.title for ws in ss.worksheets()]
    for key, title in SHEETS.items():
        if title not in existing:
            ncols = len(COLUMNS.get(key, ["A"]))
            ws = ss.add_worksheet(title=title, rows=2000, cols=max(ncols, 10))
            ws.append_row(COLUMNS.get(key, []))
            ws.format("1:1", {
                "backgroundColor": {"red":0.1,"green":0.1,"blue":0.18},
                "textFormat": {"bold":True, "foregroundColor":{"red":1,"green":1,"blue":1}},
            })

    # بيانات افتراضية
    _seed_defaults()

def _seed_defaults():
    from config import DEFAULT_CATEGORIES, DEFAULT_UNITS

    # فئات
    cats = read_df("categories")
    if cats.empty:
        icons = ["🖊️","🧹","💻","🖨️","🪑","🖨️","☕","💡","🔧","📦"]
        for i, cat in enumerate(DEFAULT_CATEGORIES):
            append_row("categories", {
                "id": gen_id(), "name": cat, "name_fr": "",
                "description": "", "icon": icons[i] if i < len(icons) else "📦",
                "active": "True", "created_at": _now(),
            })

    # وحدات
    units = read_df("units")
    if units.empty:
        from config import DEFAULT_UNITS
        symbols = {"قطعة":"قط","علبة":"عب","رزمة":"رز","لتر":"ل","كيلوغرام":"كغ",
                   "رول":"رول","كارتون":"كرت","مجموعة":"مج","زوج":"زج","متر":"م",
                   "كيلس":"كيلس","طاقم":"طاقم","حبة":"حبة","رطل":"رطل"}
        for u in DEFAULT_UNITS:
            append_row("units", {
                "id": gen_id(), "name": u, "name_fr": "",
                "symbol": symbols.get(u, u[:3]),
                "active": "True", "created_at": _now(),
            })

    # مستخدم مدير افتراضي
    users = read_df("users")
    if users.empty:
        append_row("users", {
            "id":            gen_id(),
            "username":      "admin",
            "password_hash": hash_pw("admin123"),
            "full_name":     "مدير النظام",
            "title":         "المدير",
            "role":          "مدير",
            "department":    "مصلحة الوسائل العامة",
            "office_id":     "",
            "phone":         "",
            "email":         "",
            "active":        "True",
            "last_login":    "",
            "created_at":    _now(),
            "created_by":    "system",
        })

    # مكاتب افتراضية
    offices = read_df("offices")
    if offices.empty:
        default_offices = [
            ("OFF-001","الأمانة العامة","Secrétariat Général","مكتب إداري","الطابق الأول","A"),
            ("OFF-002","مكتب الأستاذة","Bureau du Professorat","مكتب إداري","الطابق الأول","A"),
            ("OFF-003","مصلحة التدريس","Service Enseignement","مصلحة","الطابق الثاني","B"),
            ("OFF-004","مصلحة البيداغوجيا","Service Pédagogie","مصلحة","الطابق الثاني","B"),
            ("OFF-005","مكتبة الكلية","Bibliothèque","مكتبة","الطابق الأرضي","A"),
            ("OFF-006","مصلحة الماستر والدكتوراه","Service Master & Doctorat","مصلحة","الطابق الثالث","C"),
            ("OFF-007","مصلحة الوسائل العامة","Service des Moyens","مصلحة","الطابق الأرضي","A"),
            ("OFF-008","المخزن الرئيسي","Magasin Principal","مخزن","الطابق الأرضي","A"),
        ]
        for code,name,name_fr,typ,floor,building in default_offices:
            append_row("offices", {
                "id":gen_id(),"code":code,"name":name,"name_fr":name_fr,
                "type":typ,"floor":floor,"building":building,
                "surface":"","capacity":"","phone":"","email":"",
                "department":name,"notes":"","active":"True",
                "created_at":_now(),
            })