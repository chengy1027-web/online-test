import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="苗栗站空品即時監測", layout="wide")
st.title("🍀 苗栗縣-苗栗站 空氣品質即時小時值")

# 直接使用你的金鑰
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
                # 重要：將所有欄位名稱轉為小寫，避免 KeyError
                df.columns = [c.lower() for c in df.columns]
                return df
    except Exception as e:
        st.error(f"連線出錯: {e}")
    return pd.DataFrame()

df_all = fetch_data()

if not df_all.empty:
    # 檢查必要欄位是否存在，避免程式崩潰
    if 'concentration' in df_all.columns and 'monitordate' in df_all.columns:
        df_all['concentration'] = pd.to_numeric(df_all['concentration'], errors='coerce')
        df_all['monitordate'] = pd.to_datetime(df_all['monitordate'])
        
        # 篩選苗栗相關測站
        df_miaoli = df_all[df_all['sitename'].str.contains('苗栗', na=False)].copy()
        
        if not df_miaoli.empty:
            last_update = df_miaoli['monitordate'].max()
            st.info(f"📊 最後更新時間：{last_update}")
            
            # 指標顯示
            cols = st.columns(4)
            items = {"細懸浮微粒": "PM2.5", "懸浮微粒": "PM10", "臭氧": "O3", "二氧化硫": "SO2"}
            latest = df_miaoli[df_miaoli['monitordate'] == last_update]
            
            for col, (f_n, s_n) in zip(cols, items.items()):
                row = latest[latest['itemname'] == f_n]
                if not row.empty:
                    col.metric(f"{s_n}", f"{row['concentration'].iloc[0]} {row['itemunit'].iloc[0]}")
            
            # 趨勢圖
            st.subheader("📈 濃度趨勢圖")
            sel = st.selectbox("選擇項目", df_miaoli['itemname'].unique())
            st.line_chart(df_miaoli[df_miaoli['itemname'] == sel], x='monitordate', y='concentration')
        else:
            st.warning("抓不到名為『苗栗』的站點。")
            st.write("目前可用站名：", df_all['sitename'].unique())
    else:
        st.error(f"API 回傳欄位不符。目前欄位有：{list(df_all.columns)}")
else:
    st.error("無法取得資料。")
