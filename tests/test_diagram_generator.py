import unittest
from src.diagram_generator import generate_diagram


class TestDiagramGenerator(unittest.TestCase):
    def test_generate_diagram(self):
        yaml_content = """
Diagram:
  DefinitionFiles:
    - Type: URL
      Url: "https://raw.githubusercontent.com/awslabs/diagram-as-code/main/definitions/definition-for-aws-icons-light.yaml"
  Resources:
    Canvas:
      Type: AWS::Diagram::Canvas
      Children:
        - S3Bucket
    S3Bucket:
      Type: AWS::S3::Bucket
      Title: "Test Bucket"
"""
        result = generate_diagram(yaml_content)
        self.assertIn("다이어그램이 성공적으로 생성되었습니다", result)


if __name__ == "__main__":
    unittest.main()
