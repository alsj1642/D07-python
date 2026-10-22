import os
from datetime import timedelta, timezone
from email.utils import parsedate_to_datetime

import requests
import streamlit as st
from dotenv import load_dotenv

API = {
    "latest": "https://v6.exchangerate-api.com/v6/latest/USD",  # 🔌 ExchangeRate-API 최신 환율 (USD 기준)
}

KST = timezone(timedelta(hours=9))  # 한국 시간

# 고를 수 있는 통화 (코드: 이름)
CURRENCIES = {
    "KRW": "대한민국 원",
    "USD": "미국 달러",
    "JPY": "일본 엔",
    "EUR": "유로",
    "CNY": "중국 위안",
    "GBP": "영국 파운드",
    "HKD": "홍콩 달러",
    "TWD": "대만 달러",
    "VND": "베트남 동",
    "THB": "태국 바트",
    "AUD": "호주 달러",
    "CAD": "캐나다 달러",
}

# 아래 "원화로 보면" 표에 보여 줄 통화와 기준 금액 (엔·동은 100 단위가 익숙해서)
KRW_TABLE = {"USD": 1, "JPY": 100, "EUR": 1, "CNY": 1, "GBP": 1, "VND": 100}

ERROR_MESSAGES = {
    "invalid-key": "환율 키가 틀렸어요. .env의 EXCHANGERATE_API_KEY를 확인해 주세요.",
    "inactive-account": "환율 사이트 가입 인증 메일을 확인해 주세요.",
    "quota-reached": "이번 달 무료 사용량(1,500번)을 다 썼어요.",
}

MINIMAL_CSS = """
<style>
    .block-container { max-width: 640px; padding-top: 3rem; }
    h1 { font-weight: 600; letter-spacing: -0.02em; }
    .result {
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0 0.5rem;
    }
    .result .from { color: #888; font-size: 0.95rem; }
    .result .to { font-size: 2rem; font-weight: 600; margin-top: 0.25rem; }
    .result .unit { color: #888; font-size: 0.85rem; margin-top: 0.5rem; }
</style>
"""


@st.cache_data(ttl=3600)  # 1시간 동안 결과 재사용 (무료 플랜은 한 달 1,500번)
def get_rates(api_key):
    """USD 기준 환율을 한 번만 받아 와서 (데이터, None) 또는 (None, 에러 메시지)를 돌려줍니다."""
    headers = {"Authorization": f"Bearer {api_key}"}  # 키는 주소가 아니라 헤더로
    try:
        res = requests.get(API["latest"], headers=headers, timeout=10)  # 🔌 API 호출
    except requests.exceptions.Timeout:
        return None, "환율 서버가 10초 안에 대답하지 않았어요. 잠시 뒤에 다시 시도해 주세요."
    except requests.exceptions.RequestException:
        return None, "환율 서버에 연결하지 못했어요. 인터넷 연결을 확인해 주세요."

    try:
        data = res.json()
    except ValueError:
        return None, f"환율을 가져오지 못했어요. (응답 코드 {res.status_code})"

    if data.get("result") != "success":                # data["result"] = "success" 또는 "error"
        error_type = data.get("error-type", "")        # data["error-type"] = 실패 이유
        return None, ERROR_MESSAGES.get(error_type, f"환율을 가져오지 못했어요. ({error_type or res.status_code})")

    return data, None


def convert(amount, from_code, to_code, rates):
    """USD 기준 환율로 두 통화를 바꿉니다. (API 한 번으로 모든 조합 계산)"""
    return amount / rates[from_code] * rates[to_code]


def format_money(value, code):
    # 원·엔·동처럼 소수점을 안 쓰는 통화는 정수로
    if code in ("KRW", "JPY", "VND"):
        return f"{value:,.0f} {code}"
    return f"{value:,.2f} {code}"


def swap_currencies():
    st.session_state.from_code, st.session_state.to_code = (
        st.session_state.to_code,
        st.session_state.from_code,
    )


def main():
    st.set_page_config(page_title="환율 계산기", page_icon="💱", layout="centered")
    st.markdown(MINIMAL_CSS, unsafe_allow_html=True)
    st.title("환율 계산기")

    load_dotenv()
    api_key = os.getenv("EXCHANGERATE_API_KEY")
    if not api_key:
        st.error(".env에 EXCHANGERATE_API_KEY가 없어요. .env.example을 보고 채워 주세요.")
        st.stop()

    data, error = get_rates(api_key)
    if error:
        st.error(error)
        if st.button("다시 불러오기"):
            st.cache_data.clear()
            st.rerun()
        st.stop()

    rates = data["conversion_rates"]  # data["conversion_rates"] = 1 USD가 각 통화로 얼마인지

    st.session_state.setdefault("from_code", "USD")
    st.session_state.setdefault("to_code", "KRW")

    amount = st.number_input("금액", min_value=0.0, value=1.0, step=1.0, format="%.2f")

    col_from, col_swap, col_to = st.columns([5, 1, 5], vertical_alignment="bottom")
    label = lambda code: f"{code} · {CURRENCIES[code]}"
    col_from.selectbox("보내는 통화", list(CURRENCIES), format_func=label, key="from_code")
    col_swap.button("⇄", on_click=swap_currencies, use_container_width=True, help="통화 바꾸기")
    col_to.selectbox("받는 통화", list(CURRENCIES), format_func=label, key="to_code")

    from_code = st.session_state.from_code
    to_code = st.session_state.to_code
    result = convert(amount, from_code, to_code, rates)
    unit_rate = convert(1, from_code, to_code, rates)

    st.markdown(
        f"""
        <div class="result">
            <div class="from">{format_money(amount, from_code)} =</div>
            <div class="to">{format_money(result, to_code)}</div>
            <div class="unit">1 {from_code} = {unit_rate:,.4f} {to_code}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()
    st.subheader("원화로 보면")
    st.table(
        {
            "통화": [f"{base:g} {code} · {CURRENCIES[code]}" for code, base in KRW_TABLE.items()],
            "원화": [format_money(convert(base, code, "KRW", rates), "KRW") for code, base in KRW_TABLE.items()],
        }
    )

    # data["time_last_update_utc"] = 환율 기준 시각 (UTC) → 한국 시간으로 변환
    updated = parsedate_to_datetime(data["time_last_update_utc"]).astimezone(KST)
    col_info, col_btn = st.columns([3, 1], vertical_alignment="center")
    col_info.caption(f"기준 시각: {updated:%Y-%m-%d %H:%M} (한국 시간) · 하루 한 번 갱신  \n환율: ExchangeRate-API")
    if col_btn.button("새로 불러오기", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


if __name__ == "__main__":
    main()
