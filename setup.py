from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="agent-comms-mvp",
    version="0.1.0",
    author="Bluelabel Team",
    author_email="team@bluelabel.dev",
    description="Multi-agent communication framework for Bluelabel OS",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/amuslera/agent-comms-mvp",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pydantic>=2.0.0",
        "pyyaml>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "run-plan=tools.run_plan:main",
            "generate-summary=tools.generate_execution_summary:main",
            "inbox-monitor=tools.inbox_monitor:main",
            "task-status=tools.task_status_tracker:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.9",
)
