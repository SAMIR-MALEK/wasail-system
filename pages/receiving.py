# pages/receiving.py — استلام البضاعة + طلبات الشراء

import streamlit as st
import pandas as pd
from datetime import datetime, date
from utils.sheets import (
    read_df, append_row, update_row, gen_id,
    update_stock, next_purchase_order_number,
    next_invoice_number, log_activity
)


def show_receiving():
    user = st.session_state.user
    st.markdown("## 📥 الاستلام وطلبات الشراء")
    tabs = st.tabs([
        "📦 استلام بضاعة من مورد",
        "📋 طلبات الشراء",
        "➕ طلب شراء جديد",
        "📄 سجل الفواتير",
    ])
    with tabs[0]: _receive_goods(user)
    with tabs[1]: _list_purchase_orders(user)
    with tabs[2]: _new_purchase_order(user)
    with tabs[3]: _invoices_log()


# ══════════════════════════════════════════════
#  استلام بضاعة
# ══════════════════════════════════════════════
def _receive_goods(user):
    st.markdown("### 📦 تسجيل استلام بضاعة من مورد")

    products_df  = read_df("products")
    suppliers_df = read_df("suppliers")
    po_df        = read_df("purchase_orders")

    active_prods = products_df[products_df["active"].astype(str)=="True"] if not products_df.empty else pd.DataFrame()
    active_sups  = suppliers_df[suppliers_df["active"].astype(str)=="True"] if not suppliers_df.empty else pd.DataFrame()

    if active_prods.empty:
        st.warning("⚠️ لا توجد منتجات مسجلة. أضف منتجات أولاً من كتالوج المنتجات.")
        return

    with st.form("receive_form", clear_on_submit=True):
        st.markdown("#### معلومات الاستلام")
        rc1,rc2,rc3 = st.columns(3)
        with rc1:
            rec_date   = st.date_input("تاريخ الاستلام ★", value=date.today())
            inv_number = st.text_input("رقم فاتورة المورد ★", placeholder="FAC-2024-001")
        with rc2:
            if not active_sups.empty:
                sup_opts = ["-- اختر المورد --"] + list(active_sups["name"])
                sel_sup  = st.selectbox("المورد ★", sup_opts)
            else:
                sel_sup = st.text_input("اسم المورد ★")
                active_sups = pd.DataFrame()
            # ربط بطلب شراء
            if not po_df.empty:
                ordered_po = po_df[po_df["status"].isin(["approved","ordered"])]
                po_opts = ["لا يوجد طلب شراء مرتبط"] + list(ordered_po.get("number", []))
                sel_po = st.selectbox("طلب الشراء المرتبط (اختياري)", po_opts)
            else:
                sel_po = "لا يوجد"
        with rc3:
            total_amount = st.number_input("المبلغ الإجمالي (دج)", min_value=0.0, step=100.0)
            notes        = st.text_area("ملاحظات", height=80)

        st.markdown("---")
        st.markdown("#### المواد المستلمة")

        prod_names  = list(active_prods["name"])
        pid_map     = dict(zip(active_prods["name"], active_prods["id"]))
        pcode_map   = dict(zip(active_prods["name"], active_prods.get("code",active_prods["name"])))
        unit_map    = dict(zip(active_prods["name"], active_prods.get("unit_name",active_prods.get("unit",""))))

        items = []
        for i in range(1, 16):  # حتى 15 مادة
            ic1,ic2,ic3,ic4 = st.columns([4, 2, 2, 2])
            with ic1:
                pname = st.selectbox(f"المادة {i}", ["-- اختر --"]+prod_names, key=f"rc_p{i}")
            with ic2:
                qty = st.number_input("الكمية ★", min_value=0.0, step=1.0, key=f"rc_q{i}")
            with ic3:
                unit = st.text_input("الوحدة", key=f"rc_u{i}",
                    value=unit_map.get(pname,"") if pname!="-- اختر --" else "")
            with ic4:
                unit_price = st.number_input("سعر الوحدة (دج)", min_value=0.0, step=10.0, key=f"rc_pr{i}")
            if pname != "-- اختر --" and qty > 0:
                items.append({
                    "product_id":   str(pid_map.get(pname,"")),
                    "product_code": str(pcode_map.get(pname,"")),
                    "product_name": pname,
                    "unit_name":    unit,
                    "quantity":     qty,
                    "unit_price":   unit_price,
                    "total_price":  qty * unit_price,
                })

        submitted = st.form_submit_button("✅ تسجيل الاستلام", type="primary", use_container_width=True)

    if submitted:
        errs = []
        if not items:         errs.append("أضف مادة واحدة على الأقل")
        if not inv_number.strip(): errs.append("رقم الفاتورة مطلوب")
        if not active_sups.empty and sel_sup == "-- اختر المورد --":
            errs.append("اختر المورد")
        if errs:
            for e in errs: st.error(f"❌ {e}")
            return

        sup_id   = ""
        sup_name = sel_sup
        if not active_sups.empty and sel_sup != "-- اختر المورد --":
            r = active_sups[active_sups["name"]==sel_sup]
            if not r.empty:
                sup_id = str(r.iloc[0]["id"])

        inv_id  = gen_id()
        inv_num = next_invoice_number()
        now     = datetime.now().strftime("%Y-%m-%d %H:%M")

        try:
            # حفظ الفاتورة
            append_row("invoices", {
                "id":                   inv_id,
                "number":               inv_num,
                "invoice_number":       inv_number.strip(),
                "date":                 str(rec_date),
                "supplier_id":          sup_id,
                "supplier_name":        sup_name,
                "purchase_order_id":    "",
                "purchase_order_number":sel_po if sel_po!="لا يوجد طلب شراء مرتبط" else "",
                "total_amount":         total_amount,
                "tax_amount":           0,
                "net_amount":           total_amount,
                "received_by":          user["full_name"],
                "received_at":          now,
                "notes":                notes,
                "created_at":           now,
            })

            # حفظ تفاصيل الفاتورة وتحديث المخزون
            for item in items:
                append_row("invoice_items", {
                    "id":             gen_id(),
                    "invoice_id":     inv_id,
                    "invoice_number": inv_num,
                    "product_id":     item["product_id"],
                    "product_code":   item["product_code"],
                    "product_name":   item["product_name"],
                    "unit_name":      item["unit_name"],
                    "quantity":       item["quantity"],
                    "unit_price":     item["unit_price"],
                    "total_price":    item["total_price"],
                    "notes":          "",
                })

                # تسجيل حركة دخول
                append_row("stock_movements", {
                    "id":               gen_id(),
                    "date":             str(rec_date),
                    "type":             "in",
                    "direction":        "in",
                    "product_id":       item["product_id"],
                    "product_code":     item["product_code"],
                    "product_name":     item["product_name"],
                    "unit_name":        item["unit_name"],
                    "quantity":         item["quantity"],
                    "unit_cost":        item["unit_price"],
                    "total_cost":       item["total_price"],
                    "reference_type":   "invoice",
                    "reference_id":     inv_id,
                    "reference_number": inv_num,
                    "from_location":    sup_name,
                    "to_location":      "المخزن الرئيسي",
                    "supplier_id":      sup_id,
                    "supplier_name":    sup_name,
                    "notes":            f"فاتورة رقم: {inv_number}",
                    "user_id":          user["id"],
                    "user_name":        user["full_name"],
                })
                # تحديث المخزون
                update_stock(item["product_id"], item["product_code"],
                             item["product_name"], item["unit_name"],
                             item["quantity"], "in")

            log_activity(user, "استلام بضاعة", "الاستلام", inv_id, inv_num,
                        f"{len(items)} مادة من {sup_name}")

            st.success(f"""
✅ **تم تسجيل الاستلام بنجاح!**

- رقم الإيصال: **{inv_num}**
- فاتورة المورد: **{inv_number}**
- عدد المواد: **{len(items)}**
- المبلغ: **{total_amount:,.0f} دج**
""")
            # ملخص
            st.dataframe(
                pd.DataFrame(items)[["product_name","quantity","unit_name","unit_price","total_price"]].rename(columns={
                    "product_name":"المادة","quantity":"الكمية","unit_name":"الوحدة",
                    "unit_price":"سعر الوحدة","total_price":"الإجمالي"
                }),
                use_container_width=True, hide_index=True
            )
        except Exception as e:
            st.error(f"❌ {e}")


# ══════════════════════════════════════════════
#  قائمة طلبات الشراء
# ══════════════════════════════════════════════
def _list_purchase_orders(user):
    st.markdown("### 📋 طلبات الشراء")
    from config import PURCHASE_STATUS
    df = read_df("purchase_orders")
    if df.empty:
        st.info("لا توجد طلبات شراء بعد")
        return

    fc1,fc2 = st.columns(2)
    with fc1:
        status_labels = ["الكل"] + [v["label"] for v in PURCHASE_STATUS.values()]
        sf = st.selectbox("الحالة", status_labels)
    with fc2:
        search = st.text_input("🔍 بحث برقم الطلب أو المورد")

    d = df.copy()
    if sf != "الكل":
        sk = next((k for k,v in PURCHASE_STATUS.items() if v["label"]==sf), None)
        if sk: d = d[d["status"]==sk]
    if search:
        d = d[
            d["number"].str.contains(search, case=False, na=False) |
            d["supplier_name"].str.contains(search, case=False, na=False)
        ]

    d["الحالة"] = d["status"].map(
        lambda s: PURCHASE_STATUS.get(s,{}).get("icon","") + " " + PURCHASE_STATUS.get(s,{}).get("label","")
    )

    # موافقة
    if user["role"] in ["مدير","مسؤول_وسائل"]:
        pending = d[df["status"]=="pending"]
        if not pending.empty:
            st.warning(f"⏳ يوجد **{len(pending)}** طلب شراء بانتظار موافقتك")
            items_df = read_df("purchase_items")
            for _, po in pending.iterrows():
                with st.expander(f"📋 {po['number']} — {po.get('supplier_name','')}"):
                    t_items = items_df[items_df["order_id"]==po["id"]] if not items_df.empty else pd.DataFrame()
                    if not t_items.empty:
                        st.dataframe(t_items[["product_name","unit_name","requested_qty","unit_price","total_price"]].rename(columns={
                            "product_name":"المادة","unit_name":"الوحدة","requested_qty":"الكمية",
                            "unit_price":"سعر الوحدة","total_price":"الإجمالي"
                        }), use_container_width=True, hide_index=True)
                    ca,cb = st.columns(2)
                    with ca:
                        if st.button("✅ اعتماد الطلب", key=f"appo_{po['id']}", type="primary"):
                            update_row("purchase_orders", po["id"], {
                                "status":"approved","approved_by":user["full_name"],
                                "approved_at":datetime.now().strftime("%Y-%m-%d %H:%M"),
                            })
                            st.success("✅ تم الاعتماد")
                            st.rerun()
            st.divider()

    show = {
        "number":"رقم الطلب","date":"التاريخ","supplier_name":"المورد",
        "priority":"الأولوية","total_amount":"المبلغ","الحالة":"الحالة",
    }
    avail = {k:v for k,v in show.items() if k in d.columns or k=="الحالة"}
    st.dataframe(d[[c for c in avail if c in d.columns]][::-1].rename(columns=avail),
                 use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════
#  طلب شراء جديد
# ══════════════════════════════════════════════
def _new_purchase_order(user):
    st.markdown("### ➕ إنشاء طلب شراء جديد")
    products_df  = read_df("products")
    suppliers_df = read_df("suppliers")
    active_prods = products_df[products_df["active"].astype(str)=="True"] if not products_df.empty else pd.DataFrame()
    active_sups  = suppliers_df[suppliers_df["active"].astype(str)=="True"] if not suppliers_df.empty else pd.DataFrame()

    if active_prods.empty:
        st.warning("أضف منتجات أولاً")
        return

    with st.form("new_po", clear_on_submit=True):
        pc1,pc2 = st.columns(2)
        with pc1:
            sup_opts = ["-- اختر المورد --"] + (list(active_sups["name"]) if not active_sups.empty else [])
            sel_sup  = st.selectbox("المورد ★", sup_opts)
            priority = st.selectbox("الأولوية", ["عادي","عاجل","مستعجل جداً"])
            exp_delivery = st.date_input("تاريخ التسليم المتوقع")
        with pc2:
            notes = st.text_area("ملاحظات / مبرر الطلب", height=100)

        st.markdown("---")
        prod_names = list(active_prods["name"])
        pid_map    = dict(zip(active_prods["name"], active_prods["id"]))
        pcode_map  = dict(zip(active_prods["name"], active_prods.get("code",active_prods["name"])))
        unit_map   = dict(zip(active_prods["name"], active_prods.get("unit_name",active_prods.get("unit",""))))

        items = []
        for i in range(1, 11):
            ic1,ic2,ic3 = st.columns([4,2,2])
            with ic1:
                pname = st.selectbox(f"المادة {i}", ["-- اختر --"]+prod_names, key=f"po_p{i}")
            with ic2:
                qty = st.number_input("الكمية", min_value=0.0, step=1.0, key=f"po_q{i}")
            with ic3:
                price = st.number_input("سعر الوحدة التقديري", min_value=0.0, step=10.0, key=f"po_pr{i}")
            if pname != "-- اختر --" and qty > 0:
                items.append({
                    "product_id":   str(pid_map.get(pname,"")),
                    "product_code": str(pcode_map.get(pname,"")),
                    "product_name": pname,
                    "unit_name":    unit_map.get(pname,""),
                    "requested_qty":qty,
                    "unit_price":   price,
                    "total_price":  qty*price,
                })

        submitted = st.form_submit_button("📤 إرسال طلب الشراء", type="primary", use_container_width=True)

    if submitted:
        if not items: st.error("❌ أضف مادة واحدة على الأقل"); return
        if sel_sup == "-- اختر المورد --": st.error("❌ اختر المورد"); return
        try:
            sup_id = ""
            if not active_sups.empty:
                r = active_sups[active_sups["name"]==sel_sup]
                if not r.empty: sup_id = str(r.iloc[0]["id"])
            po_id  = gen_id()
            po_num = next_purchase_order_number()
            total  = sum(i["total_price"] for i in items)
            now    = datetime.now().strftime("%Y-%m-%d %H:%M")
            append_row("purchase_orders", {
                "id":gen_id(),"number":po_num,"date":now,
                "supplier_id":sup_id,"supplier_name":sel_sup,
                "status":"pending","priority":priority,
                "requested_by":user["full_name"],"requested_by_id":user["id"],
                "approved_by":"","approved_at":"",
                "expected_delivery":str(exp_delivery),"actual_delivery":"",
                "total_amount":total,"currency":"دج",
                "notes":notes,"created_at":now,
            })
            for item in items:
                append_row("purchase_items", {
                    "id":gen_id(),"order_id":po_id,"order_number":po_num,
                    "product_id":item["product_id"],"product_code":item["product_code"],
                    "product_name":item["product_name"],"unit_name":item["unit_name"],
                    "requested_qty":item["requested_qty"],"approved_qty":"","received_qty":"",
                    "unit_price":item["unit_price"],"total_price":item["total_price"],"notes":"",
                })
            st.success(f"✅ تم إرسال طلب الشراء | رقم: **{po_num}** | المبلغ التقديري: **{total:,.0f} دج**")
        except Exception as e:
            st.error(f"❌ {e}")


# ══════════════════════════════════════════════
#  سجل الفواتير
# ══════════════════════════════════════════════
def _invoices_log():
    st.markdown("### 📄 سجل فواتير الاستلام")
    df = read_df("invoices")
    if df.empty:
        st.info("لا توجد فواتير بعد")
        return
    search = st.text_input("🔍 بحث برقم الفاتورة أو المورد")
    d = df.copy()
    if search:
        d = d[
            d["number"].str.contains(search, case=False, na=False) |
            d["invoice_number"].str.contains(search, case=False, na=False) |
            d["supplier_name"].str.contains(search, case=False, na=False)
        ]
    show = ["number","invoice_number","date","supplier_name",
            "total_amount","received_by","received_at"]
    avail = [c for c in show if c in d.columns]
    rename = {
        "number":"رقم النظام","invoice_number":"رقم الفاتورة",
        "date":"التاريخ","supplier_name":"المورد",
        "total_amount":"المبلغ (دج)","received_by":"استلم بواسطة","received_at":"وقت الاستلام"
    }
    st.dataframe(d[avail][::-1].rename(columns=rename), use_container_width=True, hide_index=True)
    if not d.empty and "total_amount" in d.columns:
        total = pd.to_numeric(d["total_amount"], errors="coerce").sum()
        st.metric("إجمالي قيمة المشتريات", f"{total:,.0f} دج")
