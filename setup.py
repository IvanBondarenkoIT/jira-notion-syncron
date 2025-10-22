"""Setup configuration."""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="jira-notion-syncron",
    version="0.1.0",
    author="Your Team",
    author_email="team@company.com",
    description="Enterprise-grade synchronization system for Jira, Notion, and various data sources",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/jira-notion-syncron",
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business :: Groupware",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "jira-notion-sync=src.presentation.cli.main:cli",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)

