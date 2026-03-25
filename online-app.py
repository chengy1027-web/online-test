import streamlit as st
import pandas as pd
import requests

# 1. 基礎頁面設定
st.set_page_config(page_title="苗栗站空品監測", layout="wide")
st.title("🍀 苗栗縣-苗栗站 空氣品質即時監測")

# 2. 定義 API 資訊 (直接寫入金鑰確保連線成功)
api_key = "c2987138-cb80-4361-989a-e4c5066237b2"
API_URL = f"https://data.moenv.gov.tw/api/v2/aqx_p_488?language=zh&offset=0&limit=1000&api_key={api_key}"

def fetch_data():
    try:
        # 關閉 SSL 警告並發送請求 [cite: 7, 8]
        requests.packages.urllib3.disable_warnings()
        response = requests.get(API_URL, verify=False, timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            if 'records' in data:
                return pd.DataFrame(data['records'])
        else:
            st.error(f"API 連線失敗，錯誤碼：{response.status_code}")
    except Exception as e:
        st.error(f"執行出錯: {e}")
    return pd.DataFrame()

# 3. 取得並處理資料
df_all = fetch_data()

if not df_all.empty:
    # 轉換數值型態與時間格式
    df_all['concentration'] = pd.to_numeric(df_all['concentration'], errors='coerce')
    df_all['monitordate'] = pd.to_datetime(df_all['monitordate'])
    
    # 篩選「苗栗」站資料 (使用模糊比對增加成功率)
    df_miaoli = df_all[df_all['sitename'].str.contains('苗栗', na=False)].copy()
    
    if not df_miaoli.empty:
        # 取得最新更新時間
        last_time = df_miaoli['monitordate'].max()
        st.info(f"📊 最後更新時間：{last_time}")
        
        # 建立即時指標 (Metrics)
        cols = st.columns(4)
        items = {"細懸浮微粒": "PM2.5", "懸浮微粒": "PM10", "臭氧": "O3", "二氧化硫": "SO2"}
        
        latest_data = df_miaoli[df_miaoli['monitordate'] == last_time]
        
        for col, (full_name, short_name) in zip(cols, items.items()):
            row = latest_data[latest_data['itemname'] == full_name]
            if not row.empty:
                val = row['concentration'].iloc[0]
                unit = row['itemunit'].iloc[0]
                col.metric(f"{short_name} ({full_name})", f"{val} {unit}")

        # 趨勢圖表
        st.subheader("📈 濃度趨勢圖")
        item_list = df_miaoli['itemname'].unique()
        selected = st.selectbox("選擇觀測項目", item_list)
        chart_data = df_miaoli[df_miaoli['itemname'] == selected].sort_values('monitordate')
        st.line_chart(data=chart_data, x='monitordate', y='concentration')
        
    else:
        st.warning("成功取得苗栗縣資料，但找不到名為『苗栗』的測站。")
        st.write("目前回傳的測站清單：", df_all['sitename'].unique())
else:
    st.error("無法從環境部 API 取得任何資料。")
