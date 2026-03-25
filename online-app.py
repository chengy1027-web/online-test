import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="苗栗站空品監測診斷版", layout="wide")
st.title("🧪 苗栗站空品 API 診斷模式")

# 直接使用你的金鑰
api_key = "c2987138-cb80-4361-989a-e4c5066237b2"
# 嘗試抓取更多資料 (增加 limit)
API_URL = f"https://data.moenv.gov.tw/api/v2/aqx_p_488?language=zh&offset=0&limit=1000&api_key={api_key}"

def fetch_raw_data():
    try:
        requests.packages.urllib3.disable_warnings()
        response = requests.get(API_URL, verify=False, timeout=20)
        if response.status_code == 200:
            return response.json().get('records', [])
        else:
            st.error(f"API 連線失敗，代碼：{response.status_code}")
            return []
    except Exception as e:
        st.error(f"發生連線錯誤: {e}")
        return []

raw_records = fetch_raw_data()

if raw_records:
    df_all = pd.DataFrame(raw_records)
    
    # --- 診斷資訊區 ---
    st.success(f"✅ 成功抓取到 {len(df_all)} 筆原始記錄")
    
    # 顯示所有欄位名稱 (檢查大小寫)
    st.write("📋 API 回傳的所有欄位：", list(df_all.columns))
    
    # 自動轉成小寫欄位名稱，避免大小寫問題
    df_all.columns = [c.lower() for c in df_all.columns]
    
    # 顯示所有出現過的站名
    all_sites = df_all['sitename'].unique()
    st.write("📍 目前資料包含的站名：", all_sites)
    
    # --- 篩選區 ---
    # 只要名稱包含 "苗栗" 的都抓出來
    df_miaoli = df_all[df_all['sitename'].str.contains('苗栗', na=False)].copy()
    
    if not df_miaoli.empty:
        st.subheader("📊 苗栗站即時數據明細")
        # 轉換數值
        df_miaoli['concentration'] = pd.to_numeric(df_miaoli['concentration'], errors='coerce')
        st.dataframe(df_miaoli)
    else:
        st.warning("⚠️ 警告：資料中找不到名稱包含『苗栗』的站點。請檢查上方『目前回傳的站名』。")
        
    # 提供原始資料下載，方便檢查
    with st.expander("📥 查看所有原始 JSON 資料"):
        st.json(raw_records[:5]) # 只顯示前五筆
else:
    st.error("❌ 抓不到任何資料，請確認 API 金鑰是否過期或資料集代碼是否正確。")
