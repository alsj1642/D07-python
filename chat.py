import os

import streamlit as st
from dotenv import load_dotenv

try:
    import openai
except ImportError:
    st.error("openai 패키지가 없어요. 터미널에서 pip install -r requirements.txt 를 실행해 주세요.")
    st.stop()

API = {
    "chat": "https://api.openai.com/v1/chat/completions",  # 🔌 OpenAI 채팅 (openai 패키지가 이 주소로 보냄)
}

MODEL = "gpt-4o-mini"
SYSTEM_PROMPT = "너는 친절한 한국어 도우미야. 초보자도 이해할 수 있게 짧고 쉽게 대답해 줘."
MAX_HISTORY = 20  # 최근 대화 20개만 보내서 비용 아끼기

MINIMAL_CSS = """
<style>
    .block-container { max-width: 720px; padding-top: 3rem; }
    h1 { font-weight: 600; letter-spacing: -0.02em; }
</style>
"""


def error_message(e):
    """OpenAI 에러를 한국어 한 줄로 바꿉니다. (키·요청 내용은 화면에 내보내지 않음)"""
    if isinstance(e, openai.AuthenticationError):
        return "OpenAI 키가 틀렸어요. .env의 OPENAI_API_KEY를 확인해 주세요."
    if isinstance(e, openai.RateLimitError):
        if getattr(e, "code", None) == "insufficient_quota":
            return "OpenAI 크레딧이 없어요. platform.openai.com 결제(Billing)를 확인해 주세요."
        return "너무 자주 불렀어요. 잠시 뒤에 다시 시도해 주세요."
    if isinstance(e, openai.NotFoundError):
        return f"{MODEL} 모델을 쓸 수 없어요. 계정에서 모델 권한을 확인해 주세요."
    if isinstance(e, openai.APITimeoutError):
        return "OpenAI 서버가 제때 대답하지 않았어요. 잠시 뒤에 다시 시도해 주세요."
    if isinstance(e, openai.APIConnectionError):
        return "OpenAI 서버에 연결하지 못했어요. 인터넷 연결을 확인해 주세요."
    if isinstance(e, openai.APIStatusError):
        return f"대답을 받지 못했어요. (응답 코드 {e.status_code})"
    return "대답을 받지 못했어요. 잠시 뒤에 다시 시도해 주세요."


def stream_answer(client, messages):
    """답을 한 조각씩 받아서 바로바로 화면에 흘려 보냅니다."""
    stream = client.chat.completions.create(  # 🔌 API 호출
        model=MODEL,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages[-MAX_HISTORY:],
        stream=True,
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:  # chunk.choices[0].delta.content = 새로 온 글자 조각
            yield chunk.choices[0].delta.content


def main():
    st.set_page_config(page_title="챗봇", page_icon="💬", layout="centered")
    st.markdown(MINIMAL_CSS, unsafe_allow_html=True)

    col_title, col_btn = st.columns([4, 1], vertical_alignment="center")
    col_title.title("챗봇")
    if col_btn.button("새 대화", use_container_width=True):
        st.session_state.messages = []

    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error(".env에 OPENAI_API_KEY가 없어요. .env.example을 보고 채워 주세요.")
        st.stop()

    client = openai.OpenAI(api_key=api_key, timeout=30)

    # 지금까지 대화는 session_state에 저장 (Streamlit은 입력할 때마다 파일 전체를 다시 실행)
    st.session_state.setdefault("messages", [])
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    question = st.chat_input("무엇이든 물어보세요")
    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            try:
                answer = st.write_stream(stream_answer(client, st.session_state.messages))
            except openai.OpenAIError as e:
                st.error(error_message(e))
                st.session_state.messages.pop()  # 실패한 질문은 기록에서 빼기
                st.stop()
        st.session_state.messages.append({"role": "assistant", "content": answer})

    st.caption(f"모델: OpenAI {MODEL} · AI 답변은 틀릴 수 있어요")


if __name__ == "__main__":
    main()
