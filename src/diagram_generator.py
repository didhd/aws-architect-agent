import subprocess
import os
import tempfile


def generate_diagram(yaml_content: str) -> str:
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

        # 파일이 실제로 생성되었는지 확인
        if os.path.exists(output_file):
            return f"다이어그램이 성공적으로 생성되었습니다: {output_file}"
        else:
            return (
                f"다이어그램 파일이 생성되지 않았습니다. awsdac 출력: {result.stdout}"
            )

    except subprocess.CalledProcessError as e:
        return f"다이어그램 생성 중 오류 발생: {e.stderr}"
    finally:
        # 임시 파일 삭제
        os.unlink(temp_file_path)
