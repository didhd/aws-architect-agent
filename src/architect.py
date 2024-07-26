import asyncio
from typing import Annotated, AsyncGenerator
from langchain_core.messages import BaseMessage, AIMessage
from langgraph.graph import Graph, START
from langchain_aws import ChatBedrock
from langchain.schema import HumanMessage, SystemMessage
from diagram_generator import generate_diagram
import boto3
from typing_extensions import TypedDict
import logging
import time
import re
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class State(TypedDict):
    messages: Annotated[list, BaseMessage]
    yaml_content: str
    bedrock_response: str
    context: dict


bedrock_runtime = boto3.client("bedrock-runtime", region_name="us-west-2")


def create_llm(model_id: str):
    return ChatBedrock(
        model_id=model_id,
        client=bedrock_runtime,
        model_kwargs={"temperature": 0.7, "max_tokens": 2000},
    )


# Load the diagram_as_code.yaml file
with open("diagram_as_code.yaml", "r") as file:
    diagram_as_code_example = file.read()

system_message = SystemMessage(
    content=f"당신은 AWS Solutions Architect입니다. 고객의 질문에 대해 최적의 AWS 아키텍처를 설계하고, diagram-as-code YAML 형식으로 답변해야 합니다. YAML은 <YAML> </YAML> 태그로 감싸주세요. 예시: <YAML>\n{diagram_as_code_example}\n</YAML>"
)


async def generate_yaml(messages: list[BaseMessage], llm) -> str:
    start_time = time.time()
    logger.info(f"Generating YAML for messages")

    response = await llm.ainvoke(messages)
    yaml_content = response.content

    match = re.search(r"<YAML>(.*?)</YAML>", yaml_content, re.DOTALL)
    if match:
        yaml_content = match.group(1).strip()

    end_time = time.time()
    latency = end_time - start_time
    logger.info(f"Generated YAML (latency: {latency:.2f}s)")

    return yaml_content


async def architect_node(state: State) -> State:
    start_time = time.time()
    logger.info("Executing architect node")
    messages = state["messages"]

    if not any(isinstance(msg, SystemMessage) for msg in messages):
        messages.insert(0, system_message)

    llm = create_llm(state["context"]["model_id"])
    yaml_content = await generate_yaml(messages, llm)
    state["messages"].append(AIMessage(content=yaml_content))
    state["yaml_content"] = yaml_content
    state["bedrock_response"] = str(await llm.ainvoke(messages))

    state["context"]["current_node"] = "architect"
    end_time = time.time()
    execution_time = end_time - start_time
    logger.info(f"Architect node execution time: {execution_time:.2f}s")
    return state


async def diagram_node(state: State) -> State:
    start_time = time.time()
    logger.info("Executing diagram node")
    yaml_content = state["yaml_content"]
    diagram_result = generate_diagram(yaml_content)
    state["messages"].append(AIMessage(content=diagram_result))
    state["context"]["current_node"] = "diagram"
    end_time = time.time()
    execution_time = end_time - start_time
    logger.info(f"Diagram node execution time: {execution_time:.2f}s")
    return state


workflow = Graph()

workflow.add_node("architect", architect_node)
workflow.add_node("diagram", diagram_node)

workflow.add_edge(START, "architect")
workflow.add_edge("architect", "diagram")

chain = workflow.compile()


async def run_aws_architect_agent(
    question: str, model_id: str
) -> AsyncGenerator[dict, None]:
    logger.info(f"Running AWS Architect Agent with question: {question}")
    initial_state = State(
        messages=[HumanMessage(content=question)],
        yaml_content="",
        bedrock_response="",
        context={"model_id": model_id},
    )

    try:
        state = initial_state
        for node in ["architect", "diagram"]:
            if node == "architect":
                state = await architect_node(state)
            else:
                state = await diagram_node(state)
            yield {
                "messages": state["messages"],
                "yaml_content": state.get("yaml_content", ""),
                "bedrock_response": state.get("bedrock_response", ""),
                "context": state.get("context", {}),
            }
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        yield {"error": str(e)}
