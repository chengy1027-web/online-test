import streamlit as st
import pandas as pd
import requests

# 1. 頁面基本設定
st.set_page_config(page_title="苗栗站空品即時監測", layout="wide")
st.title("🍀 苗栗縣-苗栗站 空氣品質即時小時值")

# 2. API 設定 (直接使用你的金鑰)
api_key = "c2987138-cb80-4361-989a-e4c5066237b2"
# 使用 aqx_p_488 資料集 (苗栗縣所有測站小時值)
API_URL = f"https://data.moenv.gov.tw/api/v2/aqx_p_488?language=zh&offset=0&limit=1000&api_key={api_key}"

def fetch_data():
    try:
        # 關閉 SSL 警告 (解決本地端的憑證驗證問題)
        requests.packages.urllib3.disable_warnings()
        # 發送請求，verify=False 確保在各種網路環境下都能執行，並設定 timeout 避免卡死
        response = requests.get(API_URL, verify=False, timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            
            # 3. 強韌的資料解析邏輯：判斷回傳的是字典還是列表
            if isinstance(data, dict):
                records = data.get('records', [])
            elif isinstance(data, list):
                records = data
            else:
                records = []
                
            if records:
                df = pd.DataFrame(records)
                # 將欄位名稱統一轉為小寫，避免大小寫不一導致篩選失敗
                df.columns = [c.lower() for c in df.columns]
                return df
        else:
            st.error(f"API 連線失敗，錯誤碼：{response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"執行出錯: {e}")
        return pd.DataFrame()

# 4. 取得資料並進行視覺化處理
df_all = fetch_data()

if not df_all.empty:
    # 數值型態與時間格式轉換
    df_all['concentration'] = pd.to_numeric(df_all['concentration'], errors='coerce')
    df_all['monitordate'] = pd.to_datetime(df_all['monitordate'])
    
    # 篩選「苗栗」站資料 (模糊比對包含『苗栗』二字的站名)
    df_miaoli = df_all[df_all['sitename'].str.contains('苗栗', na=False)].copy()
    
    if not df_miaoli.empty:
        # 取得最新監測時間
        last_update = df_miaoli['monitordate'].max()
        st.info(f"📊 苗栗站最後更新時間：{last_update}")

        # 建立即時指標 (Metrics)
        st.subheader("📌 即時監測數值")
        m_cols = st.columns(4)
        target_items = {
            "細懸浮微粒": "PM2.5",
            "懸浮微粒": "PM10",
            "臭氧": "O3",
            "二氧化硫": "SO2"
        }
        
        # 取得最後一個小時的數據
        latest_data = df_miaoli[df_miaoli['monitordate'] == last_update]
        
        for col, (full_name, short_name) in zip(m_cols, target_items.items()):
            item_row = latest_data[latest_data['itemname'] == full_name]
            if not item_row.empty:
                val = item_row['concentration'].iloc[0]
                unit = item_row['itemunit'].iloc[0]
                col.metric(label=f"{short_name} ({full_name})", value=f"{val} {unit}")
            else:
                col.metric(label=short_name, value="無資料")

        # 5. 數據趨勢圖
        st.write("---")
        st.subheader("📈 24小時濃度趨勢圖")
        available_items = df_miaoli['itemname'].unique()
        selected_item = st.selectbox("請選擇觀測項目：", options=available_items)
        
        chart_df = df_miaoli[df_miaoli['itemname'] == selected_item].sort_values('monitordate')
        st.line_chart(data=chart_df, x='monitordate', y='concentration')

        # 6. 顯示原始資料表
        with st.expander("🔍 查看苗栗站原始數據明細"):
            st.dataframe(df_miaoli.sort_values('monitordate', ascending=False))
            
    else:
        st.warning("⚠️ 成功連線 API，但目前資料中沒有名稱包含『苗栗』的站點。")
        st.write("目前 API 回傳的所有站名：", df_all['sitename'].unique())
else:
    st.error("❌ 無法取得任何資料。請確認環境部 API 是否正常運作。")
