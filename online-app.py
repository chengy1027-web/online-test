import streamlit as st
import pandas as pd
import requests

# 設定 APP 頁面
st.set_page_config(page_title="苗栗站空品即時監測", layout="wide")
st.title("🍀 苗栗縣-苗栗站 空氣品質即時小時值")

# 環境部 API 網址 (苗栗站專屬資料集)
# 修改原本的 API_URL
api_key = st.secrets["MOENV_API_KEY"]
API_URL = f"https://data.moenv.gov.tw/api/v2/aqx_p_488?language=zh&offset=0&limit=1000&api_key=c2987138-cb80-4361-989a-e4c5066237b2" -H "accept: */*""


def fetch_data():
    try:
        # 加入 verify=False 略過 SSL 檢查，並加入 timeout 避免程式卡死
        response = requests.get(API_URL, verify=False, timeout=10)

        # 為了消除「不安全連線」的警告文字，可以加入這行
        requests.packages.urllib3.disable_warnings()

        data = response.json()
        df = pd.DataFrame(data['records'])

        # 轉換數值型態
        df['concentration'] = pd.to_numeric(df['concentration'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"資料抓取失敗: {e}")
        return None


df = fetch_data()

if df is not None:
    # 取得最新監測時間
    last_update = df['monitordate'].iloc[0]
    st.write(f"📊 最後更新時間：{last_update}")

    # 建立橫向指標 (Metrics)
    cols = st.columns(4)
    items = {
        "PM2.5": "細懸浮微粒",
        "PM10": "懸浮微粒",
        "O3": "臭氧",
        "SO2": "二氧化硫"
    }

    for col, (label, name) in zip(cols, items.items()):
        latest_val = df[df['itemname'] == name]['concentration'].iloc[0]
        unit = df[df['itemname'] == name]['itemunit'].iloc[0]
        col.metric(label, f"{latest_val} {unit}")

    # 資料視覺化：趨勢圖表
    st.subheader("📈 近期濃度趨勢")
    target_item = st.selectbox("選擇監測項目", options=df['itemname'].unique())
    chart_data = df[df['itemname'] == target_item].sort_values('monitordate')
    st.line_chart(data=chart_data, x='monitordate', y='concentration')

    # 顯示原始資料表
    with st.expander("查看原始數據"):
        st.write(df)
else:
    st.warning("目前無法取得資料，請檢查 API Key 或網路連線。")
