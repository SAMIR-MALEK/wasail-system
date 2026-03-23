# config.py — النظام الضخم لإدارة الوسائل العامة

APP_NAME        = "نظام الوسائل العامة"
APP_VERSION     = "3.0"
FACULTY_NAME    = "كلية الحقوق والعلوم السياسية"
UNIVERSITY_NAME = "جامعة محمد البشير الإبراهيمي — برج بوعريريج"
FACULTY_CODE    = "FDSB-BBA"

# ══════════════════════════════════════════════
#  الأدوار والصلاحيات
# ══════════════════════════════════════════════
ROLES = {
    "مدير": {
        "label": "مدير الكلية",
        "icon": "👨‍💼",
        "color": "#7c3aed",
        "permissions": ["*"],   # كل الصلاحيات
    },
    "مسؤول_وسائل": {
        "label": "مسؤول مصلحة الوسائل",
        "icon": "🏛️",
        "color": "#1d4ed8",
        "permissions": [
            "dashboard","catalog","suppliers","offices","stock_in",
            "purchase_orders","transfers","approve_transfers",
            "inventory","reports","activity_log",
        ],
    },
    "أمين_مخزن": {
        "label": "أمين المخزن",
        "icon": "📦",
        "color": "#0369a1",
        "permissions": [
            "dashboard","catalog_view","stock_in",
            "execute_transfers","stock_view","inventory",
        ],
    },
    "رئيس_مصلحة": {
        "label": "رئيس مصلحة / مسؤول مكتب",
        "icon": "🏢",
        "color": "#059669",
        "permissions": [
            "dashboard","request_transfer","my_transfers","confirm_receipt",
        ],
    },
}

def has_perm(user: dict, perm: str) -> bool:
    perms = ROLES.get(user.get("role",""), {}).get("permissions", [])
    return "*" in perms or perm in perms

# ══════════════════════════════════════════════
#  المصالح والمكاتب (القائمة الافتراضية — تتوسع من DB)
# ══════════════════════════════════════════════
DEFAULT_DEPARTMENTS = [
    "الأمانة العامة",
    "مكتب الأستاذة",
    "مصلحة التدريس",
    "مصلحة البيداغوجيا",
    "مكتبة الكلية",
    "مصلحة الماستر والدكتوراه",
    "مصلحة الوسائل العامة",
]

# ══════════════════════════════════════════════
#  فئات المنتجات (افتراضية — تتوسع من DB)
# ══════════════════════════════════════════════
DEFAULT_CATEGORIES = [
    "قرطاسية ولوازم مكتبية",
    "مواد النظافة",
    "أجهزة حاسوبية",
    "أجهزة مكتبية",
    "أثاث",
    "مواد الطباعة",
    "مواد الضيافة",
    "كهرباء وإنارة",
    "أدوات وعتاد",
    "أخرى",
]

# ══════════════════════════════════════════════
#  وحدات القياس
# ══════════════════════════════════════════════
DEFAULT_UNITS = [
    "قطعة", "علبة", "رزمة", "لتر", "كيلوغرام",
    "رول", "كارتون", "مجموعة", "زوج", "متر",
    "كيلس", "طاقم", "حبة", "رطل",
]

# ══════════════════════════════════════════════
#  أنواع المكاتب/المحلات
# ══════════════════════════════════════════════
OFFICE_TYPES = [
    "مكتب إداري",
    "مصلحة",
    "قاعة دراسية",
    "قاعة محاضرات",
    "مخزن",
    "مكتبة",
    "مختبر / ورشة",
    "مرافق مشتركة",
]

# ══════════════════════════════════════════════
#  أنواع سندات التحويل
# ══════════════════════════════════════════════
TRANSFER_TYPES = {
    "تحويل_عادي":     "تحويل مواد عادي",
    "تحويل_طارئ":     "تحويل طارئ / عاجل",
    "تحويل_داخلي":    "تحويل داخلي بين مكتبين",
    "استرجاع":        "استرجاع مواد من مصلحة",
}

# ══════════════════════════════════════════════
#  حالات سند التحويل
# ══════════════════════════════════════════════
TRANSFER_STATUS = {
    "draft":    {"label":"مسودة",                   "color":"#6b7280","icon":"📝"},
    "pending":  {"label":"بانتظار الموافقة",         "color":"#f59e0b","icon":"⏳"},
    "approved": {"label":"موافق عليه",               "color":"#3b82f6","icon":"✅"},
    "executed": {"label":"منفَّذ — بانتظار الاستلام","color":"#8b5cf6","icon":"🚚"},
    "received": {"label":"مستلَم ومؤكَّد",           "color":"#10b981","icon":"📬"},
    "rejected": {"label":"مرفوض",                   "color":"#ef4444","icon":"❌"},
    "partial":  {"label":"تسليم جزئي",              "color":"#f97316","icon":"⚠️"},
}

# ══════════════════════════════════════════════
#  حالات طلبات الشراء
# ══════════════════════════════════════════════
PURCHASE_STATUS = {
    "draft":     {"label":"مسودة",              "color":"#6b7280","icon":"📝"},
    "pending":   {"label":"بانتظار الموافقة",   "color":"#f59e0b","icon":"⏳"},
    "approved":  {"label":"معتمد",              "color":"#10b981","icon":"✅"},
    "ordered":   {"label":"تم الطلب من المورد","color":"#3b82f6","icon":"📦"},
    "received":  {"label":"مستلَم",             "color":"#7c3aed","icon":"📬"},
    "cancelled": {"label":"ملغى",              "color":"#ef4444","icon":"❌"},
}

# ══════════════════════════════════════════════
#  أوراق Google Sheets
# ══════════════════════════════════════════════
SHEETS = {
    # كتالوج المنتجات
    "categories":       "فئات_المنتجات",
    "units":            "وحدات_القياس",
    "products":         "المنتجات",
    # الموردون
    "suppliers":        "الموردون",
    "supplier_contacts":"جهات_اتصال_الموردين",
    # المكاتب والمسؤولون
    "offices":          "المكاتب_والمحلات",
    "office_managers":  "مسؤولو_المكاتب",
    # المخزون
    "stock":            "المخزون",
    "stock_movements":  "حركات_المخزن",
    # الشراء
    "purchase_orders":  "طلبات_الشراء",
    "purchase_items":   "تفاصيل_طلبات_الشراء",
    "invoices":         "فواتير_الاستلام",
    "invoice_items":    "تفاصيل_الفواتير",
    # التحويل
    "transfers":        "سندات_التحويل",
    "transfer_items":   "تفاصيل_السندات",
    # الجرد
    "inventory":        "جلسات_الجرد",
    "inventory_items":  "تفاصيل_الجرد",
    # النظام
    "users":            "المستخدمون",
    "activity_log":     "سجل_النشاط",
}

# ══════════════════════════════════════════════
#  أعمدة كل ورقة
# ══════════════════════════════════════════════
COLUMNS = {
    "categories": [
        "id","name","name_fr","description","icon","active","created_at",
    ],
    "units": [
        "id","name","name_fr","symbol","active","created_at",
    ],
    "products": [
        "id","code","name","name_fr","category_id","category_name",
        "unit_id","unit_name","unit_symbol",
        "min_stock","max_stock","reorder_qty",
        "description","specifications","brand","model",
        "active","created_at","created_by",
    ],
    "suppliers": [
        "id","code","name","name_fr","type",
        "phone","phone2","email","fax",
        "address","wilaya","nif","nis","rc",
        "bank_account","bank_name",
        "payment_terms","delivery_days",
        "rating","notes","active","created_at","created_by",
    ],
    "supplier_contacts": [
        "id","supplier_id","supplier_name",
        "full_name","position","phone","email","notes","active",
    ],
    "offices": [
        "id","code","name","name_fr","type","floor","building",
        "surface","capacity","phone","email",
        "department","notes","active","created_at",
    ],
    "office_managers": [
        "id","office_id","office_name","office_code",
        "manager_name","manager_title","manager_phone","manager_email",
        "start_date","end_date","is_current","notes",
    ],
    "stock": [
        "product_id","product_code","product_name","unit_name",
        "quantity","reserved_qty","available_qty",
        "last_in_date","last_out_date","last_updated",
    ],
    "stock_movements": [
        "id","date","type","direction",
        "product_id","product_code","product_name","unit_name",
        "quantity","unit_cost","total_cost",
        "reference_type","reference_id","reference_number",
        "from_location","to_location",
        "supplier_id","supplier_name",
        "notes","user_id","user_name",
    ],
    "purchase_orders": [
        "id","number","date","supplier_id","supplier_name",
        "status","priority",
        "requested_by","requested_by_id",
        "approved_by","approved_at",
        "expected_delivery","actual_delivery",
        "total_amount","currency",
        "notes","created_at",
    ],
    "purchase_items": [
        "id","order_id","order_number",
        "product_id","product_code","product_name","unit_name",
        "requested_qty","approved_qty","received_qty",
        "unit_price","total_price","notes",
    ],
    "invoices": [
        "id","number","invoice_number","date",
        "supplier_id","supplier_name",
        "purchase_order_id","purchase_order_number",
        "total_amount","tax_amount","net_amount",
        "received_by","received_at",
        "notes","created_at",
    ],
    "invoice_items": [
        "id","invoice_id","invoice_number",
        "product_id","product_code","product_name","unit_name",
        "quantity","unit_price","total_price","notes",
    ],
    "transfers": [
        "id","number","date","type",
        "requesting_dept","requesting_office_id","requesting_office_code",
        "requested_by","requested_by_id",
        "status","priority",
        "approved_by","approved_at",
        "executed_by","executed_at",
        "received_by","received_at",
        "notes","rejection_reason","created_at",
    ],
    "transfer_items": [
        "id","transfer_id","transfer_number",
        "product_id","product_code","product_name","unit_name",
        "requested_qty","approved_qty","delivered_qty","notes",
    ],
    "inventory": [
        "id","number","date","type","scope",
        "conducted_by","conducted_by_id",
        "validated_by","validated_at",
        "status","started_at","finished_at",
        "total_items","items_ok","items_shortage","items_surplus",
        "notes",
    ],
    "inventory_items": [
        "id","inventory_id","inventory_number",
        "product_id","product_code","product_name","unit_name",
        "theoretical_qty","actual_qty","difference",
        "unit_cost","difference_value",
        "location","notes","counted_by",
    ],
    "users": [
        "id","username","password_hash","full_name","title",
        "role","department","office_id",
        "phone","email",
        "active","last_login","created_at","created_by",
    ],
    "activity_log": [
        "id","datetime","user_id","user_name",
        "action","module","reference_id","reference_number",
        "details","ip_address",
    ],
}
