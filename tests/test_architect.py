import unittest
from src.architect import generate_yaml, run_aws_architect_agent


class TestArchitect(unittest.TestCase):
    def test_generate_yaml(self):
        question = "간단한 S3 버킷 아키텍처를 설계해주세요."
        yaml_content = generate_yaml(question)
        self.assertIn("AWS::S3::Bucket", yaml_content)

    def test_run_aws_architect_agent(self):
        question = "EC2 인스턴스와 RDS 데이터베이스를 연결하는 아키텍처를 설계해주세요."
        messages = run_aws_architect_agent(question)
        self.assertTrue(len(messages) > 1)
        self.assertIn("AWS::EC2::Instance", messages[-2].content)
        self.assertIn("AWS::RDS::DBInstance", messages[-2].content)


if __name__ == "__main__":
    unittest.main()
