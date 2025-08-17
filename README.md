# Jira Time-Tracking Assistant

A Streamlit web app that uses Google Gemini LLM and Langchain tools to help you log time effortlessly into Jira Tempo.  
Simply describe your time logs in natural language, and the AI assistant will update Jira issues accordingly.

---

## Features

- Natural language time tracking for Jira issues  
- Supports default issue key fallback if none specified  
- Integrates with Jira Tempo REST API for logging work hours  
- Interactive web UI built with Streamlit  
- Powered by Google Gemini 2.5 Flash LLM via `langchain-google-genai`  
- Extensible via Langchain tool framework  

---

## Getting Started

### Prerequisites

- Python 3.8+  
- [Jira Cloud](https://www.atlassian.com/software/jira) account with Tempo plugin  
- API tokens for Jira and Tempo  
- Google Cloud Generative AI API access  

### Installation

1. Clone this repo:

```bash
git clone https://github.com/narotam333/genai-timesheet-agent.git
cd <root folder>

2. Create and activate a Python virtual environment:

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

3. Install dependencies:

pip install -r requirements.txt

4. Create a .env file in the root directory and add your credentials:

JIRA_EMAIL=your_jira_email@example.com
JIRA_TOKEN=your_jira_api_token
TEMPO_TOKEN=your_tempo_api_token
JIRA_DOMAIN=https://your-domain.atlassian.net
GOOGLE_API_KEY=your_google_cloud_api_key

5. Usage:

5a. Packaging and CLI usage

pip install -e .
tempo_timesheet_app # launches Streamlit app in the browser

OR

5b. Run the Streamlit app:

streamlit run timesheet_entry/streamlit_app.py
python -m streamlit run timesheet_entry/streamlit_app.py # if above doesn't work

Open your browser at http://localhost:8501 and enter natural language commands like:
Log 7.5 hours to all in-progress issues for this full week.

The assistant will interpret your request and log time accordingly.
