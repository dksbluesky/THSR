import streamlit as st
import pandas as pd
from datetime import datetime, time

# ==========================================
# 設定頁面
# ==========================================
st.set_page_config(page_title="2026 春節高鐵時刻表查詢", page_icon="🚅")
st.title("🚅 2026 春節高鐵時刻查詢 Web App")
st.markdown("""
此工具支援 **Excel 檔案上傳**。
請先使用轉檔腳本 (batch_convert.py) 將 PDF 轉為 Excel，再將檔案上傳至此進行查詢。
""")

# ==========================================
# 1. 檔案上傳區
# ==========================================
uploaded_file = st.file_uploader("📂 請上傳高鐵時刻表 Excel 檔 (.xlsx)", type=["xlsx"])

# ==========================================
# 2. 輔助函式
# ==========================================
def is_train_operating(selected_date_str, op_day_str):
    if not isinstance(op_day_str, str): # 防呆：如果 Excel 讀出來不是字串
        return True 
    if "每日" in op_day_str:
        return True
    
    sel_dt = datetime.strptime(selected_date_str, "%Y/%m/%d")
    sel_md = f"{sel_dt.month}/{sel_dt.day}"
    
    # 簡單處理日期範圍邏輯
    parts = op_day_str.replace(" ", "").replace("~", "-").split(",")
    for part in parts:
        if "-" in part:
            try:
                start_s, end_s = part.split("-")
                def parse_md(s):
                    m, d = map(int, s.split("/"))
                    return m * 100 + d
                
                if parse_md(start_s) <= parse_md(sel_md) <= parse_md(end_s):
                    return True
            except:
                continue
        else:
            if part == sel_md:
                return True
    return False

def calculate_duration(t_start, t_end):
    # 處理 Excel 讀入可能是 datetime.time 或 字串 的情況
    if pd.isna(t_start) or pd.isna(t_end) or str(t_start).strip() in ["-", "nan"]:
        return 9999
    
    # 統一轉為 datetime
    def to_dt(t):
        if isinstance(t, time):
            return datetime.combine(datetime.today(), t)
        if isinstance(t, str):
            # 嘗試解析字串時間
            try:
                return datetime.strptime(t, "%H:%M")
            except:
                return None
        return None

    dt_start = to_dt(t_start)
    dt_end = to_dt(t_end)

    if not dt_start or not dt_end:
        return 9999

    if dt_end < dt_start:
        seconds = (dt_end - dt_start).total_seconds() + 24*3600
    else:
        seconds = (dt_end - dt_start).total_seconds()
        
    return int(seconds / 60)

# ==========================================
# 3. 主程式邏輯
# ==========================================
if uploaded_file is not None:
    try:
        # 讀取 Excel 的所有工作表
        xls = pd.ExcelFile(uploaded_file)
        sheet_names = xls.sheet_names
        
        # 讓使用者選擇工作表（通常是 '南下' 或 '北上'）
        st.sidebar.header("🔍 資料設定")
        selected_sheet = st.sidebar.selectbox("選擇時刻表 (Sheet)", sheet_names)
        
        df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
        
        # 清洗欄位名稱 (移除換行符號)
        df.columns = [str(c).replace("\n", "").strip() for c in df.columns]
        
        # 嘗試自動抓取欄位
        all_columns = df.columns.tolist()
        
        # --- 側邊欄：篩選條件 ---
        st.sidebar.divider()
        
        # 設定起訖站 (預設嘗試抓取 '南港' 和 '台南'，抓不到就選第1個)
        default_start = all_columns.index("南港") if "南港" in all_columns else 0
        default_end = all_columns.index("台南") if "台南" in all_columns else 0
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            start_station = st.selectbox("起點站", all_columns, index=default_start)
        with col2:
            end_station = st.selectbox("終點站", all_columns, index=default_end)
            
        # 日期與時間
        date_options = [f"2026/02/{d:02d}" for d in range(13, 24)]
        selected_date = st.sidebar.selectbox("選擇日期", date_options)
        
        time_range = st.sidebar.slider("發車時間範圍", value=(time(6, 0), time(23, 59)), format="HH:mm")
        
        # 開始過濾
        results = []
        
        # 找出關鍵欄位名稱 (有些 Excel 轉出來可能是 '車次' 或 'Train No.')
        # 這裡做模糊比對，只要欄位名稱包含 '車' 或 'Train' 就當作車次欄
        train_col = next((c for c in df.columns if "車次" in c or "Train" in c), df.columns[0])
        day_col = next((c for c in df.columns if "行駛日" in c or "Day" in c), None)

        for index, row in df.iterrows():
            # 1. 取得基本資料
            train_no = row[train_col]
            t_start = row[start_station]
            t_end = row[end_station]
            
            # 2. 判斷行駛日 (如果有該欄位)
            op_day = "每日"
            if day_col:
                op_day_val = row[day_col]
                if pd.notna(op_day_val):
                    op_day = str(op_day_val)
            
            if not is_train_operating(selected_date, op_day):
                continue

            # 3. 判斷是否有時刻
            if pd.isna(t_start) or pd.isna(t_end) or str(t_start).strip() in ["-", "nan"]:
                continue

            # 4. 判斷時間範圍
            try:
                check_time = t_start
                if isinstance(check_time, str):
                    check_time = datetime.strptime(check_time, "%H:%M").time()
                
                if not (time_range[0] <= check_time <= time_range[1]):
                    continue
            except:
                continue

            # 5. 計算時間
            duration = calculate_duration(t_start, t_end)
            
            if duration <= 120:
                 results.append({
                    "車次": train_no,
                    "發車時間": t_start,
                    "抵達時間": t_end,
                    "行車時間 (分)": duration,
                    "備註": op_day
                })

        # 顯示結果
        if results:
            result_df = pd.DataFrame(results)
            # 排序
            result_df = result_df.sort_values(by="發車時間")
            
            st.subheader(f"查詢結果：{selected_date} ({start_station} → {end_station})")
            st.write(f"共找到 **{len(result_df)}** 班符合條件的直達/快車（行車 ≤ 120 分）：")
            
            st.dataframe(
                result_df.style.background_gradient(subset=["行車時間 (分)"], cmap="Greens_r"),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "車次": st.column_config.TextColumn("車次", width="small"),
                    "發車時間": st.column_config.TimeColumn("發車時間", format="HH:mm"),
                    "抵達時間": st.column_config.TimeColumn("抵達時間", format="HH:mm"),
                    "行車時間 (分)": st.column_config.NumberColumn("行車時間", format="%d 分"),
                }
            )
        else:
            st.warning("⚠️ 找不到符合條件的班次，請檢查篩選條件或 Excel 內容。")

    except Exception as e:
        st.error(f"讀取 Excel 發生錯誤：{e}")
        st.info("請確認上傳的是由轉檔腳本產生的標準格式 Excel。")

else:
    st.info("👆 請在上方上傳 Excel 檔案以開始查詢。")
