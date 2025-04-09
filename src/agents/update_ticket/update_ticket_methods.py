import requests
import json
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage
from pandas.core.interchange.from_dataframe import primitive_column_to_ndarray

from src.config.llm import tickets_llm
import os
JIRA_URL = os.getenv("JIRA_URL")
EMAIL = os.getenv("JIRA_EMAIL")
API_TOKEN = os.getenv("JIRA_API_TOKEN")


def validate_key(ticket_key):
    print("The ticket number iş",ticket_key)
    headers = {"Accept": "application/json"}
    response = requests.get(
        f"{JIRA_URL}/rest/api/3/issue/{ticket_key}",
        headers=headers,
        auth=(EMAIL, API_TOKEN),
    )
    print("The response is:", response.status_code)
    if response.status_code == 204:
        print("The ticket key is valid.",ticket_key)
        return True
    else:
        False



def extract_issue_key(user_query):
    """Extracts the Jira issue key (number) from the user's query."""


    match = re.search(r'\b\d+\b', user_query)  # Matches any numeric issue key
    return match.group() if match else None


def extract_issue_details(user_query):
    """Uses Gemini Flash 2.0 to extract structured issue details."""
    prompt = f"""
    Extract any of the following details from the user query and return a valid JSON object:
    - "summary": A short title (if mentioned)
    - "description": A detailed explanation (if mentioned)
    - "priority": One of ["Low", "Medium", "High"] (if mentioned)
 
    If a field is not mentioned, do NOT include it in the response.

    Example Outputs:
    1. If the user says 'Set issue 10034 to High priority':
       {{ "priority": "High" }}

    2. If the user says 'Update issue 10034 summary to "Database Outage"':
       {{ "summary": "Database Outage" }}

    3. If the user says 'Change issue 10034 description to "The server is overheating."':
       {{ "description": "The server is overheating." }}

    Ensure the response is **valid JSON** and does NOT contain extra text.
    User Query: {user_query}
    """

    response = tickets_llm.invoke([SystemMessage(content="Extract structured issue details."), HumanMessage(content=prompt)])

    # Ensure response is in valid JSON format
    try:
        response_text = response.content.strip()
        print("Raw Gemini Response:", response_text)  # Debugging

        # Extract JSON part (handle cases where Gemini returns extra text)
        json_start = response_text.find("{")
        json_end = response_text.rfind("}") + 1
        if json_start != -1 and json_end != -1:
            response_text = response_text[json_start:json_end]

        return json.loads(response_text)  # Ensure valid JSON
    except json.JSONDecodeError:
        print("Error: Invalid JSON response from Gemini.")
        return {}


def fetch_current_issue(issue_key):
    """Fetches the existing Jira issue details to retain unchanged fields."""
    headers = {"Accept": "application/json"}

    response = requests.get(
        f"{JIRA_URL}/rest/api/3/issue/{issue_key}",
        headers=headers,
        auth=(EMAIL, API_TOKEN),
    )

    if response.status_code == 200:
        issue_data = response.json()
        return {
            "summary": issue_data["fields"].get("summary", ""),
            "description": issue_data["fields"].get("description", {}).get("content", [{}])[0].get("content", [{}])[
                0].get("text", ""),
            "priority": issue_data["fields"].get("priority", {}).get("name", "Medium"),
            # Default to 'Medium' if missing
        }
    else:
        print(f"Failed to fetch issue details: {response.status_code}, {response.text}")
        return None


def update_jira_issue(issue_key, summary=None, description=None, priority=None):
    """Updates the Jira issue, keeping existing values for missing fields."""
    current_issue = fetch_current_issue(issue_key)
    if not current_issue:
        print("Error: Could not retrieve current issue details.")
        return

    # Use extracted values if available, otherwise keep existing values
    data = {
        "fields": {
            "summary": summary if summary else current_issue["summary"],
            "priority": {"name": priority if priority else current_issue["priority"]},
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "text": description if description else current_issue["description"],
                                "type": "text"
                            }
                        ]
                    }
                ]
            }
        }
    }

    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    response = requests.put(
        f"{JIRA_URL}/rest/api/3/issue/{issue_key}",
        headers=headers,
        auth=(EMAIL, API_TOKEN),
        json=data
    )

    if response.status_code == 204:

        return  True
        print(f"Issue {issue_key} updated successfully!")
    else:
        print(f"Failed to update issue: {response.status_code}, {response.text}")
        return response.text

