import streamlit as st
import random
import datetime
import pandas as pd  
from collections import Counter
import json
import os
import io

st.set_page_config(page_title="🏥 全院智能排班系統 (HIS)", page_icon="🏥", layout="wide")

# ==========================================
# 🌟 全院單位清單
# ==========================================
全院單位清單 = [
    "藥劑科", "血液透析組", "部份醫技組", "放射科", "醫師暨值班",
    "門診護理", "櫃台", 
    "加護病房(護理)", "加護病房(照服)",
    "5樓病房(護理)", "5樓病房(照服)", 
    "6樓呼吸病房(護理)", "6樓呼吸病房(照服)", 
    "7樓病房(護理)", "7樓病房(照服)", 
    "8樓病房(護理)", "8樓病房(照服)", 
    "9樓呼吸病房(護理)", "9樓呼吸病房(照服)", 
    "10樓病房(護理)", "10樓病房(照服)", 
    "行政部"
]
休假類別 = ["預約排休(Wish OFF)", "特休", "事假", "病假", "婚假", "產假/陪產假", "喪假", "公假", "其他"]
部門清單 = ["護理部", "醫療部", "行政部", "醫技部"] 

# ==========================================
# 🌟 0. 中央資料庫 (Database) 
# ==========================================
DB_FILE = "hospital_db.json" 

def 初始化資料庫():
    預設班別 = [
        {"代碼": "M0", "名稱": "M0班(06-14)", "工時": 8, "津貼(元)": 0, "文字顏色": "#0066cc"},
        {"代碼": "D", "名稱": "早班(08-16)", "工時": 8, "津貼(元)": 0, "文字顏色": "#0066cc"},
        {"代碼": "E", "名稱": "小夜", "工時": 8, "津貼(元)": 500, "文字顏色": "#009900"},
        {"代碼": "N", "名稱": "大夜", "工時": 8, "津貼(元)": 800, "文字顏色": "#800080"},
        {"代碼": "12D", "名稱": "白長班", "工時": 12, "津貼(元)": 0, "文字顏色": "#0066cc"},
        {"代碼": "12N", "名稱": "夜長班", "工時": 12, "津貼(元)": 800, "文字顏色": "#800080"}
    ]

    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for 單位 in 全院單位清單:
                if 單位 not in data['當期班表資料']: data['當期班表資料'][單位] = None
                if 單位 not in data['橫式班表資料']: data['橫式班表資料'][單位] = None
                
                if data['當期班表資料'].get(單位) is not None: data['當期班表資料'][單位] = pd.DataFrame(data['當期班表資料'][單位])
                if data['橫式班表資料'].get(單位) is not None: data['橫式班表資料'][單位] = pd.DataFrame(data['橫式班表資料'][單位])
            
            if '所屬部門' not in data: data['所屬部門'] = {人: '護理部' for 人 in data['員工名單']}
            if '班別設定' not in data: data['班別設定'] = 預設班別
            if '請購與修繕紀錄' not in data: data['請購與修繕紀錄'] = []
            return data
    else:
        預設員工 = ['佳駿', '佩君', '欣怡', '朝元', '佩玲', '江慧敏', '黃秀娥', '張九樓', '李九樓']
        預設資料 = {
            '員工名單': 預設員工.copy(),
            '所屬部門': {人: '護理部' for 人 in 預設員工}, 
            '所屬單位': {
                '佳駿': '10樓病房(護理)', '佩君': '10樓病房(護理)', '欣怡': '10樓病房(護理)', 
                '朝元': '10樓病房(護理)', '佩玲': '10樓病房(護理)', '江慧敏': '10樓病房(護理)', 
                '黃秀娥': '10樓病房(護理)', '張九樓': '9樓呼吸病房(護理)', '李九樓': '9樓呼吸病房(護理)'
            },
            '年資_年數': {'佳駿': 5.0, '佩君': 3.0, '欣怡': 1.0, '朝元': 0.5, '佩玲': 10.0, '江慧敏': 0.2, '黃秀娥': 7.0, '張九樓': 4.0, '李九樓': 1.0},
            '固定休假': {'佳駿': 1, '佩君': 3, '欣怡': 5, '朝元': 7, '佩玲': 2, '江慧敏': 4, '黃秀娥': 6, '張九樓': 1, '李九樓': 2},
            '員工編號': {'佳駿': 'N001', '佩君': 'N002', '欣怡': 'N003', '朝元': 'N004', '佩玲': 'N005', '江慧敏': 'N006', '黃秀娥': 'N007', '張九樓': 'N008', '李九樓': 'N009'},
            '臨床職級': {'佳駿': 'N3', '佩君': 'N1', '欣怡': 'N', '朝元': 'N', '佩玲': 'N4', '江慧敏': 'N', '黃秀娥': 'N2', '張九樓': 'N2', '李九樓': 'N'},
            '免夜班': {人: False for 人 in 預設員工},
            '可上長班': {人: True for 人 in 預設員工},
            '請假紀錄': {人: {} for 人 in 預設員工},
            '當期班表資料': {單位: None for 單位 in 全院單位清單},
            '橫式班表資料': {單位: None for 單位 in 全院單位清單},
            '歷史班表': {},
            '班別設定': 預設班別,
            '請購與修繕紀錄': [] 
        }
        存檔專用 = 預設資料.copy()
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(存檔專用, f, ensure_ascii=False, indent=4)
        return 預設資料

if 'db' not in st.session_state:
    st.session_state['db'] = 初始化資料庫()
db = st.session_state['db']

def 儲存資料庫(data):
    存檔專用 = data.copy()
    存檔專用['當期班表資料'] = {單位: (df.to_dict('records') if isinstance(df, pd.DataFrame) else None) for 單位, df in 存檔專用['當期班表資料'].items()}
    存檔專用['橫式班表資料'] = {單位: (df.to_dict('records') if isinstance(df, pd.DataFrame) else None) for 單位, df in 存檔專用['橫式班表資料'].items()}
    for 月份, 單位字典 in 存檔專用['歷史班表'].items():
        存檔專用['歷史班表'][月份] = {單位: (df.to_dict('records') if isinstance(df, pd.DataFrame) else df) for 單位, df in 單位字典.items()}
        
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(存檔專用, f, ensure_ascii=False, indent=4)
    st.session_state['db'] = data

def 計算特休小時(年數):
    if 年數 >= 10: return min(15 + int(年數 - 9), 30) * 8
    elif 年數 >= 5: return 15 * 8
    elif 年數 >= 3: return 14 * 8
    elif 年數 >= 2: return 10 * 8
    elif 年數 >= 1: return 7 * 8
    elif 年數 >= 0.5: return 3 * 8
    return 0

def 取得合法顏色字串(輸入值):
    if pd.isna(輸入值) or 輸入值 is None: return "#000000"
    字串化 = str(輸入值).strip()
    if not 字串化 or 字串化.lower() in ['nan', 'none', 'null']: return "#000000"
    return 字串化

def 標示色彩(值):
    if isinstance(值, str):
        if 值 in ['OFF', 'Leave', 'Wish']: return 'color: red; font-weight: bold;'
        elif '衝突' in 值: return 'background-color: red; color: white; font-weight: bold;'
        
        for 班 in db.get('班別設定', []):
            if 值 == 班.get('代碼'):
                顏色 = 取得合法顏色字串(班.get('文字顏色'))
                return f"color: {顏色}; font-weight: bold;"
    return ''

def 匯出彩色Excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='單位班表')
        workbook = writer.book
        worksheet = writer.sheets['單位班表']

        格式字典 = {}
        for 班 in db.get('班別設定', []):
            代碼 = 班.get('代碼')
            if 代碼:
                顏色 = 取得合法顏色字串(班.get('文字顏色'))
                格式字典[代碼] = workbook.add_format({'font_color': 顏色, 'bold': True})
            
        fmt_off = workbook.add_format({'font_color': 'red', 'bold': True})
        fmt_alert = workbook.add_format({'bg_color': 'red', 'font_color': 'white', 'bold': True})

        for row in range(len(df)):
            for col in range(len(df.columns)):
                val = str(df.iloc[row, col])
                if val in ['OFF', 'Leave', 'Wish']: worksheet.write(row + 1, col, val, fmt_off)
                elif '衝突' in val: worksheet.write(row + 1, col, val, fmt_alert)
                elif val in 格式字典: worksheet.write(row + 1, col, val, 格式字典[val])
                else: worksheet.write(row + 1, col, val)
    return output.getvalue()

# ==========================================
# 🌟 1. 登入系統
# ==========================================
if '登入狀態' not in st.session_state: st.session_state['登入狀態'] = False
if '當前使用者' not in st.session_state: st.session_state['當前使用者'] = ""
if '當前權限' not in st.session_state: st.session_state['當前權限'] = ""

if not st.session_state['登入狀態']:
    st.title("🏥 全院智能排班系統 (HIS) - 登入")
    with st.container(border=True):
        st.subheader("🔐 系統登入")
        帳號 = st.text_input("👤 帳號 / 員工姓名")
        密碼 = st.text_input("🔑 密碼", type="password")
        if st.button("登入系統", type="primary", width="stretch"):
            if 帳號 == 'admin' and 密碼 == 'admin123':
                st.session_state['登入狀態'] = True; st.session_state['當前使用者'] = "系統管理員 (全院)"; st.session_state['當前權限'] = "管理員"; st.rerun()
            elif 帳號 in db['員工名單'] and 密碼 == '1234':
                st.session_state['登入狀態'] = True; st.session_state['當前使用者'] = 帳號; st.session_state['當前權限'] = "一般使用者"; st.rerun()
            else: st.error("❌ 帳號或密碼錯誤！")
    st.stop() 

# ==========================================
# 🌟 2. 側邊欄與切換器
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2966/2966327.png", width=80) 
    st.markdown(f"**👤 登入者：** {st.session_state['當前使用者']}")
    
    if st.session_state['當前權限'] == "管理員":
        st.markdown("---")
        當前單位 = st.selectbox("🏢 切換目前管理單位：", 全院單位清單, index=19) 
        st.info(f"👉 系統已切換至：**{當前單位}**")
    else:
        當前單位 = db['所屬單位'].get(st.session_state['當前使用者'], "未分發")
        st.markdown(f"**🏢 所屬單位：** {當前單位}")
        
    if st.button("安全登出", width="stretch"): 
        st.session_state['登入狀態'] = False; st.session_state['當前使用者'] = ""; st.rerun()
        
    st.divider()
    if st.session_state['當前權限'] == "管理員": 
        選單選項 = ["🤖 自動排班與總表", "👥 員工資料與請假", "🗂️ 歷史班表封存庫", "⚙️ 全院人事總表與後臺", "🛠️ 單位請購與修繕"]
    else: 
        選單選項 = ["📋 單位班表查詢", "📝 假單與【排班許願池】", "🛠️ 單位請購與修繕"]
    頁面 = st.radio("請選擇功能：", 選單選項)

單位名單 = [人 for 人 in db['員工名單'] if db['所屬單位'].get(人) == 當前單位]
年資 = {人: ('資深' if 年數 >= 3.0 else '資淺') for 人, 年數 in db['年資_年數'].items() if 人 in 單位名單}

# ==========================================
# 🌟 3. 一般使用者專區 
# ==========================================
if 頁面 == "📝 假單與【排班許願池】":
    st.title(f"📝 {當前單位} - {st.session_state['當前使用者']} 申請區")
    我 = st.session_state['當前使用者']
    
    with st.container(border=True):
        col_a, col_b, col_c = st.columns(3)
        假別清單 = ["預約排休(Wish OFF)", "⭐ 預約上早班(Wish D)", "⭐ 預約上小夜(Wish E)", "⭐ 預約上大夜(Wish N)", "特休", "事假", "病假", "婚假", "產假/陪產假", "喪假", "公假", "其他"]
        with col_a: 假別 = st.selectbox("請選擇需求：", 假別清單)
        with col_b: 請假日期 = st.date_input("選擇日期：", datetime.date.today())
        代理人選項 = ["無"] + [人 for 人 in 單位名單 if 人 != 我]
        with col_c: 代理人 = st.selectbox("協調代班人 (限同單位)：", 代理人選項)
        
        if st.button("送出申請", type="primary"):
            日期字串 = 請假日期.strftime("%Y-%m-%d") 
            if 日期字串 not in db['請假紀錄'].get(我, {}):
                if 我 not in db['請假紀錄']: db['請假紀錄'][我] = {}
                db['請假紀錄'][我][日期字串] = {"假別": 假別, "代理人": 代理人}
                儲存資料庫(db); st.success(f"✅ 已成功送出 {日期字串} 申請！")
            else: st.warning("⚠️ 該日已送出過申請！")
                
    st.divider()
    st.subheader("📋 我的申請紀錄")
    紀錄表 = [{"完整日期": d, "項目": info["假別"], "代班人": info["代理人"]} for d, info in db['請假紀錄'].get(我, {}).items()]
    if 紀錄表: st.dataframe(pd.DataFrame(紀錄表).sort_values(by="完整日期"), hide_index=True, width="stretch")

elif 頁面 == "📋 單位班表查詢":
    st.title(f"📋 {當前單位} - 當期班表查詢")
    if db['橫式班表資料'].get(當前單位) is not None:
        彩色版班表 = db['橫式班表資料'][當前單位].style.map(標示色彩)
        st.dataframe(彩色版班表, hide_index=True, width="stretch")
        excel_data = 匯出彩色Excel(db['橫式班表資料'][當前單位])
        st.download_button("📥 下載單位班表 (彩色 Excel)", data=excel_data, file_name=f"{當前單位}_班表.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")
    else: st.info(f"⚠️ 尚未發布【{當前單位}】的班表。")

# ==========================================
# 🌟 4. 管理員專區 
# ==========================================
elif 頁面 == "👥 員工資料與請假":
    st.title(f"👥 【{當前單位}】 人力與請假管理")
    
    with st.expander(f"➕ 新增員工至【{當前單位}】", expanded=False):
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1: 新姓名 = st.text_input("員工姓名")
        with col2: 新部門 = st.selectbox("所屬部門", 部門清單) 
        with col3: 新編號 = st.text_input("員工編號", value="N")
        with col4: 新職級 = st.selectbox("職級/職稱", ["N", "N1", "N2", "N3", "N4", "NP", "RN", "醫師", "行政", "技術員"])
        with col5: 新年資 = st.number_input("到職年資(年)", min_value=0.0, step=0.5)

        if st.button("📥 確認新增人員", type="primary"):
            if 新姓名 and 新姓名 not in db['員工名單']:
                db['員工名單'].append(新姓名); db['所屬部門'][新姓名] = 新部門; db['所屬單位'][新姓名] = 當前單位
                db['員工編號'][新姓名] = 新編號; db['臨床職級'][新姓名] = 新職級; db['年資_年數'][新姓名] = 新年資
                db['固定休假'][新姓名] = 1; db['免夜班'][新姓名] = False; db['可上長班'][新姓名] = True; db['請假紀錄'][新姓名] = {}
                儲存資料庫(db); st.success(f"✅ 【{新姓名}】 已成功加入 {當前單位}！"); st.rerun()
            elif 新姓名 in db['員工名單']: st.error("⚠️ 此姓名已存在！")

    with st.container(border=True):
        st.subheader("⚙️ 單位人員防護網與【調職】設定")
        大表資料 = [{
            "員工編號": db['員工編號'].get(人, ""), "員工姓名": 人, 
            "所屬部門": db['所屬部門'].get(人, "護理部"), "所屬單位": db['所屬單位'].get(人, ""), 
            "職級": db['臨床職級'].get(人, ""), "到職年資(年)": db['年資_年數'].get(人, 0.0),
            "固定休假(星期)": db['固定休假'].get(人, 1), "免夜班": db['免夜班'].get(人, False), "可上長班": db['可上長班'].get(人, True)
        } for 人 in 單位名單]
        
        if 大表資料:
            edited_大表 = st.data_editor(pd.DataFrame(大表資料), disabled=["員工姓名"], hide_index=True, width="stretch", 
                column_config={"所屬部門": st.column_config.SelectboxColumn("所屬部門", options=部門清單), "所屬單位": st.column_config.SelectboxColumn("所屬單位 (調職)", options=全院單位清單), "免夜班": st.column_config.CheckboxColumn("懷孕/免夜班"), "可上長班": st.column_config.CheckboxColumn("可上長班(12H)")})
            需要重整 = False
            for index, row in edited_大表.iterrows():
                人 = row["員工姓名"]; 舊單位 = db['所屬單位'].get(人); 新單位 = str(row["所屬單位"])
                db['員工編號'][人] = str(row["員工編號"]); db['所屬部門'][人] = str(row["所屬部門"]); db['所屬單位'][人] = 新單位
                db['臨床職級'][人] = str(row["職級"]); db['年資_年數'][人] = float(row["到職年資(年)"]); db['固定休假'][人] = int(row["固定休假(星期)"]); db['免夜班'][人] = bool(row["免夜班"]); db['可上長班'][人] = bool(row["可上長班"])
                if 舊單位 != 新單位: 需要重整 = True
            儲存資料庫(db)
            if 需要重整: st.success("🔄 人員調職已生效！畫面即將更新..."); st.rerun()
            
    st.divider()
    左邊區塊, 右邊區塊 = st.columns(2)
    with 左邊區塊:
        with st.container(border=True):
            st.subheader("📊 特休時數追蹤表")
            特休統計箱 = []
            for 人 in 單位名單:
                總特休 = 計算特休小時(db['年資_年數'].get(人, 0))
                已用特休 = sum(1 for 紀錄 in db['請假紀錄'].get(人, {}).values() if 紀錄.get("假別") == "特休")
                特休統計箱.append({"員工姓名": 人, "💎 總特休(H)": 總特休, "📉 已用特休": 已用特休 * 8, "✨ 剩餘特休": 總特休 - 已用特休 * 8})
            if 特休統計箱: st.dataframe(pd.DataFrame(特休統計箱), hide_index=True, width="stretch")

    with 右邊區塊:
        with st.container(border=True): 
            st.subheader("📋 單位請假與許願清單")
            所有假單 = [{"員工姓名": 人, "完整日期": 日期, "申請項目": 紀錄["假別"], "代班人": 紀錄["代理人"]} for 人 in 單位名單 for 日期, 紀錄 in db['請假紀錄'].get(人, {}).items()]
            if 所有假單: 
                df_所有假單 = pd.DataFrame(所有假單).sort_values(by="完整日期")
                edited_假單 = st.data_editor(df_所有假單, disabled=["員工姓名", "完整日期", "申請項目"], column_config={"代班人": st.column_config.SelectboxColumn("代班人", options=["無"]+單位名單)}, hide_index=True, width="stretch")
                for index, row in edited_假單.iterrows(): db['請假紀錄'][row["員工姓名"]][row["完整日期"]]["代理人"] = row["代班人"]
                儲存資料庫(db)

# ==========================================
# 🌟 5. 自動排班與總表 
# ==========================================
elif 頁面 == "🤖 自動排班與總表":
    st.title(f"🏥 【{當前單位}】 自動排班與總表 🌟")
    
    if not 單位名單:
        st.error(f"⚠️ 無法排班：【{當前單位}】 目前沒有建置任何員工。請先至「員工資料與請假」新增人員！")
        st.stop()
        
    with st.container(border=True):
        st.subheader("⚙️ 產生新班表")
        col1, col2 = st.columns([1, 2])
        with col1:
            起始日期 = st.date_input("📅 排班【起始日】：", datetime.date.today())
            排班模式 = st.radio("⚙️ 模式：", ["🤖 智慧全自動排班 (優先滿足許願池)", "📝 建立空白班表"])
        with col2:
            st.info(f"📌 排班區間：**{起始日期}** 至 **{起始日期 + datetime.timedelta(days=27)}**")
            if st.button(f"💉 產生 {當前單位} 28 天班表", width="stretch", type="primary"):
                昨天中班人員 = None; 昨天晚班人員 = None 
                連上天數 = {人: 0 for 人 in 單位名單} 
                臨時班表箱子 = []
                星期對照表 = ["一", "二", "三", "四", "五", "六", "日"]
                全院設定班別 = db.get('班別設定', [])
                
                for i in range(28): 
                    當天日期 = 起始日期 + datetime.timedelta(days=i)
                    比對用日期 = 當天日期.strftime("%Y-%m-%d")  
                    星期幾 = 當天日期.isoweekday()
                    經典日期標題 = f"{當天日期.strftime('%d')}({星期對照表[星期幾 - 1]})"
                    
                    每日資料 = {"完整日期": 比對用日期, "日期": 經典日期標題}
                    for 班 in 全院設定班別: 
                        名稱 = 班['名稱']
                        if 名稱 not in 每日資料: 
                            每日資料[名稱] = "無"
                    
                    if "自動排班" in 排班模式:
                        今天可以上班的人 = [人 for 人 in 單位名單 if db['固定休假'].get(人) != 星期幾 and db['請假紀錄'].get(人, {}).get(比對用日期, {}).get("假別") not in 休假類別]
                        快過勞名單 = [人 for 人 in 今天可以上班的人 if 連上天數[人] >= 5]
                        for 人 in 快過勞名單: 今天可以上班的人.remove(人) 
                        
                        D願望 = [人 for 人 in 今天可以上班的人 if db['請假紀錄'].get(人, {}).get(比對用日期, {}).get("假別") == "⭐ 預約上早班(Wish D)"]
                        E願望 = [人 for 人 in 今天可以上班的人 if db['請假紀錄'].get(人, {}).get(比對用日期, {}).get("假別") == "⭐ 預約上小夜(Wish E)"]
                        N願望 = [人 for 人 in 今天可以上班的人 if db['請假紀錄'].get(人, {}).get(比對用日期, {}).get("假別") == "⭐ 預約上大夜(Wish N)"]
                        
                        if len(今天可以上班的人) >= 3:
                            早班候選人 = [人 for 人 in 今天可以上班的人 if 人 not in [昨天中班人員, 昨天晚班人員]]
                            D願望合格 = [人 for 人 in D願望 if 人 in 早班候選人]
                            if D願望合格: 今日早班 = random.choice(D願望合格) 
                            elif 早班候選人: 今日早班 = random.choice(早班候選人)
                            else: 今日早班 = random.choice(今天可以上班的人) if 今天可以上班的人 else "無"
                            剩下的 = 今天可以上班的人.copy(); 剩下的.remove(今日早班) if 今日早班 in 剩下的 else None
                            
                            大夜合格者 = [人 for 人 in 剩下的 if not db['免夜班'].get(人, False)]
                            N願望合格 = [人 for 人 in N願望 if 人 in 大夜合格者]
                            if N願望合格: 今日晚班 = random.choice(N願望合格) 
                            else: 今日晚班 = random.choice(大夜合格者) if 大夜合格者 else "無"
                            if 今日晚班 != "無": 剩下的.remove(今日晚班)
                            
                            小夜合格者 = [人 for 人 in 剩下的 if not db['免夜班'].get(人, False)]
                            E願望合格 = [人 for 人 in E願望 if 人 in 小夜合格者]
                            if E願望合格: 今日中班 = random.choice(E願望合格) 
                            else: 今日中班 = random.choice(小夜合格者) if 小夜合格者 else "無"
                            
                            for 人 in 單位名單:
                                if 人 in [今日早班, 今日中班, 今日晚班]: 連上天數[人] += 1
                                else: 連上天數[人] = 0 
                            昨天中班人員 = 今日中班; 昨天晚班人員 = 今日晚班
                            
                            for 班 in 全院設定班別:
                                if 班['代碼'] == 'D': 每日資料[班['名稱']] = 今日早班
                                elif 班['代碼'] == 'E': 每日資料[班['名稱']] = 今日中班
                                elif 班['代碼'] == 'N': 每日資料[班['名稱']] = 今日晚班
                    
                    臨時班表箱子.append(每日資料)

                db['當期班表資料'][當前單位] = pd.DataFrame(臨時班表箱子)
                儲存資料庫(db); st.rerun() 

    if db['當期班表資料'].get(當前單位) is not None:
        st.divider()
        st.subheader("✏️ 手動微調直式班表")

        當前班表DF = db['當期班表資料'][當前單位]
        原始設定班別名稱 = [班['名稱'] for 班 in db.get('班別設定', [])]
        唯一的班別名稱 = []
        for name in 原始設定班別名稱:
            if name not in 唯一的班別名稱: 唯一的班別名稱.append(name)

        for 名稱 in 唯一的班別名稱:
            if 名稱 not in 當前班表DF.columns: 當前班表DF[名稱] = "無"

        保留的欄位 = ["完整日期", "日期"] + 唯一的班別名稱
        多餘的欄位 = [col for col in 當前班表DF.columns if col not in 保留的欄位]
        if 多餘的欄位: 當前班表DF = 當前班表DF.drop(columns=多餘的欄位)

        當前班表DF = 當前班表DF[保留的欄位]
        db['當期班表資料'][當前單位] = 當前班表DF

        選項 = ["無"] + 單位名單
        動態欄位設定 = {"完整日期": None}
        for 名稱 in 唯一的班別名稱: 動態欄位設定[名稱] = st.column_config.SelectboxColumn(名稱, options=選項)
            
        edited_df = st.data_editor(當前班表DF, column_config=動態欄位設定, width="stretch", hide_index=True)
        db['當期班表資料'][當前單位] = edited_df

        st.divider()
        
        with st.expander("⚙️ 點此展開：自訂班別與津貼設定", expanded=False):
            df_班別 = pd.DataFrame(db.get('班別設定', []))
            edited_班別 = st.data_editor(
                df_班別, num_rows="dynamic", hide_index=True, width="stretch",
                column_config={
                    "代碼": st.column_config.TextColumn("班別代碼 (例: D)", required=True),
                    "名稱": st.column_config.TextColumn("顯示名稱 (務必獨一無二)", required=True),
                    "工時": st.column_config.NumberColumn("工時 (小時)", min_value=1, max_value=24, step=1),
                    "津貼(元)": st.column_config.NumberColumn("單班津貼 (元)", min_value=0, step=10),
                    "文字顏色": st.column_config.TextColumn("文字顏色 (Hex碼或英文, 例: #FF0000 或 red)")
                }
            )
            if st.button("💾 儲存並套用班別設定", type="primary"):
                新班別清單 = edited_班別.to_dict('records')
                檢查名稱清單 = [班['名稱'] for 班 in 新班別清單]
                if len(檢查名稱清單) != len(set(檢查名稱清單)):
                    st.error("🚨 儲存失敗！有兩個以上的班別使用了相同的「顯示名稱」，請為每個班別取獨一無二的名字（例如：白班A、白班B）")
                else:
                    db['班別設定'] = 新班別清單
                    儲存資料庫(db); st.success("✅ 設定已套用！"); st.rerun()

        st.subheader(f"📊 【{當前單位}】 經典彩色橫式排班表與津貼結算")
        
        全院設定班別 = db.get('班別設定', [])
        津貼對照表 = {班['代碼']: 班.get('津貼(元)', 0) for 班 in 全院設定班別}
        工時對照表 = {班['代碼']: 班.get('工時', 8) for 班 in 全院設定班別}
        
        橫式資料 = []
        for 人 in 單位名單:
            個人班表 = {"職稱/姓名": f"{db['臨床職級'].get(人, '')} {人}", "應上": 160, "已排": 0, "預估津貼(元)": 0}
            for index, row in edited_df.iterrows():
                顯示日期 = row["日期"]; 完整日期 = row["完整日期"]; 代碼 = "OFF" 
                如果有假 = db['請假紀錄'].get(人, {}).get(完整日期)
                
                if 如果有假 and 如果有假["假別"] in 休假類別: 代碼 = "Wish" if 如果有假["假別"] == "預約排休(Wish OFF)" else "Leave"
                else:
                    當天排班 = []
                    for 班 in 全院設定班別:
                        if row.get(班['名稱']) == 人:
                            班別代碼 = 班['代碼']
                            當天排班.append(班別代碼)
                            個人班表["已排"] += 工時對照表.get(班別代碼, 8)
                            個人班表["預估津貼(元)"] += 津貼對照表.get(班別代碼, 0)
                            個人班表[f"{班別代碼}班總數"] = 個人班表.get(f"{班別代碼}班總數", 0) + 1
                            
                    if len(當天排班) > 1: 代碼 = "⚠️ 衝突" 
                    elif len(當天排班) == 1: 代碼 = 當天排班[0]
                個人班表[顯示日期] = 代碼
            橫式資料.append(個人班表)
            
        橫式DF = pd.DataFrame(橫式資料)
        排版欄位 = ["職稱/姓名", "應上", "已排", "預估津貼(元)"] + [col for col in 橫式DF.columns if "總數" in col] + [col for col in 橫式DF.columns if col not in ["職稱/姓名", "應上", "已排", "預估津貼(元)"] and "總數" not in col]
        橫式DF = 橫式DF[排版欄位]
        
        db['橫式班表資料'][當前單位] = 橫式DF
        儲存資料庫(db)
        
        彩色版班表 = 橫式DF.style.map(標示色彩)
        st.dataframe(彩色版班表, hide_index=True, width="stretch")
        
        col_dl, col_save = st.columns([1, 1])
        with col_dl: 
            excel_data = 匯出彩色Excel(橫式DF)
            st.download_button(f"📥 下載 {當前單位} 完美班表 (彩色 Excel)", data=excel_data, file_name=f"{當前單位}_班表.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary", width="stretch")
        with col_save:
            封存名稱 = st.text_input("輸入封存月份 (例: 2026-03)：", value=datetime.date.today().strftime("%Y-%m"), label_visibility="collapsed")
            if st.button("💾 將此班表封存至歷史庫", width="stretch"):
                if 封存名稱 not in db['歷史班表']: db['歷史班表'][封存名稱] = {}
                db['歷史班表'][封存名稱][當前單位] = 橫式DF.to_dict('records')
                儲存資料庫(db); st.success(f"✅ {當前單位} 班表已永久封存至【{封存名稱}】！")

        st.divider()
        st.subheader("📈 排班與津貼數據儀表板 (Dashboard)")
        dash_col1, dash_col2 = st.columns(2)
        統計標籤 = [col for col in 橫式DF.columns if "總數" in col]
        if 統計標籤:
            with dash_col1:
                st.markdown("📊 **各人員班次分配統計**")
                chart_data = 橫式DF[['職稱/姓名'] + 統計標籤].set_index('職稱/姓名')
                st.bar_chart(chart_data)
        with dash_col2:
            st.markdown("💰 **預估津貼排行 (元)**")
            fee_data = 橫式DF[['職稱/姓名', '預估津貼(元)']].set_index('職稱/姓名')
            st.bar_chart(fee_data)

elif 頁面 == "🗂️ 歷史班表封存庫":
    st.title(f"🗂️ 【{當前單位}】 歷史班表庫")
    if db.get('歷史班表'):
        選擇月份 = st.selectbox("請選擇要查看的歷史班表：", list(db['歷史班表'].keys()))
        if 當前單位 in db['歷史班表'][選擇月份]:
            歷史DF = pd.DataFrame(db['歷史班表'][選擇月份][當前單位])
            st.dataframe(歷史DF.style.map(標示色彩), hide_index=True, width="stretch")
            excel_data = 匯出彩色Excel(歷史DF)
            st.download_button("📥 下載此歷史班表 (彩色 Excel)", data=excel_data, file_name=f"{當前單位}_{選擇月份}_歷史班表.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")
        else: st.info(f"這個月份沒有【{當前單位}】的封存紀錄。")
    else: st.info("目前尚無封存的歷史紀錄。")

# ==========================================
# 🌟 6. 全院人事總表與後臺 (🚀 終極動態增刪版)
# ==========================================
elif 頁面 == "⚙️ 全院人事總表與後臺":
    st.title("⚙️ 全院人事總表與後臺")
    
    with st.container(border=True):
        st.subheader("🏥 全院員工超級編輯器 (HR Master Editor)")
        
        # 💡 教學提示區
        st.info("💡 **操作秘笈：** \n* **➕ 新增員工**：滑到表格最下方，點擊灰色的 `+` 號即可新增一列。\n* **🗑️ 刪除員工**：點擊該列表格最左側的空白處將整行反白，然後按下鍵盤的 `Delete` 或 `Backspace` 鍵。\n* *(注意：請編輯完成後務必按下紅色儲存按鈕)*")
        
        全院資料 = []
        for 人 in db['員工名單']:
            全院資料.append({
                "原姓名": 人, 
                "員工編號": db['員工編號'].get(人, ""),
                "員工姓名": 人, 
                "所屬部門": db['所屬部門'].get(人, "護理部"),
                "所屬單位": db['所屬單位'].get(人, "未分發"),
                "職級/職稱": db['臨床職級'].get(人, ""),
                "到職年資(年)": db['年資_年數'].get(人, 0.0),
                "懷孕/免夜班": db['免夜班'].get(人, False)
            })
        df_全院 = pd.DataFrame(全院資料)
        
        col1, col2, col3 = st.columns(3)
        with col1: 搜尋關鍵字 = st.text_input("🔍 搜尋姓名/編號：")
        with col2: 篩選部門 = st.multiselect("🏥 篩選部門：", 部門清單)
        with col3: 篩選單位 = st.multiselect("🏢 篩選單位：", 全院單位清單)
        
        if not df_全院.empty:
            if 搜尋關鍵字: df_全院 = df_全院[df_全院['員工姓名'].str.contains(搜尋關鍵字, case=False, na=False) | df_全院['員工編號'].str.contains(搜尋關鍵字, case=False, na=False)]
            if 篩選部門: df_全院 = df_全院[df_全院['所屬部門'].isin(篩選部門)]
            if 篩選單位: df_全院 = df_全院[df_全院['所屬單位'].isin(篩選單位)]
        
        # 🚀 開啟 num_rows="dynamic" 讓表格可以支援新增與刪除
        edited_全院 = st.data_editor(
            df_全院, hide_index=True, width="stretch", num_rows="dynamic",
            column_config={
                "原姓名": None, # 隱藏原始姓名欄位 (系統背後比對用)
                "所屬部門": st.column_config.SelectboxColumn("所屬部門", options=部門清單),
                "所屬單位": st.column_config.SelectboxColumn("所屬單位", options=全院單位清單),
                "職級/職稱": st.column_config.SelectboxColumn("職級/職稱", options=["N", "N1", "N2", "N3", "N4", "NP", "RN", "醫師", "行政", "技術員"]),
                "懷孕/免夜班": st.column_config.CheckboxColumn("懷孕/免夜班")
            }
        )
        
        if st.button("💾 儲存全院人事修改", type="primary", width="stretch"):
            有錯誤 = False
            
            # 第一關：檢查新增或修改的資料是否有名字為空或重複
            編輯後的姓名清單 = []
            for index, row in edited_全院.iterrows():
                new_name = str(row["員工姓名"]).strip()
                if pd.isna(row["員工姓名"]) or not new_name:
                    st.error("⚠️ 員工姓名不可為空！請檢查您新增或修改的資料列。")
                    有錯誤 = True; break
                if new_name in 編輯後的姓名清單:
                    st.error(f"⚠️ 編輯區內有重複的姓名【{new_name}】！請為他們加上編號或全名。")
                    有錯誤 = True; break
                編輯後的姓名清單.append(new_name)

            if not 有錯誤:
                # 🚀 執行刪除：找出存在於原始篩選表中，但編輯後不見的人
                原始這批人 = df_全院['原姓名'].dropna().tolist()
                後來這批人 = edited_全院['原姓名'].dropna().tolist()
                被刪除的人 = [人 for 人 in 原始這批人 if 人 not in 後來這批人]

                for 人 in 被刪除的人:
                    if 人 in db['員工名單']:
                        db['員工名單'].remove(人)
                        db['員工編號'].pop(人, None); db['所屬部門'].pop(人, None)
                        db['所屬單位'].pop(人, None); db['臨床職級'].pop(人, None)
                        db['年資_年數'].pop(人, None); db['固定休假'].pop(人, None)
                        db['免夜班'].pop(人, None); db['可上長班'].pop(人, None)
                        db['請假紀錄'].pop(人, None)

                # 🚀 執行修改與新增
                for index, row in edited_全院.iterrows():
                    old_name = str(row["原姓名"]).strip() if pd.notna(row["原姓名"]) else ""
                    new_name = str(row["員工姓名"]).strip()

                    # 如果是修改名字，先確保新名字不跟「資料庫中其他未修改的人」衝突
                    資料庫其他人 = [n for n in db['員工名單'] if n != old_name]
                    if new_name in 資料庫其他人:
                        st.error(f"⚠️ 姓名【{new_name}】與資料庫中原有的其他員工衝突！")
                        有錯誤 = True; break

                    if old_name and old_name != new_name: # 名字改了 (原有人員)
                        idx = db['員工名單'].index(old_name)
                        db['員工名單'][idx] = new_name
                        db['員工編號'][new_name] = db['員工編號'].pop(old_name, "")
                        db['所屬部門'][new_name] = db['所屬部門'].pop(old_name, "護理部")
                        db['所屬單位'][new_name] = db['所屬單位'].pop(old_name, "未分發")
                        db['臨床職級'][new_name] = db['臨床職級'].pop(old_name, "")
                        db['年資_年數'][new_name] = db['年資_年數'].pop(old_name, 0.0)
                        db['固定休假'][new_name] = db['固定休假'].pop(old_name, 1)
                        db['免夜班'][new_name] = db['免夜班'].pop(old_name, False)
                        db['可上長班'][new_name] = db['可上長班'].pop(old_name, True)
                        db['請假紀錄'][new_name] = db['請假紀錄'].pop(old_name, {})
                    
                    elif not old_name: # 完全沒有舊名字，代表是「新增的人員」！
                        if new_name not in db['員工名單']:
                            db['員工名單'].append(new_name)
                            db['固定休假'][new_name] = 1
                            db['可上長班'][new_name] = True
                            db['請假紀錄'][new_name] = {}

                    # 更新所有最新屬性
                    db['員工編號'][new_name] = str(row["員工編號"]) if pd.notna(row["員工編號"]) else ""
                    db['所屬部門'][new_name] = str(row["所屬部門"]) if pd.notna(row["所屬部門"]) else "護理部"
                    db['所屬單位'][new_name] = str(row["所屬單位"]) if pd.notna(row["所屬單位"]) else "未分發"
                    db['臨床職級'][new_name] = str(row["職級/職稱"]) if pd.notna(row["職級/職稱"]) else "N"
                    db['年資_年數'][new_name] = float(row["到職年資(年)"]) if pd.notna(row["到職年資(年)"]) else 0.0
                    db['免夜班'][new_name] = bool(row["懷孕/免夜班"])

                if not 有錯誤:
                    儲存資料庫(db)
                    st.success("✅ 全院人事資料已成功更新 (已儲存您的新增與刪除操作)！")
                    st.rerun()

# ==========================================
# 🌟 7. 單位請購與修繕 
# ==========================================
elif 頁面 == "🛠️ 單位請購與修繕":
    st.title(f"🛠️ {當前單位} - 申請與追蹤區")
    
    with st.container(border=True):
        st.subheader("📝 填寫新申請單")
        col1, col2, col3 = st.columns(3)
        with col1: 申請類別 = st.selectbox("申請類別", ["🔧 修繕報修", "📦 物品請購"])
        with col2: 項目名稱 = st.text_input("項目名稱 (例: 病房冷氣、A4影印紙)")
        with col3: 緊急程度 = st.selectbox("緊急程度", ["🟢 一般", "🟡 急件", "🔴 非常緊急 (危及安全)"])
        詳細說明 = st.text_area("詳細說明 (請描述故障狀況或請購原因，越詳細越好！)")
        
        if st.button("送出申請單", type="primary"):
            if 項目名稱:
                新單 = {
                    "申請日期": datetime.date.today().strftime("%Y-%m-%d"),
                    "申請單位": 當前單位,
                    "申請人": st.session_state['當前使用者'],
                    "類別": 申請類別,
                    "項目名稱": 項目名稱,
                    "詳細說明": 詳細說明,
                    "緊急程度": 緊急程度,
                    "處理進度": "📝 待處理"
                }
                db['請購與修繕紀錄'].append(新單)
                儲存資料庫(db)
                st.success("✅ 申請單已成功送出！行政與工務部門將會盡快處理。")
                st.rerun()
            else:
                st.warning("⚠️ 請填寫「項目名稱」再送出喔！")

    st.divider()
    st.subheader("📋 單位申請紀錄與進度追蹤")
    
    單位紀錄 = [單 for 單 in db.get('請購與修繕紀錄', []) if 單['申請單位'] == 當前單位]
    
    if 單位紀錄:
        df_紀錄 = pd.DataFrame(單位紀錄)
        df_紀錄 = df_紀錄[["處理進度", "申請日期", "申請人", "類別", "項目名稱", "緊急程度", "詳細說明"]]
        
        if st.session_state['當前權限'] == "管理員":
            st.info("👑 管理員模式：您可以直接在下方表格修改「處理進度」，修改完請點擊下方按鈕儲存。")
            edited_紀錄 = st.data_editor(
                df_紀錄, disabled=["申請日期", "申請人", "類別", "項目名稱", "緊急程度", "詳細說明"],
                column_config={"處理進度": st.column_config.SelectboxColumn("處理進度", options=["📝 待處理", "⏳ 處理中", "✅ 已結案", "❌ 退件或取消"])},
                hide_index=True, width="stretch"
            )
            
            if st.button("💾 儲存進度更新", width="stretch"):
                其他單位紀錄 = [單 for 單 in db['請購與修繕紀錄'] if 單['申請單位'] != 當前單位]
                更新後的單位紀錄 = edited_紀錄.to_dict('records')
                for 單 in 更新後的單位紀錄: 單['申請單位'] = 當前單位
                db['請購與修繕紀錄'] = 其他單位紀錄 + 更新後的單位紀錄
                儲存資料庫(db); st.success("✅ 進度狀態已成功更新！"); st.rerun()
        else:
            st.dataframe(df_紀錄, hide_index=True, width="stretch")
    else:
        st.info("目前沒有任何請購或修繕紀錄。")