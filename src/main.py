import os
from architect import run_aws_architect_agent

# OpenAI API 키 설정 (실제 환경에서는 환경 변수로 관리해야 합니다)
os.environ["OPENAI_API_KEY"] = "your-api-key-here"

if __name__ == "__main__":
    question = "S3에서 Athena SQL을 통해 데이터를 가져와 Bedrock Titan 임베딩을 적용하는 과정에서 시간이 오래 걸리고 타임아웃 에러가 발생하는데, 이를 해결할 수 있는 최적의 아키텍처를 가이드해주세요."
    messages = run_aws_architect_agent(question)
    for message in messages:
        print(f"{message.type}: {message.content}\n")
    