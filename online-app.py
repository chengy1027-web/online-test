import streamlit as st
import pandas as pd
import requests

# 1. 頁面基本設定
st.set_page_config(page_title="苗栗站空品即時監測", layout="wide")
st.title("🍀 苗栗縣-苗栗站 空氣品質即時監測")

# 2. API 設定
api_key = "c2987138-cb80-4361-989a-e4c5066237b2"
API_URL = f"https://data.moenv.gov.tw/api/v2/aqx_p_488?language=zh&offset=0&limit=1000&api_key={api_key}"

def fetch_data():
    try:
        requests.packages.urllib3.disable_warnings()
        response = requests.get(API_URL, verify=False, timeout=20)
        if response.status_code == 200:
            data = response.json()
            records = data.get('records', []) if isinstance(data, dict) else data
            if records:
                df = pd.DataFrame(records)
                # 統一轉小寫欄位名稱
                df.columns = [c.lower() for c in df.columns]
                return df
    except Exception as e:
        st.error(f"連線出錯: {e}")
    return pd.DataFrame()

df_all = fetch_data()

if not df_all.empty:
    # 3. 篩選苗栗相關測站
    df_miaoli = df_all[df_all['sitename'].str.contains('苗栗', na=False)].copy()
    
    if not df_miaoli.empty:
        # 轉換時間與數值欄位
        df_miaoli['datacreationdate'] = pd.to_datetime(df_miaoli['datacreationdate'])
        
        # 定義我們要顯示的重點污染物欄位
        target_cols = ['pm2.5', 'pm10', 'o3', 'so2', 'aqi']
        for col in target_cols:
            if col in df_miaoli.columns:
                df_miaoli[col] = pd.to_numeric(df_miaoli[col], errors='coerce')

        # 取得最新一筆資料
        last_update = df_miaoli['datacreationdate'].max()
        st.info(f"📅 最後更新時間：{last_update}")
        
        # 4. 建立即時指標 (Metrics)
        latest = df_miaoli[df_miaoli['datacreationdate'] == last_update].iloc[0]
        
        m_cols = st.columns(5)
        m_cols[0].metric("AQI 指數", f"{latest['aqi']}")
        m_cols[1].metric("PM2.5 (μg/m³)", f"{latest['pm2.5']}")
        m_cols[2].metric("PM10 (μg/m³)", f"{latest['pm10']}")
        m_cols[3].metric("O3 (ppb)", f"{latest['o3']}")
        m_cols[4].metric("SO2 (ppb)", f"{latest['so2']}")

        # 5. 濃度趨勢圖
        st.write("---")
        st.subheader("📈 歷史濃度趨勢 (最近 24 小時)")
        # 排除非數值欄位供使用者選擇
        display_options = ['pm2.5', 'pm10', 'o3', 'so2', 'aqi']
        selected = st.selectbox("請選擇觀測項目：", options=display_options)
        
        chart_data = df_miaoli.sort_values('datacreationdate')
        st.line_chart(data=chart_data, x='datacreationdate', y=selected)

        # 6. 顯示原始資料明細
        with st.expander("🔍 查看苗栗站原始數據明細"):
            st.dataframe(df_miaoli.sort_values('datacreationdate', ascending=False))
    else:
        st.warning("⚠️ 抓到資料了，但裡面沒有『苗栗』站。")
        st.write("目前可用站名：", df_all['sitename'].unique())
else:
    st.error("❌ 無法取得資料，請確認 API 金鑰。")
