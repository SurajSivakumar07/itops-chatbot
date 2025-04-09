from langchain_google_genai import ChatGoogleGenerativeAI
import requests
import json
import re
from dotenv import load_dotenv

import os

load_dotenv()

JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_DOMAIN = "surajsuri279.atlassian.net"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


class JiraTicketManager:
    def __init__(self):
        self.auth = (JIRA_EMAIL, JIRA_API_TOKEN)
        self.headers_json = {"Accept": "application/json"}
        self.headers_post = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Initialize LLM (not used yet, placeholder for future use)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0,
            api_key=GOOGLE_API_KEY
        )

    def get_ticket_info(self, issue_key):
        try:
            url = f"https://{JIRA_DOMAIN}/rest/api/3/issue/{issue_key}"
            response = requests.get(url, auth=self.auth, headers=self.headers_json)

            if response.status_code == 200:
                data = response.json()
                summary = data.get("fields", {}).get("summary", "No summary")
                status = data.get("fields", {}).get("status", {}).get("name", "Unknown")
                description = data.get("fields", {}).get("description", "No description")

                return {
                    "success": True,
                    "message": f"Ticket {issue_key}: '{summary}' (Status: {status})",
                    "data": {
                        "summary": summary,
                        "status": status,
                        "description": description
                    }
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to get ticket info: {response.text}"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error retrieving ticket info: {str(e)}"
            }

    def close_ticket(self, issue_key):
        try:
            info_result = self.get_ticket_info(issue_key)
            if not info_result["success"]:
                return info_result

            current_status = info_result["data"]["status"].lower()
            if current_status in ["done", "closed", "resolved", "complete"]:
                return {
                    "success": True,
                    "message": f"Issue {issue_key} is already in '{current_status}' status."
                }

            # Get available transitions
            url = f"https://{JIRA_DOMAIN}/rest/api/3/issue/{issue_key}/transitions"
            response = requests.get(url, auth=self.auth, headers=self.headers_json)

            if response.status_code != 200:
                return {
                    "success": False,
                    "message": f"Failed to get transitions: {response.text}"
                }

            transitions = response.json().get("transitions", [])
            if not transitions:
                return {
                    "success": False,
                    "message": "No transitions available for this issue."
                }

            # Try fuzzy matching for closing transitions
            closing_keywords = ["done", "closed", "resolve", "resolved", "complete", "finish", "mark as done"]
            target_transition = next(
                (t for t in transitions if any(keyword in t["name"].lower() for keyword in closing_keywords)),
                None
            )

            if not target_transition:
                transition_names = [t["name"] for t in transitions]
                return {
                    "success": False,
                    "message": f"No closing transition found. Available transitions: {', '.join(transition_names)}"
                }

            payload = {
                "transition": {
                    "id": target_transition["id"]
                }
            }

            response = requests.post(
                url,
                headers=self.headers_post,
                auth=self.auth,
                data=json.dumps(payload)
            )

            if response.status_code in [200, 204]:
                return {
                    "success": True,
                    "message": f"Issue {issue_key} closed successfully with transition '{target_transition['name']}'."
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to close issue {issue_key}: {response.text}"
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error occurred: {str(e)}"
            }

    def reopen_ticket(self, issue_key):
        try:
            url = f"https://{JIRA_DOMAIN}/rest/api/3/issue/{issue_key}/transitions"
            response = requests.get(url, auth=self.auth, headers=self.headers_json)

            if response.status_code != 200:
                return {
                    "success": False,
                    "message": f"Failed to get transitions: {response.text}"
                }

            transitions = response.json().get("transitions", [])
            if not transitions:
                return {
                    "success": False,
                    "message": "No transitions available for this issue."
                }

            target_transition = next(
                (t for t in transitions if "reopen" in t["name"].lower()),
                None
            )

            if not target_transition:
                transition_names = [t["name"] for t in transitions]
                return {
                    "success": False,
                    "message": f"No reopen transition found. Available transitions: {', '.join(transition_names)}"
                }

            payload = {
                "transition": {
                    "id": target_transition["id"]
                }
            }

            response = requests.post(
                url,
                headers=self.headers_post,
                auth=self.auth,
                data=json.dumps(payload)
            )

            if response.status_code in [200, 204]:
                return {
                    "success": True,
                    "message": f"Issue {issue_key} reopened successfully."
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to reopen issue {issue_key}: {response.text}"
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error occurred: {str(e)}"
            }

    def process_command(self, user_input):
        """Process natural language commands like 'close ticket 10265'."""
        match = re.search(r'(?:ticket|issue)\s+#?([A-Z]+-\d+|\d+)', user_input, re.IGNORECASE)
        if not match:
            return "Please specify a ticket number (e.g., 'close ticket 10265')."

        issue_key = match.group(1)

        if re.search(r'(close|resolve|complete|finish)', user_input, re.IGNORECASE):
            result = self.close_ticket(issue_key)
            return result["message"]
        elif re.search(r'(reopen|open)', user_input, re.IGNORECASE):
            result = self.reopen_ticket(issue_key)
            return result["message"]
        elif re.search(r'(get|show|display|info|information|details)', user_input, re.IGNORECASE):
            result = self.get_ticket_info(issue_key)
            return result["message"]
        else:
            result = self.get_ticket_info(issue_key)
            return result["message"]



import os
#authentication
JIRA_URL = os.getenv("JIRA_URL")
EMAIL = os.getenv("JIRA_EMAIL")
API_TOKEN = os.getenv("JIRA_API_TOKEN")

def extract_issue_key(user_query):
    """Extracts the Jira issue key (number) from the user's query."""


    match = re.search(r'\b\d+\b', user_query)  # Matches any numeric issue key
    return match.group() if match else False

def validate_key(ticket_key):
    print("The ticket number iş",ticket_key)
    headers = {"Accept": "application/json"}
    response = requests.get(
        f"{JIRA_URL}/rest/api/3/issue/{ticket_key}",
        headers=headers,
        auth=(EMAIL, API_TOKEN),
    )
    print("The response is:", response.status_code)
    if response.status_code == 200:
        print("The ticket key is valid.",ticket_key)
        return True
    else:
        False