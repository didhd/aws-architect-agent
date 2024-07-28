import os
import subprocess
import logging
import re
import base64
import traceback
from typing import Annotated, Generator, TypedDict, Dict
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage
from langgraph.graph import StateGraph, Graph, START, END
from diagram_generator import generate_diagram
import boto3
from langchain_aws import ChatBedrock

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class State(TypedDict):
    messages: Annotated[list[BaseMessage], "The conversation history"]
    yaml_content: Annotated[str, "The generated YAML content"]
    architecture_explanation: Annotated[str, "Explanation of the architecture"]
    diagram_generated: Annotated[bool, "Whether the diagram has been generated"]
    validation_result: Annotated[str, "Result of the validation"]
    iteration_count: Annotated[int, "Number of iterations"]
    architecture_score: Annotated[float, "Score of the current architecture (0-100)"]
    current_node: Annotated[str, "Current node in the workflow"]
    next_node: Annotated[str, "Next node to be executed"]
    context: Annotated[dict, "Additional context information"]


bedrock_runtime = boto3.client("bedrock-runtime", region_name="us-west-2")


def create_llm(model_id: str):
    return ChatBedrock(
        model_id=model_id,
        client=bedrock_runtime,
        model_kwargs={"temperature": 0.7, "max_tokens": 32768},
    )


with open("diagram_as_code.yaml", "r") as file:
    diagram_as_code_example = file.read()


def extract_yaml(content: str) -> str:
    match = re.search(r"<DIAGRAM>(.*?)</DIAGRAM>", content, re.DOTALL)
    if match:
        yaml_content = match.group(1).strip()
        return yaml_content
    return ""


def check_warn_messages(yaml_content: str) -> bool:
    if not yaml_content:
        return False
    with open("temp_architecture.yaml", "w") as f:
        f.write(yaml_content)
    result = subprocess.run(
        ["awsdac", "temp_architecture.yaml"], capture_output=True, text=True
    )
    return "WARN" not in result.stdout


def architect_node(state: State) -> State:
    logger.info("Executing architect node")
    messages = state["messages"]
    llm = create_llm(state["context"]["model_id"])
    try:
        previous_validation = state.get("previous_validation", "")
        previous_score = state.get("previous_score", 0)

        prompt = f"""당신은 AWS Solutions Architect입니다. 주어진 요구사항에 대해 최적의 AWS 아키텍처를 설계하고, 
        diagram-as-code YAML 형식으로 답변해야 합니다.
        
        요구사항: {messages[-1].content}
        
        이전 검증 결과: {previous_validation}
        이전 점수: {previous_score}
        
        위의 검증 결과와 점수를 참고하여 아키텍처를 개선해주세요. 특히 이전 검증 결과가 있다면 누락된 구성 요소를 추가하고, 연결이 부자연스러운 부분을 수정해주세요.
        
        응답 예시:
        <DIAGRAM>
        {diagram_as_code_example}
        </DIAGRAM>
        
        설명:
        [여기에 아키텍처 설명 작성]
        """

        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content

        yaml_content = extract_yaml(content)
        if not check_warn_messages(yaml_content):
            raise ValueError("Invalid YAML generated")

        explanation_match = re.search(r"설명:(.*?)$", content, re.DOTALL)
        explanation = explanation_match.group(1).strip() if explanation_match else ""

        state["yaml_content"] = yaml_content
        state["architecture_explanation"] = explanation
        state["current_node"] = "Architect"
        state["next_node"] = "Diagram"

        logger.info("Architect node execution successful")
        return state
    except Exception as e:
        logger.error(f"Architect node execution failed: {str(e)}")
        state["next_node"] = "FINISH"
        return state


def diagram_node(state: State) -> State:
    logger.info("Executing diagram node")
    try:
        yaml_content = state["yaml_content"]
        diagram_result = generate_diagram(yaml_content)

        if diagram_result["success"]:
            state["diagram_generated"] = True
            state["diagram_feedback"] = diagram_result["feedback"]
            logger.info(
                f"Diagram node execution successful: {diagram_result['message']}"
            )
        else:
            state["diagram_generated"] = False
            state["diagram_feedback"] = None
            logger.error(f"Diagram generation failed: {diagram_result['message']}")

        state["current_node"] = "Diagram"
        state["next_node"] = "Validate"
        return state
    except Exception as e:
        logger.error(f"Diagram node execution failed: {str(e)}")
        state["next_node"] = "FINISH"
        return state


def validate_node(state: State) -> State:
    logger.info("Executing validate node")
    try:
        llm = create_llm(state["context"]["model_id"])
        with open("output.png", "rb") as image_file:
            image_data = image_file.read()
            image_base64 = base64.b64encode(image_data).decode("utf-8")

        diagram_feedback = state.get("diagram_feedback", {})
        warnings = "\n".join(diagram_feedback.get("warnings", []))
        errors = "\n".join(diagram_feedback.get("errors", []))
        suggestions = "\n".join(diagram_feedback.get("suggestions", []))

        prompt = f"""다음 YAML로 표현된 AWS 아키텍처와 생성된 다이어그램(output.png)을 검증해주세요. 기준점은 설명입니다.
        그림을 보며 선이 연결된 부분이 자연스러운지, 아키텍처가 요구사항을 충족하는지 확인해주세요. 1)부자연스러운 선이 있을때마다 5점씩, 2)설명에는 있으나 그림에는 빠진 요소가 있을때마다 10점씩 감점해야합니다.
        
        YAML:
        {state['yaml_content']}
        
        설명:
        {state['architecture_explanation']}

        다이어그램 생성 중 발생한 경고:
        {warnings}

        다이어그램 생성 중 발생한 오류:
        {errors}

        다이어그램 개선 제안:
        {suggestions}

        위의 정보를 고려하여 아키텍처를 평가하고, 개선이 필요한 부분을 지적해주세요.
        검증 결과와 점수를 작성해주세요. 
        
        응답 예시:
        <검증결과>[검증 결과]</검증결과>

        <점수>[0-100 사이의 점수]</점수>
        """
        response = llm.invoke(
            [
                HumanMessage(
                    content=[
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"
                            },
                        },
                    ]
                )
            ]
        )
        validation_result = response.content

        score_match = re.search(r"<점수>(\d+)</점수>", validation_result)
        score = float(score_match.group(1)) if score_match else 0

        state["validation_result"] = validation_result
        state["architecture_score"] = score
        state["current_node"] = "Validate"
        state["next_node"] = "supervisor"
        logger.info(f"Validate node execution successful: {validation_result}")
        return state
    except Exception as e:
        logger.error(f"Validate node execution failed: {str(e)}")
        state["next_node"] = "FINISH"
        return state


def supervisor_node(state: State) -> State:
    logger.info(f"Executing supervisor node. Current state: {state['current_node']}")
    try:
        state["iteration_count"] = state.get("iteration_count", 0) + 1
        logger.info(f"Iteration count: {state['iteration_count']}")

        if state["iteration_count"] >= 25:
            logger.warning("Reached maximum iteration count. Finishing.")
            state["next_node"] = "FINISH"
        elif state["current_node"] == "supervisor" and not state["yaml_content"]:
            logger.info("Initial state or no YAML content. Moving to Architect node.")
            state["next_node"] = "Architect"
        elif state["current_node"] == "Architect" and state["yaml_content"]:
            logger.info("YAML content generated. Moving to Diagram node.")
            state["next_node"] = "Diagram"
        elif state["current_node"] == "Diagram" and state["diagram_generated"]:
            logger.info("Diagram generated. Moving to Validate node.")
            state["next_node"] = "Validate"
        elif state["current_node"] == "Validate" and state["validation_result"]:
            if state["architecture_score"] >= 90:
                logger.info("Architecture is satisfactory and validated. Finishing.")
                state["next_node"] = "FINISH"
            else:
                logger.info("Starting new architecture design cycle.")
                state["previous_validation"] = state["validation_result"]
                state["previous_score"] = state["architecture_score"]
                state["yaml_content"] = ""
                state["diagram_generated"] = False
                state["validation_result"] = ""
                state["architecture_score"] = 0
                state["next_node"] = "Architect"
        else:
            logger.warning(
                f"Unexpected state: {state['current_node']}. Moving to Architect node."
            )
            state["next_node"] = "Architect"

        logger.info(f"Supervisor decision: Next node is {state['next_node']}")
        return state
    except Exception as e:
        logger.error(f"Supervisor node execution failed: {str(e)}")
        state["next_node"] = "FINISH"
        return state


def create_workflow(model_id: str):
    workflow = StateGraph(State)

    workflow.add_node("Architect", architect_node)
    workflow.add_node("Diagram", diagram_node)
    workflow.add_node("Validate", validate_node)
    workflow.add_node("supervisor", supervisor_node)

    members = ["Architect", "Diagram", "Validate"]

    for member in members:
        workflow.add_edge(member, "supervisor")

    conditional_map = {k: k for k in members}
    conditional_map["FINISH"] = END
    workflow.add_conditional_edges(
        "supervisor", lambda state: state["next_node"], conditional_map
    )

    workflow.set_entry_point("supervisor")

    graph = workflow.compile()

    os.makedirs("assets", exist_ok=True)
    png_data = graph.get_graph(xray=True).draw_mermaid_png()
    with open("assets/graph.png", "wb") as f:
        f.write(png_data)

    return graph


def run_aws_architect_agent(
    question: str, model_id: str
) -> Generator[Dict, None, None]:
    logger.info(f"Running AWS Architect Agent with question: {question}")

    graph = create_workflow(model_id)
    initial_state = State(
        messages=[
            SystemMessage(
                content=f"당신은 AWS Solutions Architect입니다. 고객의 질문에 대해 최적의 AWS 아키텍처를 설계하고, diagram-as-code YAML 형식으로 답변해야 합니다. YAML DIAGRAM은 Markdown 없이 <DIAGRAM> </DIAGRAM> 태그로 감싸주세요."
            ),
            HumanMessage(content=question),
        ],
        yaml_content="",
        bedrock_response="",
        context={"model_id": model_id},
        current_node="supervisor",
        next_node="supervisor",
        architecture_explanation="",
        diagram_generated=False,
        validation_result="",
        iteration_count=0,
        architecture_score=0,
    )

    try:
        for output in graph.stream(initial_state):
            logger.debug(f"Graph output: {output}")

            if isinstance(output, dict) and len(output) == 1:
                node_name, state = next(iter(output.items()))
            else:
                raise ValueError(f"Unexpected output format: {output}")

            current_node = state.get("current_node")
            if current_node is None:
                raise ValueError(f"current_node not found in state: {state}")

            logger.info(f"Current node: {current_node}")

            if current_node == "Architect":
                yield {
                    "yaml_content": state["yaml_content"],
                    "architecture_explanation": state["architecture_explanation"],
                }
            elif current_node == "Diagram":
                yield {"diagram_generated": state["diagram_generated"]}
            elif current_node == "Validate":
                yield {"validation_result": state["validation_result"]}
            elif current_node == "supervisor":
                next_node = state["next_node"]
                logger.info(f"Supervisor decision: Next node is {next_node}")

            if state["next_node"] == "FINISH":
                logger.info("Workflow completed")
                break

    except Exception as e:
        logger.error(f"Error occurred in run_aws_architect_agent: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        yield {"error": str(e), "traceback": traceback.format_exc()}
