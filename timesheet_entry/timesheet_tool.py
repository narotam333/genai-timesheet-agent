#!/usr/bin/env python
# coding: utf-8

# In[7]:


import os                         # For accessing environment variables
import getpass                    # (Optional) For secure password input in interactive sessions
import requests                   # For making HTTP requests (e.g., to APIs)
from typing import List, Optional       # For optional type hints
from datetime import datetime, timedelta
import dateparser

# Load environment variables from a .env file
from dotenv import load_dotenv

# LangChain tool base classes for defining custom tools
from langchain.tools import Tool, BaseTool

# For handling callbacks during tool execution (logging, streaming, etc.)
from langchain.callbacks.manager import CallbackManagerForToolRun

# Used to define structured inputs and validation for tools
from pydantic import Field


# In[8]:


# Load environment variables from .env file
load_dotenv()

# Setup API Keys
if not os.environ.get("GOOGLE_API_KEY"):
  os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter API key for Google Gemini: ")
if not os.environ.get("JIRA_DOMAIN"):
  os.environ["JIRA_DOMAIN"] = getpass.getpass("Enter JIRA domain: ")
if not os.environ.get("JIRA_EMAIL"):
  os.environ["JIRA_EMAIL"] = getpass.getpass("Enter JIRA email: ")
if not os.environ.get("JIRA_TOKEN"):
  os.environ["JIRA_TOKEN"] = getpass.getpass("Enter JIRA token: ")
if not os.environ.get("TEMPO_TOKEN"):
  os.environ["TEMPO_TOKEN"] = getpass.getpass("Enter TEMPO token: ")


# In[9]:


class LogTimeToTempoTool(BaseTool):
    """
    A LangChain-compatible tool for logging work hours to Tempo Timesheets 
    using the JIRA and Tempo APIs.

    This tool:
    1. Retrieves the current user's JIRA account ID using the JIRA REST API.
    2. Fetches the JIRA issue details (such as the internal issue ID) using the issue key.
    3. Submits a worklog entry to Tempo Timesheets for the specified issue.

    Attributes:
        name (str): The tool name used by LangChain.
        description (str): Human-readable summary of the tool's purpose.
        jira_email (str): JIRA account email address used for API authentication.
        jira_token (str): JIRA API token for basic authentication.
        tempo_token (str): Tempo API bearer token for worklog creation.
        jira_domain (str): Base domain for the JIRA instance 
            (e.g., "your-domain.atlassian.net"). The trailing slash is removed.

    Args for _run():
        time_seconds (int): Number of seconds to log.
        issue_key (Optional[str]): Optional; JIRA issue key (e.g., "ABC-123"); Required only in manual mode; default to MGAP-X.
        description (Optional[str]): Optional; Description or comment for the worklog entry; default value will be "work".    
        work_date (Optional[str]): Optional; Specific date in YYYY-MM-DD or natural language (e.g., "yesterday").
        date_range (Optional[str]): Optional; Natural language date range, like "this week", "last week", or "next Monday".
        work_start (Optional[str]): Optional; Start time in HH:MM:SS format; default value is "09:00:00".

    Methods:
    resolve_dates(work_date: Optional[str], date_range: Optional[str]) -> List[str]
        Parses a specific date or natural language range into a list of work dates in 'YYYY-MM-DD' format.

    get_account_id() -> str
        Retrieves the Jira account ID for the currently authenticated user.

    log_manual(issue_key, time_seconds, work_date, account_id, work_start="09:00:00", description="work") -> str
        Logs a specific number of seconds to a given Jira issue for a given date and time.

    log_auto_for_date(work_date, account_id, total_hours, work_start="09:00:00", description="work") -> str
        Distributes total work hours evenly across all in-progress Jira issues for a given date.

    post_worklog(issue_key, issue_id, time_seconds, work_date, work_start, description, account_id) -> str
        Posts a single worklog entry to the Tempo API with the specified parameters.


    Returns:
        str: Success message if the time entry is logged successfully, or an error message otherwise.

    Workflow:
        1. Calls GET /rest/api/3/myself to retrieve the account ID for the authenticated JIRA user.
        2. Calls GET /rest/api/3/issue/{issueKey} to retrieve the issue's internal ID.
        3. Sends a POST https://api.tempo.io/4/worklogs request with:
            - Issue key and ID
            - Time spent in seconds
            - Work date and start time
            - Description
            - Author account ID
            - Optional time booking category
        4. Returns a message indicating whether the operation succeeded or failed.

    Exceptions:
        Any exception during HTTP requests or JSON parsing is caught and returned as an error message.
    """
    name: str = "log_time_to_tempo"
    description: str = "Log time to Tempo Timesheets using JIRA and Tempo API."
    jira_email: str = Field(..., description="JIRA account email")
    jira_token: str = Field(..., description="JIRA API token")
    tempo_token: str = Field(..., description="Tempo API token")
    jira_domain: str = Field(..., description="JIRA domain, e.g., your-domain.atlassian.net")


    def _run(
        self,
        time_seconds: int,
        issue_key: Optional[str] = "MGAP-X",
        description: Optional[str] = "Work log entry",
        work_date: Optional[str] = None,
        date_range: Optional[str] = None,
        work_start: Optional[str] = "09:00:00",
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        print(f"LLM input: work_date={work_date}, date_range={date_range}")

        try:
            # Step 1: Resolve work dates
            dates_to_log = self.resolve_dates(work_date, date_range)

            # Step 2: Get account ID (once)
            account_id = self.get_account_id()

            # Step 3: Mode handling (auto or manual)
            results = []
            for date in dates_to_log:
                if issue_key != "MGAP-X":
                    print("In manual mode...")
                    print("Values:", issue_key, time_seconds, date, work_start, description, account_id)
                    result = self.log_manual(issue_key, 
                                             time_seconds, 
                                             date, 
                                             account_id,
                                             work_start, 
                                             description)
                else:
                    print("In auto mode...")
                    print("Values:", date, account_id, time_seconds, work_start, description)
                    total_hours = time_seconds / 3600
                    if not total_hours:
                        return "total_hours is required in auto_from_jira mode."
                    result = self.log_auto_for_date(date, 
                                                    account_id, 
                                                    total_hours,
                                                    work_start, 
                                                    description)
                results.append(f"{date}: {result}")

            return "\n".join(results)

        except Exception as e:
            return f"Exception occurred: {str(e)}"

    # --- Utility Methods ---

    def resolve_dates(self, work_date: Optional[str], date_range: Optional[str]) -> List[str]:
        today = datetime.today()
        dates = []

        if date_range:
            date_range_lower = date_range.lower().replace("_", " ").strip()

            if date_range_lower in("this_week", "this week"):
                start = today - timedelta(days=today.weekday())  # Monday
                for i in range(5):  # Mon to Fri
                    dates.append((start + timedelta(days=i)).strftime('%Y-%m-%d'))

            elif date_range_lower in("full_week" or "full week"):
                start = today - timedelta(days=today.weekday())  # Monday
                for i in range(5):  # Mon–Fri
                    dates.append((start + timedelta(days=i)).strftime('%Y-%m-%d'))

            elif date_range_lower in("next_week" "next week"):
                print("Here for next week conversion...")
                start = today + timedelta(days=(7 - today.weekday()))  # Next Monday
                print("Start:", start)
                for i in range(5):  # Mon–Fri next week
                    dates.append((start + timedelta(days=i)).strftime('%Y-%m-%d'))

            elif date_range_lower in("last_week", "last week"):
                start = today - timedelta(days=(today.weekday() + 7))  # Previous Monday
                for i in range(5):  # Mon–Fri last week
                    dates.append((start + timedelta(days=i)).strftime('%Y-%m-%d'))

            else:
                # Try to parse generic natural language date like "next Monday"
                parsed = dateparser.parse(date_range)
                if not parsed:
                    raise ValueError(f"Could not parse date_range: {date_range}")
                dates = [parsed.strftime('%Y-%m-%d')]

        elif work_date:
            parsed = dateparser.parse(work_date)
            if not parsed:
                raise ValueError(f"Could not parse work_date: {work_date}")
            dates = [parsed.strftime('%Y-%m-%d')]

        else:
            # Default to today
            dates = [today.strftime('%Y-%m-%d')]

        print(dates)
        return dates

    def get_account_id(self) -> str:
        url = f"https://{self.jira_domain}/rest/api/3/myself"
        response = requests.get(
            url,
            auth=(self.jira_email, self.jira_token),
            headers={"Accept": "application/json"}
        )
        if response.status_code != 200:
            raise Exception(f"Failed to fetch account info: {response.text}")
        return response.json()["accountId"]

    def log_manual(self, issue_key, time_seconds, work_date, account_id, work_start: Optional[str]="09:00:00", description: Optional[str] = "work") -> str:
        issue_url = f"https://{self.jira_domain}/rest/api/3/issue/{issue_key}"
        issue_response = requests.get(
            issue_url,
            auth=(self.jira_email, self.jira_token),
            headers={"Accept": "application/json"}
        )
        if issue_response.status_code != 200:
            return f"Failed to fetch issue {issue_key}: {issue_response.text}"
        issue_id = issue_response.json()["id"]

        return self.post_worklog(issue_key, issue_id, time_seconds, work_date, work_start, description, account_id)

    def log_auto_for_date(self, work_date, account_id, total_hours, work_start: Optional[str]="09:00:00", description: Optional[str] = "work") -> str:
        # Fetch in-progress issues
        jql = 'assignee=currentUser() AND project=MGAP AND statusCategory="In Progress"'
        search_url = f"https://{self.jira_domain}/rest/api/3/search"
        search_response = requests.get(
            search_url,
            auth=(self.jira_email, self.jira_token),
            headers={"Accept": "application/json"},
            params={"jql": jql, "fields": "id,key"}
        )
        if search_response.status_code != 200:
            return f"Failed to fetch in-progress issues: {search_response.text}"
        issues = search_response.json().get("issues", [])
        if not issues:
            return "No in-progress issues found."

        total_seconds = int(total_hours * 3600)
        base_seconds = total_seconds // len(issues)
        remaining_seconds = total_seconds % len(issues)  # Leftover time to distribute

        base_time = datetime.strptime(work_start, "%H:%M:%S")

        results = []
        for i, issue in enumerate(issues):
            # Distribute extra seconds to avoid truncation loss
            extra = 1 if i < remaining_seconds else 0
            time_for_this_issue = base_seconds + extra

            # Compute start time for this issue
            issue_start_time = base_time + timedelta(seconds=i * base_seconds)
            issue_start_str = issue_start_time.strftime("%H:%M:%S")

            result = self.post_worklog(
                issue["key"],
                issue["id"],
                time_for_this_issue,
                work_date,
                issue_start_str,  # New start time for each issue
                description,
                account_id
            )
            logged_hours = round(time_for_this_issue / 3600, 2)
            results.append(f"{issue['key']}: {logged_hours}h at {issue_start_str}")
        return " | ".join(results)

    def post_worklog(self, issue_key, issue_id, time_seconds, work_date, work_start, description, account_id) -> str:
        tempo_url = "https://api.tempo.io/4/worklogs"
        payload = {
            "issueKey": issue_key,
            "issueId": issue_id,
            "timeSpentSeconds": time_seconds,
            "startDate": work_date,
            "startTime": work_start,
            "description": description,
            "authorAccountId": account_id
        }
        response = requests.post(
            tempo_url,
            headers={
                "Authorization": f"Bearer {self.tempo_token}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        if response.status_code in [200, 201]:
            return f"Logged {time_seconds // 3600}h to {issue_key}"
        else:
            return f"Failed for {issue_key}: {response.text}"


# In[ ]:




