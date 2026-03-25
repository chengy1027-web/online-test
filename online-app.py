import streamlit as st
import pandas as pd
import requests

# 1. 頁面設定
st.set_page_config(page_title="苗栗/頭份/三義空品監測", layout="wide")
st.title("🍀 苗栗縣重點測站 - 空氣品質即時監測")

# 2. API 設定
api_key = "c2987138-cb80-4361-989a-e4c5066237b2"
API_URL = f"https://data.moenv.gov.tw/api/v2/aqx_p_488?language=zh&offset=0&limit=50000&api_key={api_key}"

def fetch_data():
    try:
        requests.packages.urllib3.disable_warnings()
        response = requests.get(API_URL, verify=False, timeout=30)
        if response.status_code == 200:
            data = response.json()
            records = data.get('records', []) if isinstance(data, dict) else data
            if records:
                df = pd.DataFrame(records)
                df.columns = [c.lower() for c in df.columns] # 統一轉小寫
                return df
    except Exception as e:
        st.error(f"連線出錯: {e}")
    return pd.DataFrame()

df_all = fetch_data()

if not df_all.empty:
    # 3. 篩選目標測站：苗栗、頭份、三義
    target_sites = ['苗栗', '頭份', '三義']
    df_target = df_all[df_all['sitename'].isin(target_sites)].copy()
    
    if not df_target.empty:
        # 資料型態轉換
        df_target['datacreationdate'] = pd.to_datetime(df_target['datacreationdate'])
        num_cols = ['aqi', 'pm2.5', 'pm10', 'o3', 'so2','no2', 'windspeed']
        for col in num_cols:
            if col in df_target.columns:
                df_target[col] = pd.to_numeric(df_target[col], errors='coerce')

        # 4. 側邊欄：選擇測站
        st.sidebar.header("設定")
        selected_site = st.sidebar.selectbox("切換觀測站點", target_sites)
        site_data = df_target[df_target['sitename'] == selected_site].copy()
        
        # 取得最新一筆資料
        last_update = site_data['datacreationdate'].max()
        latest = site_data[site_data['datacreationdate'] == last_update].iloc[0]

        st.info(f"📍 當前站點：{selected_site} | 🕒 更新時間：{last_update}")

        # 5. AQI 警示功能
        aqi_val = latest['aqi']
        if aqi_val > 100:
            st.markdown(f"""
                <div style="padding:20px;background-color:#FF4B4B;border-radius:10px;">
                    <h2 style="color:white;margin:0;">⚠️ AQI：{aqi_val} (對敏感族群不健康)</h2>
                    <p style="color:white;font-size:18px;margin-top:10px;">
                        <b>空氣品質不良，啟動應變及加強防護措施！</b>
                    </p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.success(f"✅ 當前 AQI 指數：{aqi_val} (品質良好/普通)")

        # 6. 即時指標顯示 (Metrics)
        st.write("### 📌 即時監測數據")
        m_cols = st.columns(6)
        m_cols[0].metric("PM10", f"{latest['pm10']} μg/m³")
        m_cols[1].metric("PM2.5", f"{latest['pm2.5']} μg/m³")
        m_cols[2].metric("O3 (臭氧)", f"{latest['o3']} ppb")
        m_cols[3].metric("SO2 (二氧化硫)", f"{latest['so2']} ppb")
        m_cols[4].metric("NO2 (二氧化氮)", f"{latest['no2']} ppb")
        m_cols[5].metric("🌬️ 風速", f"{latest['windspeed']} m/s")

        # 7. 歷史趨勢圖
        st.write("---")
        st.subheader(f"📈 {selected_site}站 24小時趨勢")
        display_options = {
            'aqi': 'AQI 指數',
            'pm2.5': '細懸浮微粒 (PM2.5)',            
            'pm10': '懸浮微粒 (PM10)',
            'o3': '臭氧 (O3)',
            'windspeed': '風速 (Wind Speed)'
        }
        selected_item = st.selectbox("請選擇觀測項目：", options=list(display_options.keys()), format_func=lambda x: display_options[x])
        
        chart_data = site_data.sort_values('datacreationdate')
        st.line_chart(data=chart_data, x='datacreationdate', y=selected_item)

        # 8. 數據表
        with st.expander("🔍 查看原始數據明細"):
            st.dataframe(site_data.sort_values('datacreationdate', ascending=False))
    else:
        st.warning("⚠️ 抓到資料了，但裡面沒有苗栗、頭份或三義站。")
else:
    st.error("❌ 無法取得資料，請確認環境部 API 狀態。")
