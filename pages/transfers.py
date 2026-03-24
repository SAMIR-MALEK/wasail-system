# pages/transfers.py

import streamlit as st
import pandas as pd
from datetime import datetime
from utils.sheets import (
    read_df, append_row, update_row, update_stock,
    gen_id, next_transfer_number, get_product_stock, log_activity
)
from utils.print_transfer import print_link
from config import TRANSFER_STATUS, TRANSFER_TYPES, has_perm


def show_transfers():
    user = st.session_state.user
    role = user["role"]
    st.markdown("## 📋 سندات التحويل")

    if has_perm(user, "approve_transfers"):
        tabs = st.tabs(["📄 كل السندات","➕ طلب جديد","✅ الموافقة","📊 إحصاءات"])
        with tabs[0]: _all(user)
        with tabs[1]: _create(user)
        with tabs[2]: _approve(user)
        with tabs[3]: _stats()
    elif has_perm(user, "execute_transfers"):
        tabs = st.tabs(["📦 تنفيذ السندات","🗂️ سجل التنفيذ"])
        with tabs[0]: _execute(user)
        with tabs[1]: _executed_log(user)
    else:
        tabs = st.tabs(["➕ طلب جديد","📄 طلباتي","📬 تأكيد الاستلام"])
        with tabs[0]: _create(user)
        with tabs[1]: _my(user)
        with tabs[2]: _confirm(user)


# ── إنشاء طلب ────────────────────────────────────────────────────────
def _create(user):
    st.markdown("### ➕ طلب تحويل مواد جديد")
    products_df = read_df("products")
    offices_df  = read_df("offices")
    active_prods= products_df[products_df["active"].astype(str).str.strip().str.upper()=="TRUE"] if not products_df.empty else pd.DataFrame()
    active_off  = offices_df[offices_df["active"].astype(str).str.strip().str.upper()=="TRUE"]   if not offices_df.empty  else pd.DataFrame()

    if active_prods.empty:
        st.warning("لا توجد منتجات مسجلة."); return

    office_opts = []
    office_id_map = {}
    office_code_map = {}
    if not active_off.empty:
        office_opts = list(active_off["name"])
        office_id_map  = dict(zip(active_off["name"], active_off["id"]))
        office_code_map= dict(zip(active_off["name"], active_off.get("code",active_off["name"])))

    with st.form("new_tr", clear_on_submit=True):
        tc1,tc2,tc3 = st.columns(3)
        with tc1:
            if has_perm(user,"approve_transfers"):
                dept = st.selectbox("المصلحة الطالبة ★",
                    office_opts if office_opts else ["-- لا توجد مكاتب --"])
            else:
                dept = user.get("department","")
                st.info(f"المصلحة: **{dept}**")
        with tc2:
            tr_type  = st.selectbox("نوع التحويل ★", list(TRANSFER_TYPES.values()))
            priority = st.selectbox("الأولوية", ["عادي","عاجل","مستعجل"])
        with tc3:
            notes = st.text_area("سبب الطلب / ملاحظات", height=80)

        st.markdown("---")
        st.markdown("### المواد المطلوبة")
        prod_names = list(active_prods["name"])
        pid_map    = dict(zip(active_prods["name"], active_prods["id"]))
        pcode_map  = dict(zip(active_prods["name"], active_prods.get("code",active_prods["name"])))
        unit_map   = dict(zip(active_prods["name"], active_prods.get("unit_name",active_prods.get("unit",""))))

        items = []
        for i in range(1, 16):
            ic = st.columns([4,2,2])
            with ic[0]: pname = st.selectbox(f"المادة {i}",["-- اختر --"]+prod_names, key=f"tr_p{i}")
            with ic[1]: qty   = st.number_input("الكمية", min_value=0.0, step=1.0, key=f"tr_q{i}")
            with ic[2]:
                if pname != "-- اختر --":
                    avail = get_product_stock(pid_map.get(pname,""))
                    color = "#10b981" if avail > 0 else "#ef4444"
                    st.markdown(
                        f"<div style='padding:6px;border-radius:5px;background:#f8f9fa;"
                        f"border-right:3px solid {color};font-size:.82rem;'>"
                        f"متاح: <strong style='color:{color};'>{avail:.0f}</strong> {unit_map.get(pname,'')}</div>",
                        unsafe_allow_html=True
                    )
            if pname != "-- اختر --" and qty > 0:
                items.append({
                    "product_id":   str(pid_map.get(pname,"")),
                    "product_code": str(pcode_map.get(pname,"")),
                    "product_name": pname,
                    "unit_name":    unit_map.get(pname,""),
                    "requested_qty":qty,
                })

        submitted = st.form_submit_button("📤 إرسال الطلب", type="primary", use_container_width=True)

    if submitted:
        if not items: st.error("❌ أضف مادة واحدة على الأقل"); return
        try:
            tid  = gen_id()
            tnum = next_transfer_number()
            now  = datetime.now().strftime("%Y-%m-%d %H:%M")
            off_id   = office_id_map.get(dept,"")
            off_code = office_code_map.get(dept,"")
            tr_type_key = next((k for k,v in TRANSFER_TYPES.items() if v==tr_type), tr_type)

            append_row("transfers", {
                "id":tid,"number":tnum,"date":now,"type":tr_type,
                "requesting_dept":dept,
                "requesting_office_id":off_id,"requesting_office_code":off_code,
                "requested_by":user["full_name"],"requested_by_id":user["id"],
                "status":"pending","priority":priority,
                "approved_by":"","approved_at":"",
                "executed_by":"","executed_at":"",
                "received_by":"","received_at":"",
                "notes":notes,"rejection_reason":"","created_at":now,
            })
            for item in items:
                append_row("transfer_items",{
                    "id":gen_id(),"transfer_id":tid,"transfer_number":tnum,
                    "product_id":item["product_id"],"product_code":item["product_code"],
                    "product_name":item["product_name"],"unit_name":item["unit_name"],
                    "requested_qty":item["requested_qty"],"approved_qty":"",
                    "delivered_qty":"","notes":"",
                })
            log_activity(user,"إنشاء سند تحويل","التحويل",tid,tnum,
                        f"{len(items)} مادة لـ {dept}")
            st.success(f"✅ رقم السند: **{tnum}** | الأولوية: **{priority}**")
        except Exception as e:
            st.error(f"❌ {e}")


# ── الموافقة ─────────────────────────────────────────────────────────
def _approve(user):
    st.markdown("### ✅ الموافقة على طلبات التحويل")
    transfers_df = read_df("transfers")
    if transfers_df.empty: st.info("لا توجد سندات"); return
    pending = transfers_df[transfers_df["status"]=="pending"]
    if pending.empty: st.success("✅ لا توجد طلبات معلقة"); return

    items_df = read_df("transfer_items")
    for _,t in pending.iterrows():
        ti = items_df[items_df["transfer_id"].astype(str)==str(t["id"])] if not items_df.empty else pd.DataFrame()
        with st.expander(f"📋 {t['number']}  ·  {t['requesting_dept']}  ·  {t.get('priority','')}  ·  {t.get('date','')}"):
            priority_color = {"عادي":"#6b7280","عاجل":"#f59e0b","مستعجل":"#ef4444"}.get(t.get("priority","عادي"),"#6b7280")
            st.markdown(f"""
            <div style="display:flex;gap:12px;margin-bottom:12px;flex-wrap:wrap">
                <span style="background:{priority_color}22;color:{priority_color};
                      border:1px solid {priority_color}55;padding:3px 10px;border-radius:20px;font-size:.8rem">
                    ⚡ {t.get('priority','')}
                </span>
                <span style="background:#f0f4ff;color:#3b82f6;padding:3px 10px;border-radius:20px;font-size:.8rem">
                    📋 {t.get('type','')}
                </span>
            </div>
            """, unsafe_allow_html=True)

            cc1,cc2 = st.columns(2)
            with cc1:
                st.markdown(f"**طلب بواسطة:** {t.get('requested_by','')}")
                st.markdown(f"**التاريخ:** {t.get('date','')}")
                st.markdown(f"**ملاحظات:** {t.get('notes','—')}")

            if not ti.empty:
                # تحقق من المخزون
                stock_ok = True
                for _,item in ti.iterrows():
                    avail = get_product_stock(str(item["product_id"]))
                    req   = float(item.get("requested_qty",0))
                    if req > avail:
                        st.warning(f"⚠️ **{item['product_name']}**: مطلوب {req:.0f} — متاح {avail:.0f}")
                        stock_ok = False

                st.dataframe(
                    ti[["product_code","product_name","unit_name","requested_qty"]].rename(columns={
                        "product_code":"الرمز","product_name":"المادة",
                        "unit_name":"الوحدة","requested_qty":"الكمية المطلوبة"
                    }),
                    use_container_width=True, hide_index=True
                )

            ca,cb,cc = st.columns([2,3,2])
            with ca:
                if st.button("✅ موافقة", key=f"appr_{t['id']}", type="primary"):
                    now = datetime.now().strftime("%Y-%m-%d %H:%M")
                    update_row("transfers", t["id"], {
                        "status":"approved","approved_by":user["full_name"],"approved_at":now
                    })
                    log_activity(user,"موافقة سند","التحويل",t["id"],t["number"])
                    st.success(f"✅ تمت الموافقة على {t['number']}"); st.rerun()
            with cb:
                reason = st.text_input("سبب الرفض", key=f"rej_r_{t['id']}")
            with cc:
                if st.button("❌ رفض", key=f"rej_{t['id']}"):
                    if not reason.strip(): st.warning("أدخل سبب الرفض")
                    else:
                        update_row("transfers",t["id"],{
                            "status":"rejected","approved_by":user["full_name"],
                            "approved_at":datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "rejection_reason":reason
                        })
                        st.error(f"❌ تم رفض {t['number']}"); st.rerun()


# ── تنفيذ (أمين المخزن) ──────────────────────────────────────────────
def _execute(user):
    st.markdown("### 📦 تنفيذ سندات التحويل")
    transfers_df = read_df("transfers")
    if transfers_df.empty: st.info("لا توجد سندات"); return
    approved = transfers_df[transfers_df["status"]=="approved"]
    if approved.empty: st.info("✅ لا توجد سندات موافق عليها بانتظار التنفيذ"); return

    items_df = read_df("transfer_items")
    for _,t in approved.iterrows():
        ti = items_df[items_df["transfer_id"].astype(str)==str(t["id"])] if not items_df.empty else pd.DataFrame()
        with st.expander(f"📋 {t['number']}  ·  {t['requesting_dept']}  ·  وافق: {t.get('approved_by','')}"):
            if ti.empty: st.warning("لا تفاصيل لهذا السند"); continue

            st.markdown("##### الكميات المسلَّمة:")
            delivered = {}
            for _,item in ti.iterrows():
                avail = get_product_stock(str(item["product_id"]))
                req   = float(item.get("requested_qty",0))
                ic1,ic2,ic3 = st.columns([3,2,2])
                with ic1:
                    st.markdown(f"**{item['product_name']}** ({item['unit_name']})")
                    st.caption(f"الرمز: {item.get('product_code','')}")
                with ic2:
                    color = "#10b981" if avail>=req else "#f59e0b"
                    st.markdown(
                        f"<div style='padding:6px;border-radius:5px;background:#f8f9fa;"
                        f"border-right:3px solid {color};font-size:.82rem;'>"
                        f"مطلوب: <b>{req:.0f}</b><br>"
                        f"متاح: <b style='color:{color}'>{avail:.0f}</b></div>",
                        unsafe_allow_html=True
                    )
                with ic3:
                    d_qty = st.number_input(
                        "كمية التسليم",
                        min_value=0.0, max_value=float(avail),
                        value=min(req, float(avail)),
                        key=f"del_{t['id']}_{item['id']}"
                    )
                    delivered[str(item["id"])] = d_qty

            if st.button(f"🚚 تنفيذ وخصم المخزون", key=f"exec_{t['id']}", type="primary"):
                try:
                    now = datetime.now().strftime("%Y-%m-%d %H:%M")
                    for _,item in ti.iterrows():
                        d_qty = delivered.get(str(item["id"]),0)
                        if d_qty > 0:
                            update_stock(
                                str(item["product_id"]),item.get("product_code",""),
                                item["product_name"],item["unit_name"],-d_qty,"out"
                            )
                            append_row("stock_movements",{
                                "id":gen_id(),"date":now,"type":"out","direction":"out",
                                "product_id":item["product_id"],"product_code":item.get("product_code",""),
                                "product_name":item["product_name"],"unit_name":item["unit_name"],
                                "quantity":d_qty,"unit_cost":"","total_cost":"",
                                "reference_type":"transfer","reference_id":t["id"],
                                "reference_number":t["number"],
                                "from_location":"المخزن الرئيسي","to_location":t["requesting_dept"],
                                "supplier_id":"","supplier_name":"",
                                "notes":f"سند تحويل إلى {t['requesting_dept']}",
                                "user_id":user["id"],"user_name":user["full_name"],
                            })
                            update_row("transfer_items",item["id"],{"delivered_qty":d_qty})
                    update_row("transfers",t["id"],{
                        "status":"executed","executed_by":user["full_name"],"executed_at":now
                    })
                    log_activity(user,"تنفيذ سند تحويل","التحويل",t["id"],t["number"])
                    st.success(f"✅ تم تنفيذ {t['number']}"); st.rerun()
                except Exception as e:
                    st.error(f"❌ {e}")


# ── تأكيد الاستلام ───────────────────────────────────────────────────
def _confirm(user):
    st.markdown("### 📬 تأكيد استلام المواد")
    transfers_df = read_df("transfers")
    if transfers_df.empty: st.info("لا توجد سندات"); return
    dept = user.get("department","")
    executed = transfers_df[
        (transfers_df["status"]=="executed") &
        (transfers_df["requesting_dept"]==dept)
    ]
    if executed.empty: st.success("✅ لا توجد سندات بانتظار تأكيد الاستلام"); return

    items_df = read_df("transfer_items")
    for _,t in executed.iterrows():
        ti = items_df[items_df["transfer_id"].astype(str)==str(t["id"])] if not items_df.empty else pd.DataFrame()
        with st.expander(f"📋 {t['number']}  ·  نُفِّذ: {t.get('executed_at','')}"):
            if not ti.empty:
                st.dataframe(
                    ti[["product_code","product_name","unit_name","requested_qty","delivered_qty"]].rename(columns={
                        "product_code":"الرمز","product_name":"المادة","unit_name":"الوحدة",
                        "requested_qty":"المطلوب","delivered_qty":"المسلَّم"
                    }),
                    use_container_width=True, hide_index=True
                )
            st.markdown(f"""
            <div style="background:#fff9e6;border:1px solid #f59e0b;border-radius:8px;padding:12px;margin-bottom:12px;">
                ⚠️ بتأكيدك تقر باستلام المواد أعلاه وتحمّل مسؤولية حفظها واستخدامها.
                <br><strong>المستلِم: {user['full_name']}</strong>
            </div>""", unsafe_allow_html=True)

            cc1,cc2 = st.columns(2)
            with cc1:
                if st.button(f"✅ تأكيد الاستلام والتوقيع", key=f"recv_{t['id']}", type="primary"):
                    now = datetime.now().strftime("%Y-%m-%d %H:%M")
                    update_row("transfers",t["id"],{
                        "status":"received","received_by":user["full_name"],"received_at":now
                    })
                    log_activity(user,"تأكيد استلام","التحويل",t["id"],t["number"])
                    st.success(f"✅ تم التأكيد بتاريخ {now}"); st.rerun()
            with cc2:
                t_dict = t.to_dict()
                t_dict["status_label"] = TRANSFER_STATUS.get(t["status"],{}).get("label","")
                items_list = ti.to_dict("records") if not ti.empty else []
                st.markdown(print_link(t_dict, items_list), unsafe_allow_html=True)


# ── كل السندات ───────────────────────────────────────────────────────
def _all(user):
    st.markdown("### 📄 جميع سندات التحويل")
    df = read_df("transfers")
    if df.empty: st.info("لا توجد سندات بعد"); return

    offices_df = read_df("offices")
    office_names = ["الكل"] + (list(offices_df[offices_df["active"].astype(str).str.strip().str.upper()=="TRUE"]["name"]) if not offices_df.empty else [])

    fc1,fc2,fc3,fc4 = st.columns(4)
    with fc1:
        status_labels = ["الكل"] + [v["label"] for v in TRANSFER_STATUS.values()]
        sf = st.selectbox("الحالة",status_labels)
    with fc2: of = st.selectbox("المصلحة", office_names)
    with fc3: pf = st.selectbox("الأولوية",["الكل","عادي","عاجل","مستعجل"])
    with fc4: search = st.text_input("🔍 بحث")

    d = df.copy()
    if sf != "الكل":
        sk = next((k for k,v in TRANSFER_STATUS.items() if v["label"]==sf),None)
        if sk: d = d[d["status"]==sk]
    if of != "الكل": d = d[d["requesting_dept"]==of]
    if pf != "الكل" and "priority" in d.columns: d = d[d["priority"]==pf]
    if search: d = d[
        d["number"].str.contains(search,case=False,na=False) |
        d["requested_by"].str.contains(search,case=False,na=False)
    ]
    d["الحالة"] = d["status"].map(lambda s:TRANSFER_STATUS.get(s,{}).get("icon","")+" "+TRANSFER_STATUS.get(s,{}).get("label",""))

    show = {"number":"السند","date":"التاريخ","requesting_dept":"المصلحة",
            "type":"النوع","priority":"الأولوية","requested_by":"طُلب بواسطة","الحالة":"الحالة"}
    avail = {k:v for k,v in show.items() if k in d.columns or k=="الحالة"}
    st.dataframe(d[[c for c in avail if c in d.columns]][::-1].rename(columns=avail),
                 use_container_width=True, hide_index=True)
    st.caption(f"عدد السندات: **{len(d)}**")

    # طباعة
    st.divider()
    if not d.empty:
        sel_num = st.selectbox("طباعة سند:", list(d["number"]))
        row = d[d["number"]==sel_num].iloc[0].to_dict()
        items_df = read_df("transfer_items")
        ti = items_df[items_df["transfer_id"].astype(str)==str(row.get("id",""))] if not items_df.empty else pd.DataFrame()
        row["status_label"] = TRANSFER_STATUS.get(row.get("status",""),{}).get("label","")
        st.markdown(print_link(row, ti.to_dict("records") if not ti.empty else []), unsafe_allow_html=True)


def _my(user):
    df = read_df("transfers")
    if df.empty: st.info("لا توجد طلبات"); return
    my = df[df["requesting_dept"]==user.get("department","")].copy()
    my["الحالة"] = my["status"].map(lambda s:TRANSFER_STATUS.get(s,{}).get("icon","")+" "+TRANSFER_STATUS.get(s,{}).get("label",""))
    cols = ["number","date","type","الحالة","notes","rejection_reason"]
    avail = [c for c in cols if c in my.columns]
    rename = {"number":"السند","date":"التاريخ","type":"النوع","notes":"ملاحظات","rejection_reason":"سبب الرفض"}
    st.dataframe(my[avail][::-1].rename(columns=rename), use_container_width=True, hide_index=True)

def _executed_log(user):
    df = read_df("transfers")
    if df.empty: st.info("لا سجل"); return
    my = df[df["executed_by"]==user["full_name"]].copy()
    my["الحالة"] = my["status"].map(lambda s:TRANSFER_STATUS.get(s,{}).get("label",""))
    cols = ["number","date","requesting_dept","الحالة","executed_at"]
    avail = [c for c in cols if c in my.columns]
    rename = {"number":"السند","date":"التاريخ","requesting_dept":"المصلحة","executed_at":"وقت التنفيذ"}
    st.dataframe(my[avail][::-1].rename(columns=rename), use_container_width=True, hide_index=True)

def _stats():
    st.markdown("### 📊 إحصاءات سندات التحويل")
    df = read_df("transfers")
    if df.empty: st.info("لا بيانات"); return
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("**الحالات**")
        st.bar_chart(df["status"].map(lambda s:TRANSFER_STATUS.get(s,{}).get("label",s)).value_counts())
    with c2:
        st.markdown("**الطلبات حسب المصلحة**")
        st.bar_chart(df["requesting_dept"].value_counts())
    if "priority" in df.columns:
        st.markdown("**الأولويات**")
        st.bar_chart(df["priority"].value_counts())
