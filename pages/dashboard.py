# pages/dashboard.py

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.sheets import read_df, get_stock_df
from config import TRANSFER_STATUS, ROLES, has_perm


def show_dashboard():
    user = st.session_state.user
    role = user["role"]

    # ── تحية ─────────────────────────────────────────────
    hour = datetime.now().hour
    greet = "صباح الخير" if hour < 12 else ("مساء الخير" if hour < 18 else "مساء النور")
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0f0c29 0%,#1a1a2e 50%,#16213e 100%);
         border-radius:14px;padding:22px 28px;margin-bottom:22px;color:white;
         border-right:5px solid #e94560;">
        <h2 style="margin:0;font-size:1.5rem;">
            {ROLES[role]['icon']} {greet}، {user['full_name']}
        </h2>
        <p style="margin:5px 0 0;opacity:.72;font-size:.82rem;">
            {ROLES[role]['label']} &nbsp;·&nbsp; {user.get('department','')}
            &nbsp;·&nbsp; {datetime.now().strftime('%A %d %B %Y — %H:%M')}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── تحميل البيانات ────────────────────────────────────
    stock_df     = get_stock_df()
    products_df  = read_df("products")
    transfers_df = read_df("transfers")
    movements_df = read_df("stock_movements")
    offices_df   = read_df("offices")
    suppliers_df = read_df("suppliers")
    po_df        = read_df("purchase_orders")

    active_prods = products_df[products_df["active"].astype(str).str.strip().str.upper()=="TRUE"] if not products_df.empty else pd.DataFrame()
    active_offices = offices_df[offices_df["active"].astype(str).str.strip().str.upper()=="TRUE"] if not offices_df.empty else pd.DataFrame()
    active_sups    = suppliers_df[suppliers_df["active"].astype(str).str.strip().str.upper()=="TRUE"] if not suppliers_df.empty else pd.DataFrame()

    # ── حسابات ───────────────────────────────────────────
    total_products = len(active_prods)
    total_offices  = len(active_offices)
    total_suppliers= len(active_sups)

    low_stock = 0
    out_of_stock = 0
    if not stock_df.empty and not active_prods.empty:
        for _, p in active_prods.iterrows():
            pid = str(p.get("id",""))
            r   = stock_df[stock_df["product_id"].astype(str)==pid]
            qty = float(r.iloc[0]["quantity"]) if not r.empty else 0
            mn  = float(p.get("min_stock",0))
            if qty == 0: out_of_stock += 1
            elif qty <= mn: low_stock += 1

    pending_transfers = 0
    approved_transfers = 0
    if not transfers_df.empty:
        pending_transfers  = len(transfers_df[transfers_df["status"]=="pending"])
        approved_transfers = len(transfers_df[transfers_df["status"]=="approved"])

    today = datetime.now().strftime("%Y-%m-%d")
    today_in  = len(movements_df[movements_df["date"].str.startswith(today,na=False) & (movements_df["direction"]=="in")]) if not movements_df.empty else 0
    today_out = len(movements_df[movements_df["date"].str.startswith(today,na=False) & (movements_df["direction"]=="out")]) if not movements_df.empty else 0

    pending_po = 0
    if not po_df.empty:
        pending_po = len(po_df[po_df["status"].isin(["pending","approved"])])

    # ── صف 1: البطاقات الكبيرة ────────────────────────────
    c1,c2,c3,c4 = st.columns(4)
    _big_card(c1, str(total_products),   "📦 إجمالي المنتجات",   "#667eea","#764ba2")
    _big_card(c2, str(total_offices),    "🏢 المكاتب والمحلات",  "#43e97b","#38f9d7", dark=True)
    _big_card(c3, str(total_suppliers),  "🏭 الموردون",          "#fa709a","#fee140")
    _big_card(c4, str(pending_transfers),"⏳ طلبات معلقة",
              "#f59e0b","#d97706" if pending_transfers else "#6b7280",
              alert=pending_transfers>0)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── صف 2: تنبيهات ────────────────────────────────────
    c5,c6,c7,c8 = st.columns(4)
    _small_card(c5, str(out_of_stock),   "🔴 نفد المخزون",    "#ef4444" if out_of_stock else "#10b981")
    _small_card(c6, str(low_stock),      "🟠 مخزون منخفض",   "#f59e0b" if low_stock else "#10b981")
    _small_card(c7, str(approved_transfers), "✅ جاهز للتنفيذ", "#3b82f6")
    _small_card(c8, str(pending_po),     "📋 طلبات شراء معلقة","#8b5cf6")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── صف 3: جداول ──────────────────────────────────────
    col_a, col_b = st.columns([1,1])

    with col_a:
        st.markdown("#### ⚠️ تنبيهات المخزون")
        if active_prods.empty or stock_df.empty:
            st.info("لا توجد بيانات")
        else:
            alerts = []
            for _, p in active_prods.iterrows():
                pid = str(p.get("id",""))
                r   = stock_df[stock_df["product_id"].astype(str)==pid]
                qty = float(r.iloc[0]["quantity"]) if not r.empty else 0
                mn  = float(p.get("min_stock",0))
                if qty <= mn:
                    status = "🔴 نفد" if qty==0 else "🟠 منخفض"
                    alerts.append({
                        "المادة": p.get("name",""),
                        "المتاح": f"{qty:.0f}",
                        "الحد الأدنى": f"{mn:.0f}",
                        "الوحدة": p.get("unit_name",""),
                        "الحالة": status,
                    })
            if alerts:
                st.dataframe(pd.DataFrame(alerts), use_container_width=True, hide_index=True)
            else:
                st.success("✅ جميع المنتجات فوق حد التنبيه")

    with col_b:
        st.markdown("#### 📋 آخر سندات التحويل")
        if transfers_df.empty:
            st.info("لا توجد سندات بعد")
        else:
            last = transfers_df.tail(7)[::-1].copy()
            last["الحالة"] = last["status"].map(
                lambda s: TRANSFER_STATUS.get(s,{}).get("icon","") + " " + TRANSFER_STATUS.get(s,{}).get("label","")
            )
            show = {c:c for c in ["number","date","requesting_dept","الحالة"] if c in last.columns}
            rename = {"number":"السند","date":"التاريخ","requesting_dept":"المصلحة"}
            st.dataframe(last[list(show)].rename(columns=rename), use_container_width=True, hide_index=True)

    # ── صف 4: حركات اليوم + إحصاء شهري ──────────────────
    col_c, col_d = st.columns([1,1])

    with col_c:
        st.markdown("#### 🔄 آخر حركات المخزن")
        if movements_df.empty:
            st.info("لا توجد حركات")
        else:
            last_mv = movements_df.tail(8)[::-1].copy()
            type_map = {"in":"📥 دخول","out":"📤 خروج"}
            last_mv["النوع"] = last_mv.get("direction", last_mv.get("type","")).map(type_map)
            show = ["date","النوع","product_name","quantity","unit_name","reference_number"]
            avail = [c for c in show if c in last_mv.columns]
            rename2 = {"date":"التاريخ","product_name":"المادة","quantity":"الكمية",
                       "unit_name":"الوحدة","reference_number":"المرجع"}
            st.dataframe(last_mv[avail].rename(columns=rename2), use_container_width=True, hide_index=True)

    with col_d:
        st.markdown("#### 📊 توزيع المنتجات بالفئة")
        if not active_prods.empty and "category_name" in active_prods.columns:
            cat_counts = active_prods["category_name"].value_counts().head(8)
            st.bar_chart(cat_counts)
        else:
            st.info("أضف منتجات لرؤية الإحصاء")


# ── مساعدات بطاقات ───────────────────────────────────────────────────
def _big_card(col, val, label, c1, c2, dark=False, alert=False):
    txt = "#fff"
    border = "border:2px solid rgba(255,80,80,.6);" if alert else ""
    with col:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,{c1},{c2});border-radius:12px;
             padding:18px 14px;text-align:center;{border}
             box-shadow:0 4px 16px rgba(0,0,0,.13);">
            <div style="color:{txt};font-size:2.2rem;font-weight:900;line-height:1;">{val}</div>
            <div style="color:rgba(255,255,255,.85);font-size:.8rem;margin-top:4px;">{label}</div>
        </div>""", unsafe_allow_html=True)

def _small_card(col, val, label, color):
    with col:
        st.markdown(f"""
        <div style="background:white;border:1px solid #e9ecef;border-radius:10px;
             padding:14px;text-align:center;border-top:3px solid {color};
             box-shadow:0 2px 8px rgba(0,0,0,.06);">
            <div style="color:{color};font-size:1.7rem;font-weight:800;">{val}</div>
            <div style="color:#555;font-size:.78rem;margin-top:2px;">{label}</div>
        </div>""", unsafe_allow_html=True)
