import streamlit as st
import pandas as pd
import requests

# 1. 設定 APP 頁面標題與佈局
st.set_page_config(page_title="苗栗站空品即時監測", layout="wide")
st.title("🍀 苗栗縣-苗栗站 空氣品質即時小時值")

# 直接先放金鑰測試，排除 Secrets 設定問題
api_key = "c2987138-cb80-4361-989a-e4c5066237b2"
API_URL = f"https://data.moenv.gov.tw/api/v2/aqx_p_488?language=zh&offset=0&limit=1000&api_key={api_key}"

def fetch_data():
    try:
        # 關閉 SSL 警告 (解決本地端的憑證錯誤問題)
        requests.packages.urllib3.disable_warnings()
        # 發送請求，verify=False 確保在各種網路環境下都能執行
        response = requests.get(API_URL, verify=False, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if 'records' in data:
                all_df = pd.DataFrame(data['records'])
                
                # 關鍵步驟：篩選出「苗栗站」的資料
                df = all_df[all_df['sitename'].str.contains'苗栗'].copy()
                
                # 將濃度欄位轉為數字，無法轉換的變為 NaN
                df['concentration'] = pd.to_numeric(df['concentration'], errors='coerce')
                # 確保時間欄位格式正確
                df['monitordate'] = pd.to_datetime(df['monitordate'])
                
                return df
        else:
            st.error(f"API 連線失敗，錯誤碼：{response.status_code}")
            return None
    except Exception as e:
        st.error(f"執行出錯: {e}")
        return None

# 執行資料抓取
df = fetch_data()

if df is not None and not df.empty:
    # 取得最新一筆監測時間
    last_update = df.sort_values('monitordate', ascending=False)['monitordate'].iloc[0]
    st.info(f"📅 資料最後更新時間：{last_update}")

    # 3. 建立上方即時指標 (Metrics)
    st.subheader("📌 即時監測數值")
    m_cols = st.columns(4)
    target_items = {
        "細懸浮微粒": "PM2.5",
        "懸浮微粒": "PM10",
        "臭氧": "O3",
        "二氧化硫": "SO2"
    }
    
    # 取得最新一小時的各項數值
    latest_data = df[df['monitordate'] == last_update]
    
    for col, (full_name, short_name) in zip(m_cols, target_items.items()):
        item_row = latest_data[latest_data['itemname'] == full_name]
        if not item_row.empty:
            val = item_row['concentration'].iloc[0]
            unit = item_row['itemunit'].iloc[0]
            col.metric(label=f"{short_name} ({full_name})", value=f"{val} {unit}")
        else:
            col.metric(label=short_name, value="無資料")

    # 4. 資料視覺化：趨勢圖表
    st.write("---")
    st.subheader("📈 24小時濃度趨勢圖")
    
    # 讓使用者選擇想看的測項
    available_items = df['itemname'].unique()
    selected_item = st.selectbox("請選擇觀測項目：", options=available_items, index=0)
    
    # 準備圖表資料
    chart_df = df[df['itemname'] == selected_item].sort_values('monitordate')
    
    # 使用 Streamlit 內建折線圖
    st.line_chart(data=chart_df, x='monitordate', y='concentration')

    # 5. 顯示原始資料表 (折疊式)
    with st.expander("🔍 查看苗栗站原始數據明細"):
        st.dataframe(df.sort_values('monitordate', ascending=False))

else:
    st.warning("⚠️ 暫時抓不到苗栗站的資料，請確認 API 金鑰是否有效，或稍後再試。")
