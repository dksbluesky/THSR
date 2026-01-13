import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# 需要安裝: pip install webdriver-manager selenium
from webdriver_manager.chrome import ChromeDriverManager 

# ================= 【模式切換開關】 =================
# True = 模擬演習模式 (現在測試用，會馬上啟動)
# False = 實戰模式 (搶票當天用，會等到指定時間)
SIMULATION_MODE = True
# ====================================================


# ================= 【配置區】 =================
# 你的身分證字號 (用於快速填寫，請自行替換)
MY_ID = "Y120170281"

if SIMULATION_MODE:
    # --- 🟡 模擬模式設定 (測試用) ---
    print("【警告】目前為「模擬演習模式」！")
    print("程式將在 10 秒後啟動瀏覽器，請觀察填寫是否正確。")
    
    # 設定啟動時間為：現在時間 + 10秒
    TARGET_TIME = datetime.now() + timedelta(seconds=10)
    
    # 【重要】請在此輸入一個「目前已經開放訂票」的日期進行測試 (例如明天)
    # 格式 YYYY/MM/DD
    TRAVEL_DATE = datetime.now().strftime("%Y/%m/%d") # 預設今天，建議手動改成明天例如 "2024/02/20"
    TRAVEL_TIME = "12:00" # 測試時間
    
    # 測試用的起訖站 (例如 台北=2 到 高雄=12)
    START_STATION_VAL = "2"
    END_STATION_VAL = "12"
    TICKET_COUNT = "1"

else:
    # --- 🔴 實戰模式設定 (2026/1/16 當天用) ---
    print("【注意】目前為「實戰模式」！將等待至目標時刻。")
    
    # 目標搶票時間：2026年1月16日 00:00:00
    TARGET_TIME = datetime(2026, 1, 16, 0, 0, 0)
    
    # 任務 B：2/16 台南(10) -> 南港(1)，1 張
    TRAVEL_DATE = "2026/02/16" 
    TRAVEL_TIME = "12:00" 
    START_STATION_VAL = "10" 
    END_STATION_VAL = "1" 
    TICKET_COUNT = "1"
# =======================================================


def launch_booking_assistant():
    print(f"--------------------------------------------------")
    print(f"目前的目標日期: {TRAVEL_DATE} {TRAVEL_TIME}")
    print(f"等待啟動時間: {TARGET_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"--------------------------------------------------")
    
    # 精準倒數計時
    while datetime.now() < TARGET_TIME:
        # 在最後 10 秒每秒印出提示 (模擬模式下這會馬上出現)
        remaining_seconds = (TARGET_TIME - datetime.now()).total_seconds()
        if remaining_seconds < 11 and remaining_seconds > 0:
             print(f"倒數: {int(remaining_seconds)}")
             time.sleep(0.9)
        else:
             time.sleep(0.1)

    print(">>> 時間到！啟動瀏覽器 <<<")

    # 初始化 Chrome 選項
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    # 嘗試隱藏自動化跡象
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        # 1. 前往高鐵訂票頁面
        driver.get("https://irs.thsrc.com.tw/IMINT/")
        wait = WebDriverWait(driver, 15)
        
        # 2. 處理 Cookie 同意 (如果出現)
        try:
            cookie_btn = wait.until(EC.element_to_be_clickable((By.ID, "cookieDone")))
            cookie_btn.click()
            print("已接受 Cookie")
        except:
            print("無 Cookie 提示跳過")

        print(f"正在嘗試預填資訊 (日期: {TRAVEL_DATE})...")
        
        # --- 使用 JavaScript 快速填寫表單值 (速度最快) ---
        
        # 選擇起訖站
        driver.execute_script(f"document.querySelector('select[name=\"selectStartStation\"]').value = '{START_STATION_VAL}';")
        driver.execute_script(f"document.querySelector('select[name=\"selectDestinationStation\"]').value = '{END_STATION_VAL}';")
        
        # 選擇日期 (嘗試用 JS 強制寫入日期欄位值)
        # 注意：這在實戰中可能因為網站改版而失效，若失效請手動選擇日期
        try:
            # 尋找日期輸入框，通常 ID 是 toTimeInputField，但可能會變
            date_input_js = f"document.getElementById('toTimeInputField').value = '{TRAVEL_DATE}';"
            driver.execute_script(date_input_js)
            print("已嘗試透過 JS 填寫日期")
        except Exception as e:
            print(f"JS 填寫日期失敗 (不影響後續，請手動填寫): {e}")

        # 選擇時間
        driver.execute_script(f"document.querySelector('select[name=\"toTimeTable\"]').value = '{TRAVEL_TIME}';")
        
        # 選擇張數
        driver.execute_script(f"document.querySelector('select[name=\"ticketPanel:rows:0:ticketAmount\"]').value = '{TICKET_COUNT}';")

        print("--------------------------------------------------")
        print("【演習/實戰提示】")
        print("1. 程式已嘗試預選起訖站、時間、張數。")
        print(f"2. 【請檢查日期】是否正確填入: {TRAVEL_DATE} (若無請手動選擇)。")
        print("3. 【最關鍵】請手動輸入圖形驗證碼！")
        print(f"4. 按下「開始查詢」，在下一頁輸入身分證號: {MY_ID}")
        print("--------------------------------------------------")

        # 保持瀏覽器開啟，直到你手動關閉
        while True:
            time.sleep(1)

    except Exception as e:
        print(f"發生意外錯誤: {e}")
        # 在實戰中如果發生這個錯誤，請不要關閉視窗，直接手動接管操作
        print("請放棄程式，立即全手動操作！")

if __name__ == "__main__":
    # 執行主程式
    launch_booking_assistant()