import streamlit as st
import pandas as pd
import requests

# 1. 頁面設定與自定義 CSS
st.set_page_config(page_title="苗栗空品應變指揮中心", layout="wide")

# 注入 CSS 美化版面
st.markdown("""
    <style>
    /* 全域背景色與字體 */
    .main { background-color: #f5f7f9; }
    /* 美化 Metric 卡片 */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e1e4e8;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    /* 側邊欄顏色 */
    .sidebar .sidebar-content { background-image: linear-gradient(#2e7bcf,#2e7bcf); color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ 苗栗縣空品應變指揮中心")

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
                df.columns = [c.lower() for c in df.columns] # 統一轉小寫
                return df
    except Exception as e:
        st.error(f"連線出錯: {e}")
    return pd.DataFrame()

df_all = fetch_data()

if not df_all.empty:
    # 3. 篩選測站：苗栗、頭份、三義
    target_sites = ['苗栗', '頭份', '三義']
    df_target = df_all[df_all['sitename'].isin(target_sites)].copy()
    
    if not df_target.empty:
        # 資料型態轉換
        df_target['datacreationdate'] = pd.to_datetime(df_target['datacreationdate'])
        num_cols = ['aqi', 'pm2.5', 'pm10', 'o3', 'so2', 'windspeed']
        for col in num_cols:
            if col in df_target.columns:
                df_target[col] = pd.to_numeric(df_target[col], errors='coerce')

        # 4. 側邊欄：功能選單
        with st.sidebar:
            st.header("🎛️ 控制面板")
            selected_site = st.selectbox("切換觀測站點", target_sites)
            st.write("---")
            st.write("📖 **操作說明**：當 AQI 超過 100 時，系統會自動切換為應變模式。")

        site_data = df_target[df_target['sitename'] == selected_site].copy()
        last_update = site_data['datacreationdate'].max()
        latest = site_data[site_data['datacreationdate'] == last_update].iloc[0]

        # 5. AQI 警示功能與應變文字
        aqi_val = latest['aqi']
        if aqi_val > 100:
            st.markdown(f"""
                <div style="padding:25px;background-color:#d9534f;border-radius:10px;border-left:10px solid #a94442;margin-bottom:20px;">
                    <h2 style="color:white;margin:0;">🚨 應變模式啟動：{selected_site}站 AQI {aqi_val}</h2>
                    <p style="color:white;font-size:20px;margin-top:10px;font-weight:bold;">
                        空氣品質不良，啟動應變及加強防護措施！
                    </p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.success(f"✅ {selected_site} 站目前空氣品質良好 (AQI: {aqi_val})")

        # 6. 即時指標 (分兩列顯示更美觀)
        st.write(f"### 📍 {selected_site} 站即時數據 (更新於 {last_update})")
        m_cols = st.columns(5)
        m_cols[0].metric("PM2.5", f"{latest['pm2.5']} μg/m³")
        m_cols[1].metric("PM10", f"{latest['pm10']} μg/m³")
        m_cols[2].metric("O3", f"{latest['o3']} ppb")
        m_cols[3].metric("SO2", f"{latest['so2']} ppb")
        m_cols[4].metric("🌬️ 風速", f"{latest['windspeed']} m/s")

        # 7. 歷史趨勢圖 (使用單一圖表容器美化)
        st.write("---")
        c1, c2 = st.columns([1, 3])
        with c1:
            st.subheader("📊 趨勢分析")
            display_options = {
                'aqi': 'AQI 指數',
                'pm2.5': 'PM2.5 濃度',
                'pm10': 'PM10 濃度',
                'windspeed': '風速監測'
            }
            selected_item = st.radio("觀測項目", options=list(display_options.keys()), format_func=lambda x: display_options[x])
        with c2:
            chart_data = site_data.sort_values('datacreationdate')
            st.line_chart(data=chart_data, x='datacreationdate', y=selected_item)

        # 8. 原始數據表格 (精簡顯示)
        with st.expander("🔍 檢視歷史數據明細"):
            st.dataframe(site_data[['datacreationdate', 'aqi', 'pm2.5', 'pm10', 'windspeed', 'status']].sort_values('datacreationdate', ascending=False), use_container_width=True)
    else:
        st.warning("⚠️ 無法獲取特定站點資料。")
else:
    st.error("❌ API 連線中斷。")
