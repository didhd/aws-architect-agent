import streamlit as st
from architect import run_aws_architect_agent, AIMessage
import asyncio
import re
import yaml

st.set_page_config(page_title="AWS 아키텍처 설계 도우미", page_icon="🏗️", layout="wide")

st.markdown(
    """
<style>
    .main-header {font-size: 2.5rem; color: #FF9900; text-align: center; margin-bottom: 2rem;}
    .subheader {font-size: 1.5rem; color: #232F3E; margin-top: 2rem; margin-bottom: 1rem;}
    .info-box {background-color: #F7F7F7; padding: 1rem; border-radius: 10px; border-left: 5px solid #FF9900;}
    .footer {text-align: center; color: #666; font-size: 0.8rem;}
    .sample-button {margin-right: 10px; margin-bottom: 10px;}
    .context-box {background-color: #E6F3FF; padding: 1rem; border-radius: 10px; border-left: 5px solid #0066CC; margin-bottom: 1rem;}
    .log-box {background-color: #F0F0F0; padding: 1rem; border-radius: 10px; font-family: monospace; white-space: pre-wrap; overflow-x: auto;}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    "<h1 class='main-header'>AWS 아키텍처 설계 도우미</h1>", unsafe_allow_html=True
)

bedrock_models = [
    "anthropic.claude-3-sonnet-20240229-v1:0",
    "anthropic.claude-3.5-sonnet-20240229-v1:0",
    "amazon.titan-tg1-ultra-20240229-v1:0",
]
selected_model = st.sidebar.selectbox("Select a Bedrock Model", bedrock_models)

sample_requirements = {
    "웹 애플리케이션": "고가용성 웹 애플리케이션을 위한 AWS 아키텍처를 설계해주세요. 사용자 트래픽은 변동이 심하며, 데이터베이스와 정적 자산 저장소가 필요합니다.",
    "마이크로서비스": "마이크로서비스 아키텍처를 AWS에서 구현하고 싶습니다. 서비스 간 통신, 로드 밸런싱, 그리고 컨테이너 오케스트레이션을 고려해주세요.",
    "데이터 처리 파이프라인": "대용량 데이터를 실시간으로 수집, 처리, 분석하는 파이프라인을 AWS에서 구축하고 싶습니다. 확장성과 비용 효율성을 고려해주세요.",
    "서버리스 백엔드": "모바일 앱을 위한 서버리스 백엔드 아키텍처를 설계해주세요. 사용자 인증, API 요청 처리, 그리고 데이터 저장소를 포함해야 합니다.",
    "재해 복구": "중요한 비즈니스 애플리케이션을 위한 재해 복구 솔루션을 AWS에서 구현하고 싶습니다. RPO와 RTO를 최소화하는 방안을 제시해주세요.",
}

st.markdown("<h2 class='subheader'>예시 요구사항</h2>", unsafe_allow_html=True)
st.markdown("아래 버튼을 클릭하여 예시 요구사항을 입력란에 채울 수 있습니다:")

cols = st.columns(len(sample_requirements))
for i, (key, value) in enumerate(sample_requirements.items()):
    with cols[i]:
        if st.button(key, key=f"sample_button_{i}", help=value):
            st.session_state.user_question = value

st.markdown(
    "<h2 class='subheader'>AWS 아키텍처 요구사항 설명</h2>", unsafe_allow_html=True
)
user_question = st.text_area(
    "여기에 AWS 아키텍처 요구사항을 자세히 설명해주세요:",
    value=st.session_state.get("user_question", ""),
    height=150,
    key="user_input",
)

# Placeholders for results
status_text = st.empty()
context_placeholder = st.empty()
diagram_placeholder = st.empty()
details_placeholder = st.empty()


def handle_architecture_result(status):
    if "error" in status:
        st.error(f"오류가 발생했습니다: {status['error']}")
        return

    if "context" in status:
        context_placeholder.markdown(
            f"<div class='context-box'>{status['context']}</div>",
            unsafe_allow_html=True,
        )

    if "yaml_content" in status:
        with st.expander("중간 결과 (YAML)", expanded=False):
            st.code(status["yaml_content"], language="yaml")

    if "bedrock_response" in status:
        with st.expander("Bedrock 응답", expanded=False):
            st.code(status["bedrock_response"])

    if "messages" in status:
        messages = status["messages"]
        if messages:
            last_message = messages[-1]
            if isinstance(last_message, AIMessage):
                with st.expander("생성된 결과", expanded=False):
                    st.markdown(
                        f"<div class='info-box'>{last_message.content}</div>",
                        unsafe_allow_html=True,
                    )

                if "성공적으로 생성되었습니다" in last_message.content:
                    match = re.search(r"생성되었습니다: (.+)", last_message.content)
                    if match:
                        image_file = match.group(1)
                        diagram_placeholder.image(image_file)
                    else:
                        st.warning("다이어그램 파일을 찾을 수 없습니다.")


async def process_architecture(user_question, model_id):
    i = 0
    async for status in run_aws_architect_agent(user_question, model_id):
        i += 1
        status_text.text(f"진행 중... {int((i / 2) * 100)}%")
        handle_architecture_result(status)

    status_text.text("완료!")

    # 최종 결과 표시
    final_status = status
    if "messages" in final_status:
        final_message = final_status["messages"][-1]
        if isinstance(final_message, AIMessage):
            details_placeholder.markdown(
                f"<div class='info-box'>{final_message.content}</div>",
                unsafe_allow_html=True,
            )


def start_architecture_creation():
    if user_question:
        with st.spinner("아키텍처 생성 중..."):
            asyncio.run(process_architecture(user_question, selected_model))
    else:
        st.warning("AWS 아키텍처 요구사항을 입력해주세요.")


if st.button("아키텍처 생성", key="generate_button"):
    start_architecture_creation()

st.sidebar.markdown("<h2 class='subheader'>프로젝트 소개</h2>", unsafe_allow_html=True)
st.sidebar.markdown(
    "<div class='info-box'>"
    "이 앱은 LangGraph, ChatGPT, 그리고 diagram-as-code를 사용하여 "
    "사용자의 요구사항에 기반한 AWS 아키텍처 다이어그램을 생성합니다. "
    "아키텍처 요구사항을 설명하면 AI가 적합한 다이어그램을 생성해 드립니다."
    "</div>",
    unsafe_allow_html=True,
)

st.sidebar.markdown("<h2 class='subheader'>사용 방법</h2>", unsafe_allow_html=True)
st.sidebar.markdown(
    "<div class='info-box'>"
    "1. 예시 요구사항 중 하나를 선택하거나 직접 요구사항을 작성합니다.<br>"
    "2. '아키텍처 생성' 버튼을 클릭합니다.<br>"
    "3. 생성된 YAML과 다이어그램을 확인합니다.<br>"
    "4. 필요에 따라 요구사항을 수정하고 다시 생성합니다."
    "</div>",
    unsafe_allow_html=True,
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "<p class='footer'>© 2024 AWS 아키텍처 설계 도우미</p>", unsafe_allow_html=True
)
