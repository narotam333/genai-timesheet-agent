from setuptools import setup, find_packages

setup(
    name="tempo_timesheet_entry",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "streamlit",
        "langchain",
        "langchain_core",
        "langchain-google-genai",
        "langgraph",
        "python-dotenv",
        "requests",
        "pydantic",
        "dateparser"
    ],
    entry_points={
        'console_scripts': [
            'tempo_timesheet_app=timesheet_entry.launch_app:main'
        ],
    },
    include_package_data=True,
    description="Streamlit app to log time to JIRA Tempo using LLM",
    author="Narotam Aggarwal",
    author_email="naroram333@gmail.com",
    url="https://github.com/narotam333/timesheet_entry",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)

