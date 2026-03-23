# pages/users.py
import streamlit as st, pandas as pd
from datetime import datetime
from utils.sheets import read_df, append_row, update_row, gen_id, hash_pw
from config import ROLES, DEFAULT_DEPARTMENTS

def show_users():
    if not (st.session_state.user["role"]=="مدير" or st.session_state.user["role"]=="مسؤول_وسائل"):
        st.error("❌ غير مصرح"); return
    st.markdown("## 👥 إدارة المستخدمين والحسابات")
    tabs=st.tabs(["📋 المستخدمون","➕ مستخدم جديد","🔒 تغيير كلمة مرور","📊 نشاط المستخدمين"])
    with tabs[0]: _list()
    with tabs[1]: _add()
    with tabs[2]: _change_pw()
    with tabs[3]: _activity()

def _list():
    df=read_df("users")
    if df.empty: st.info("لا يوجد مستخدمون"); return
    offices_df=read_df("offices")
    show_inactive=st.checkbox("عرض الحسابات المعطلة")
    d=df.copy() if show_inactive else df[df["active"].astype(str)=="True"]
    d["الدور"]=d["role"].map(lambda r:ROLES.get(r,{}).get("icon","")+" "+ROLES.get(r,{}).get("label",r))
    show=["username","full_name","title","الدور","department","phone","email","last_login","created_at"]
    avail=[c for c in show if c in d.columns]
    rename={"username":"اسم الدخول","full_name":"الاسم الكامل","title":"الصفة",
            "department":"المصلحة","phone":"الهاتف","email":"البريد",
            "last_login":"آخر دخول","created_at":"تاريخ الإنشاء"}
    st.dataframe(d[avail].rename(columns=rename),use_container_width=True,hide_index=True)
    st.caption(f"إجمالي: **{len(d)}** مستخدم")

def _add():
    st.markdown("### ➕ إضافة مستخدم جديد")
    offices_df=read_df("offices")
    office_names=list(offices_df[offices_df["active"].astype(str)=="True"]["name"]) if not offices_df.empty else []
    with st.form("add_user",clear_on_submit=True):
        uc1,uc2=st.columns(2)
        with uc1:
            full_name=st.text_input("الاسم الكامل ★")
            title    =st.text_input("الصفة / المنصب",placeholder="رئيس مصلحة التدريس")
            username =st.text_input("اسم الدخول ★")
            password =st.text_input("كلمة المرور ★ (6+ أحرف)",type="password")
        with uc2:
            role      =st.selectbox("الدور ★",list(ROLES.keys()),format_func=lambda r:ROLES[r]["label"])
            department=st.selectbox("المصلحة ★",DEFAULT_DEPARTMENTS)
            office    =st.selectbox("المكتب",["لا يوجد"]+office_names)
            phone     =st.text_input("الهاتف")
            email     =st.text_input("البريد الإلكتروني")
        if st.form_submit_button("✅ إنشاء الحساب",type="primary",use_container_width=True):
            errs=[]
            if not full_name.strip(): errs.append("الاسم مطلوب")
            if not username.strip():  errs.append("اسم الدخول مطلوب")
            if not password or len(password)<6: errs.append("كلمة المرور: 6 أحرف على الأقل")
            existing=read_df("users")
            if not existing.empty and username.strip() in list(existing.get("username",[])):
                errs.append("اسم الدخول مستخدم")
            if errs:
                for e in errs: st.error(f"❌ {e}")
            else:
                office_id=""
                if not offices_df.empty and office!="لا يوجد":
                    r=offices_df[offices_df["name"]==office]
                    if not r.empty: office_id=str(r.iloc[0]["id"])
                append_row("users",{
                    "id":gen_id(),"username":username.strip(),
                    "password_hash":hash_pw(password),"full_name":full_name.strip(),
                    "title":title.strip(),"role":role,"department":department,
                    "office_id":office_id,"phone":phone.strip(),"email":email.strip(),
                    "active":"True","last_login":"",
                    "created_at":datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "created_by":st.session_state.user["full_name"],
                })
                st.success(f"✅ حساب **{full_name}** | دور: {ROLES[role]['label']} | دخول: `{username}`")

def _change_pw():
    st.markdown("### 🔒 تغيير كلمة مرور")
    df=read_df("users")
    if df.empty: return
    active=df[df["active"].astype(str)=="True"]
    sel=st.selectbox("المستخدم",list(active["full_name"]+" ("+active["username"]+")"))
    username=sel.split("(")[-1].rstrip(")")
    new_pw=st.text_input("كلمة المرور الجديدة",type="password")
    confirm=st.text_input("تأكيد كلمة المرور",type="password")
    if st.button("تحديث",type="primary"):
        if len(new_pw)<6: st.error("6 أحرف على الأقل")
        elif new_pw!=confirm: st.error("كلمتا المرور غير متطابقتين")
        else:
            uid=active[active["username"]==username].iloc[0]["id"]
            update_row("users",uid,{"password_hash":hash_pw(new_pw)})
            st.success(f"✅ تم تحديث كلمة مرور {username}")

def _activity():
    df=read_df("activity_log")
    if df.empty: st.info("لا سجل نشاط"); return
    search=st.text_input("🔍 بحث")
    d=df.copy()
    if search:
        d=d[d["user_name"].str.contains(search,case=False,na=False)|
            d["action"].str.contains(search,case=False,na=False)]
    show=["datetime","user_name","action","module","reference_number","details"]
    avail=[c for c in show if c in d.columns]
    rename={"datetime":"التوقيت","user_name":"المستخدم","action":"الإجراء",
            "module":"الوحدة","reference_number":"المرجع","details":"التفاصيل"}
    st.dataframe(d[avail][::-1].rename(columns=rename),use_container_width=True,hide_index=True)
