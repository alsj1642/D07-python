import os

import requests
import streamlit as st
from dotenv import load_dotenv

API = {
    "weather": "https://api.openweathermap.org/data/2.5/weather",  # 🔌 OpenWeather 현재 날씨
}

# 서울 시청 위치
SEOUL_LAT = 37.5665
SEOUL_LON = 126.9780


@st.cache_data(ttl=600)  # 10분 동안은 같은 결과를 재사용 (API 호출 횟수 절약)
def get_weather(api_key):
    """날씨 데이터를 돌려주거나, 실패하면 (None, 에러 메시지)를 돌려줍니다."""
    params = {
        "lat": SEOUL_LAT,
        "lon": SEOUL_LON,
        "units": "metric",  # 섭씨(℃)
        "lang": "kr",       # 날씨 설명을 한국어로
        "appid": api_key,
    }
    try:
        res = requests.get(API["weather"], params=params, timeout=10)  # 🔌 API 호출
    except requests.exceptions.Timeout:
        return None, "날씨 서버가 10초 안에 대답하지 않았어요. 잠시 뒤에 다시 시도해 주세요."
    except requests.exceptions.RequestException:
        return None, "날씨 서버에 연결하지 못했어요. 인터넷 연결을 확인해 주세요."

    if res.status_code == 401:
        return None, "날씨 키가 틀렸거나 아직 켜지지 않았어요(가입 후 최대 2시간)."
    if res.status_code == 404:
        return None, "그 도시를 찾지 못했어요."
    if res.status_code == 429:
        return None, "1분에 너무 많이 불렀어요. 잠시 뒤에 다시 시도해 주세요."
    if res.status_code != 200:
        return None, f"날씨를 가져오지 못했어요. (응답 코드 {res.status_code})"

    return res.json(), None


def main():
    st.set_page_config(page_title="서울 지금 날씨", page_icon="🌤️")
    st.title("🌤️ 서울 지금 날씨")

    load_dotenv()
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        st.error(".env에 OPENWEATHER_API_KEY가 없어요. .env.example을 보고 채워 주세요.")
        st.stop()

    if st.button("🔄 새로고침"):
        get_weather.clear()  # 캐시를 지우고 다시 불러오기

    with st.spinner("날씨를 불러오는 중..."):
        data, error = get_weather(api_key)

    if error:
        st.error(error)
        st.stop()

    temp = data["main"]["temp"]                     # data["main"]["temp"] = 지금 기온
    feels_like = data["main"]["feels_like"]         # data["main"]["feels_like"] = 체감온도
    humidity = data["main"]["humidity"]             # data["main"]["humidity"] = 습도(%)
    description = data["weather"][0]["description"]  # data["weather"][0]["description"] = 날씨 설명
    icon = data["weather"][0]["icon"]                # data["weather"][0]["icon"] = 날씨 아이콘 코드

    col_icon, col_desc = st.columns([1, 3])
    col_icon.image(f"https://openweathermap.org/img/wn/{icon}@2x.png")
    col_desc.subheader(description)

    col1, col2, col3 = st.columns(3)
    col1.metric("기온", f"{temp:.1f}℃")
    col2.metric("체감온도", f"{feels_like:.1f}℃", f"{feels_like - temp:+.1f}℃", delta_color="off")
    col3.metric("습도", f"{humidity}%")

    st.caption("날씨: OpenWeather")


if __name__ == "__main__":
    main()
