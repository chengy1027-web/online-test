import streamlit as st
import pandas as pd
import requests

# 設定 APP 頁面
st.set_page_config(page_title="苗栗站空品即時監測", layout="wide")
st.title("🍀 苗栗縣-苗栗站 空氣品質即時小時值")

# 專家修正：使用 f-string 將 secrets 中的金鑰帶入網址
try:
    api_key = st.secrets["MOENV_API_KEY"]
except KeyError:
    # 如果本地測試沒設定 secrets，先放個備案或提示
    st.error("請在 Streamlit Secrets 中設定 MOENV_API_KEY")
    st.stop()

# 使用 aqx_p_488 資料集 (苗栗縣所有測站小時值)
API_URL = f"https://data.moenv.gov.tw/api/v2/aqx_p_488?language=zh&offset=0&limit=1000&api_key={api_key}"

def fetch_data():
    try:
        headers = {"accept": "*/*"}
        # 解決本地端的 SSL 驗證問題
        requests.packages.urllib3.disable_warnings()
        response = requests.get(API_URL, headers=headers, verify=False, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if 'records' in data:
                df = pd.DataFrame(data['records'])
                # 只篩選「苗栗」站，避免資料太雜
                df_miaoli = df[df['sitename'] == '苗栗'].copy()
                # 數值轉換
                df_miaoli['concentration'] = pd.to_numeric(df_miaoli['concentration'], errors='coerce')
                return df_miaoli
        else:
            st.error(f"API 連線失敗，錯誤碼：{response.status_code}")
            return None
    except Exception as e:
        st.error(f"執行出錯: {e}")
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
