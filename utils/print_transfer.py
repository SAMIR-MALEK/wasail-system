# utils/print_transfer.py
from config import FACULTY_NAME, UNIVERSITY_NAME, TRANSFER_STATUS
import base64

def build_transfer_html(transfer: dict, items: list) -> str:
    status_label = TRANSFER_STATUS.get(transfer.get("status",""),{}).get("label","")

    rows_html = ""
    for i, item in enumerate(items, 1):
        delivered = item.get("delivered_qty", item.get("requested_qty",""))
        rows_html += f"""<tr>
            <td style="text-align:center">{i}</td>
            <td>{item.get('product_code','')}</td>
            <td style="text-align:right">{item.get('product_name','')}</td>
            <td style="text-align:center">{item.get('unit_name','')}</td>
            <td style="text-align:center">{item.get('requested_qty','')}</td>
            <td style="text-align:center;font-weight:700;color:#1a1a2e">{delivered}</td>
        </tr>"""
    while len(items) + rows_html.count("<tr>") < 10:
        rows_html += "<tr><td></td><td></td><td>&nbsp;</td><td></td><td></td><td></td></tr>"

    html = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head><meta charset="UTF-8">
<title>سند التحويل {transfer.get('number','')}</title>
<style>
@page{{size:A4;margin:15mm;}}
*{{box-sizing:border-box;margin:0;padding:0;font-family:Tahoma,Arial,sans-serif;}}
body{{font-size:11px;color:#111;background:white;direction:rtl;}}
.header{{display:flex;justify-content:space-between;align-items:flex-start;
         border-bottom:3px double #1a1a2e;padding-bottom:10px;margin-bottom:10px;}}
.hc{{text-align:center;flex:1;line-height:1.8;font-size:10.5px;}}
.hc b{{font-size:11.5px;}}
.logo{{width:70px;height:70px;border:2px dashed #bbb;border-radius:50%;
       display:flex;align-items:center;justify-content:center;
       font-size:9px;color:#aaa;text-align:center;flex-shrink:0;}}
.title{{text-align:center;margin:10px 0 12px;}}
.title h1{{font-size:17px;font-weight:900;border:2px solid #1a1a2e;
           display:inline-block;padding:5px 30px;border-radius:3px;}}
.title p{{font-size:9px;color:#666;margin-top:3px;letter-spacing:2px;}}
.meta{{width:100%;border-collapse:collapse;margin-bottom:12px;font-size:10.5px;}}
.meta td{{padding:5px 8px;border:1px solid #ccc;}}
.meta .lbl{{background:#f0f4ff;font-weight:700;width:20%;white-space:nowrap;}}
.sec-title{{font-size:11px;font-weight:800;border-right:4px solid #e94560;
            padding-right:8px;margin-bottom:5px;}}
.items{{width:100%;border-collapse:collapse;font-size:10.5px;margin-bottom:12px;}}
.items th{{background:#1a1a2e;color:white;padding:6px 5px;text-align:center;border:1px solid #1a1a2e;}}
.items td{{padding:5px;border:1px solid #ccc;height:24px;}}
.items tr:nth-child(even) td{{background:#f8f9ff;}}
.sig-wrap{{border:1px solid #ccc;border-radius:4px;overflow:hidden;}}
.sig-hd{{background:#1a1a2e;color:white;text-align:center;padding:5px;font-size:10.5px;font-weight:700;}}
.sig-body{{display:flex;}}
.sig-box{{flex:1;padding:12px;border-left:1px solid #ddd;text-align:center;}}
.sig-box:last-child{{border-left:none;}}
.sig-role{{font-weight:800;font-size:10.5px;color:#1a1a2e;}}
.sig-name{{font-size:10px;color:#555;margin:3px 0 20px;}}
.sig-line{{border-top:1px solid #888;width:80%;margin:0 auto;}}
.sig-date{{font-size:9px;color:#888;margin-top:4px;}}
.footer{{margin-top:12px;border-top:1px solid #eee;padding-top:5px;
         text-align:center;font-size:8px;color:#aaa;}}
.print-btn{{display:block;margin:16px auto;padding:9px 30px;
            background:#1a1a2e;color:white;border:none;border-radius:6px;
            font-size:13px;cursor:pointer;font-family:inherit;}}
@media print{{.no-print{{display:none!important;}}}}
</style></head>
<body>
<button class="print-btn no-print" onclick="window.print()">🖨️ طباعة السند</button>
<div class="header">
  <div class="logo">شعار<br>الكلية</div>
  <div class="hc">
    الجمهورية الجزائرية الديمقراطية الشعبية<br>
    وزارة التعليم العالي والبحث العلمي<br>
    <b>{UNIVERSITY_NAME}</b><br>
    <b>{FACULTY_NAME}</b><br>
    <small style="color:#555">Université Mohamed Bachir El Ibrahimi — BBA &nbsp;|&nbsp; Faculté de Droit et des Sciences Politiques</small>
  </div>
  <div style="width:70px"></div>
</div>
<div class="title"><h1>سند التحويل</h1><p>BON DE TRANSFERT DE MATÉRIELS</p></div>
<table class="meta">
  <tr>
    <td class="lbl">رقم السند</td><td><b>{transfer.get('number','')}</b></td>
    <td class="lbl">التاريخ</td><td>{transfer.get('date','')}</td>
  </tr>
  <tr>
    <td class="lbl">المصلحة الطالبة</td><td>{transfer.get('requesting_dept','')}</td>
    <td class="lbl">رمز المكتب</td><td>{transfer.get('requesting_office_code','')}</td>
  </tr>
  <tr>
    <td class="lbl">طُلب بواسطة</td><td>{transfer.get('requested_by','')}</td>
    <td class="lbl">الحالة</td><td><b>{status_label}</b></td>
  </tr>
  <tr>
    <td class="lbl">نوع التحويل</td><td>{transfer.get('type','')}</td>
    <td class="lbl">ملاحظات</td><td>{transfer.get('notes','')}</td>
  </tr>
</table>
<div class="sec-title">تفاصيل المواد المحوَّلة / Désignation des Matériels</div>
<table class="items">
  <thead><tr>
    <th style="width:5%">#</th>
    <th style="width:12%">الرمز</th>
    <th style="width:38%;text-align:right">التسمية / Désignation</th>
    <th style="width:11%">الوحدة</th>
    <th style="width:14%">الكمية المطلوبة</th>
    <th style="width:14%">الكمية المسلَّمة</th>
  </tr></thead>
  <tbody>{rows_html}</tbody>
</table>
<div class="sig-wrap">
  <div class="sig-hd">التوقيعات — Signatures</div>
  <div class="sig-body">
    <div class="sig-box">
      <div class="sig-role">مسؤول مصلحة الوسائل</div>
      <div class="sig-name">{transfer.get('approved_by','')}</div>
      <div class="sig-line"></div>
      <div class="sig-date">التاريخ: {transfer.get('approved_at','.....................')}</div>
    </div>
    <div class="sig-box">
      <div class="sig-role">أمين المخزن</div>
      <div class="sig-name">{transfer.get('executed_by','')}</div>
      <div class="sig-line"></div>
      <div class="sig-date">التاريخ: {transfer.get('executed_at','.....................')}</div>
    </div>
    <div class="sig-box">
      <div class="sig-role" style="color:#e94560">رئيس {transfer.get('requesting_dept','المصلحة')}</div>
      <div class="sig-name" style="font-weight:800;color:#1a1a2e">{transfer.get('received_by','...................................')}</div>
      <div class="sig-line"></div>
      <div class="sig-date">التاريخ: {transfer.get('received_at','.....................')}</div>
    </div>
  </div>
</div>
<div class="footer">
  نظام الوسائل العامة — {FACULTY_NAME} — {UNIVERSITY_NAME} | السند: {transfer.get('number','')}
</div>
<button class="print-btn no-print" onclick="window.print()">🖨️ طباعة السند</button>
</body></html>"""
    return html

def print_link(transfer: dict, items: list) -> str:
    html    = build_transfer_html(transfer, items)
    encoded = base64.b64encode(html.encode("utf-8")).decode()
    num     = transfer.get("number","")
    return f"""
    <a href="data:text/html;charset=utf-8;base64,{encoded}" target="_blank"
       style="display:inline-flex;align-items:center;gap:8px;padding:9px 20px;
              background:linear-gradient(135deg,#1a1a2e,#0f3460);color:white;
              border-radius:8px;text-decoration:none;font-size:.88rem;font-weight:600;">
        🖨️ فتح سند الطباعة — {num}
    </a>
    <small style="display:block;color:#888;margin-top:4px;font-size:.74rem;">
        يفتح في تبويب جديد ← Ctrl+P للطباعة
    </small>"""
