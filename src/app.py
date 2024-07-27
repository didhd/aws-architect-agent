import streamlit as st
from architect import run_aws_architect_agent

st.set_page_config(page_title="AWS 아키텍처 설계 도우미", page_icon="🏗️", layout="wide")

st.title("AWS 아키텍처 설계 도우미")

bedrock_models = [
    "anthropic.claude-3-sonnet-20240229-v1:0",
    "anthropic.claude-3.5-sonnet-20240229-v1:0",
    "anthropic.claude-3-haiku-20240307-v1:0",
]

if "selected_model" not in st.session_state:
    st.session_state.selected_model = bedrock_models[0]

if "user_question" not in st.session_state:
    st.session_state.user_question = ""

if "feedback" not in st.session_state:
    st.session_state.feedback = ""

if "iteration" not in st.session_state:
    st.session_state.iteration = 0

st.sidebar.title("설정")
st.session_state.selected_model = st.sidebar.selectbox(
    "Bedrock 모델 선택", bedrock_models
)

st.write(f"선택된 모델: {st.session_state.selected_model}")

# 예시 요구사항
sample_requirements = {
    "웹 애플리케이션": "고가용성 웹 애플리케이션을 위한 AWS 아키텍처를 설계해주세요. 사용자 트래픽은 변동이 심하며, 데이터베이스와 정적 자산 저장소가 필요합니다.",
    "마이크로서비스": "마이크로서비스 아키텍처를 AWS에서 구현하고 싶습니다. 서비스 간 통신, 로드 밸런싱, 그리고 컨테이너 오케스트레이션을 고려해주세요.",
    "데이터 처리 파이프라인": "대용량 데이터를 실시간으로 수집, 처리, 분석하는 파이프라인을 AWS에서 구축하고 싶습니다. 확장성과 비용 효율성을 고려해주세요.",
    "서버리스 백엔드": "모바일 앱을 위한 서버리스 백엔드 아키텍처를 설계해주세요. 사용자 인증, API 요청 처리, 그리고 데이터 저장소를 포함해야 합니다.",
    "재해 복구": "중요한 비즈니스 애플리케이션을 위한 재해 복구 솔루션을 AWS에서 구현하고 싶습니다. RPO와 RTO를 최소화하는 방안을 제시해주세요.",
}

# 예시 버튼 생성
st.markdown(
    """
    <style>
        div[data-testid="column"] {
            width: fit-content !important;
            flex: unset;
        }
        div[data-testid="column"] * {
            width: fit-content !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.write("예시 요구사항:")
cols = st.columns(len(sample_requirements))
for i, (key, value) in enumerate(sample_requirements.items()):
    if cols[i].button(key, key=f"example_{i}"):
        st.session_state.user_question = value

# 사용자 입력 텍스트 영역
user_question = st.text_area(
    "AWS 아키텍처 요구사항을 자세히 설명해주세요:",
    value=st.session_state.user_question,
    height=150,
    key="user_question",
)

if st.button("아키텍처 생성"):
    if user_question:
        progress_bar = st.progress(0)
        status_text = st.empty()
        yaml_expander = st.expander("YAML 내용", expanded=False)
        diagram_container = st.empty()
        explanation_container = st.empty()
        validation_container = st.empty()

        try:
            with st.spinner("AWS 아키텍처 생성 중..."):
                for status in run_aws_architect_agent(
                    user_question, st.session_state.selected_model
                ):
                    if "error" in status:
                        st.error(f"오류가 발생했습니다: {status['error']}")
                        if "traceback" in status:
                            st.code(status["traceback"], language="python")
                        break

                    if "yaml_content" in status:
                        with st.spinner("AWS 아키텍처 YAML 생성 중..."):
                            yaml_expander.code(status["yaml_content"], language="yaml")
                            status_text.text("AWS 아키텍처 YAML 생성 완료")
                            progress_bar.progress(0.33)

                    if "architecture_explanation" in status:
                        with st.spinner("아키텍처 설명 생성 중..."):
                            explanation_container.markdown("### 아키텍처 설명")
                            explanation_container.write(
                                status["architecture_explanation"]
                            )
                            status_text.text("아키텍처 설명 생성 완료")
                            progress_bar.progress(0.66)

                    if status.get("diagram_generated"):
                        with st.spinner("아키텍처 다이어그램 생성 중..."):
                            diagram_container.image(
                                "output.png", caption="생성된 아키텍처 다이어그램"
                            )
                            status_text.text("아키텍처 다이어그램 생성 완료")
                            progress_bar.progress(0.8)

                    if status.get("validation_result"):
                        with st.spinner("아키텍처 설계 검증 중..."):
                            validation_container.markdown(
                                "### 설계 검증 결과 및 개선 제안"
                            )
                            validation_container.write(status["validation_result"])
                            status_text.text("아키텍처 설계 검증 완료")
                            progress_bar.progress(1.0)

                status_text.text("AWS 아키텍처 설계 완료!")
        except Exception as e:
            st.error(f"오류가 발생했습니다: {str(e)}")
    else:
        st.warning("AWS 아키텍처 요구사항을 입력해주세요.")

st.sidebar.markdown("---")
st.sidebar.markdown(
    "<p class='footer'>© 2024 AWS 아키텍처 설계 도우미</p>", unsafe_allow_html=True
)
