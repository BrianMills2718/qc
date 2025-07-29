"""
Setup configuration for the Qualitative Coding Analysis Tool
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="qualitative_coding",
    version="2.1.0",
    description="LLM-powered tool for analyzing qualitative research interviews with Neo4j",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Qualitative Research Team",
    author_email="research@example.com",
    packages=find_packages(where=".", include=["qc", "qc.*"]),
    python_requires=">=3.8",
    install_requires=[
        "aiosqlite>=0.17.0",
        "google-generativeai>=0.3.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "pyyaml>=5.4.0",
        "anyio>=3.0.0",
        "bleach>=6.0.0",
        "python-json-logger>=2.0.0",
        "tiktoken>=0.5.0",
        "litellm>=1.0.0",
        "python-dotenv>=0.19.0",
        "backoff>=2.2.0",
        "neo4j>=5.0.0",
        "python-docx>=0.8.11",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio>=0.15.0",
            "black>=21.0.0",
            "flake8>=3.9.0",
            "mypy>=0.910",
        ],
    },
    entry_points={
        "console_scripts": [
            "qc=qc.cli:run",
        ],
    },
    include_package_data=True,
    package_data={
        "qc": ["*.yaml", "*.yml"],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)