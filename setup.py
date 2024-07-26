from setuptools import setup, find_packages

with open("requirements.txt") as f:
    required = f.read().splitlines()

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="aws-architect-agent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=required,
    entry_points={
        "console_scripts": [
            "aws-architect=src.main:main",
        ],
    },
    author="Sanghwa Na",
    author_email="sanghwa@amazon.com",
    description="An AWS architecture diagram generator using LangGraph and ChatGPT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/didhd/aws-architect-agent",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
