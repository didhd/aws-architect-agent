import subprocess
import os
import tempfile


def generate_diagram(yaml_content: str) -> dict:
    # 임시 파일 생성
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as temp_file:
        temp_file.write(yaml_content)
        temp_file_path = temp_file.name

    try:
        # awsdac 명령어 실행
        result = subprocess.run(
            ["awsdac", temp_file_path], capture_output=True, text=True, check=True
        )

        # 출력 파일 이름 확인 (기본값은 output.png)
        output_file = "output.png"
        feedback = analyze_diagram_output(result.stderr)

        # 파일이 실제로 생성되었는지 확인
        if os.path.exists(output_file):
            return {
                "success": True,
                "message": f"다이어그램이 성공적으로 생성되었습니다 stdout: {result.stdout}, stderr: {result.stderr}",
                "feedback": feedback,
            }
        else:
            return {
                "success": False,
                "message": f"다이어그램 파일이 생성되지 않았습니다. stdout: {result.stdout}, stderr: {result.stderr}",
                "feedback": feedback,
            }

    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "message": f"다이어그램 생성 중 오류 발생: {e.stderr}",
            "feedback": None,
        }
    finally:
        # 임시 파일 삭제
        os.unlink(temp_file_path)


def analyze_diagram_output(output: str) -> dict:
    feedback = {"warnings": [], "errors": [], "suggestions": []}

    for line in output.split("\n"):
        if "WARN" in line:
            feedback["warnings"].append(line)
        elif "ERROR" in line:
            feedback["errors"].append(line)
        elif "consider" in line.lower() or "suggest" in line.lower():
            feedback["suggestions"].append(line)

    return feedback
