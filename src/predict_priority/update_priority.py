
import requests
import os
JIRA_URL=os.environ.get("JIRA_URL")
EMAIL=os.environ.get("JIRA_EMAIL")
API_TOKEN=os.environ.get("JIRA_API_KEY")

def update_priority(issue_key,priority):
    """Updates the Jira issue, keeping existing values for missing fields."""

    # Use extracted values if available, otherwise keep existing values
    data = {
        "fields": {
            "priority": {"name": priority},

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
        return "Updated sucessfully."
        print(f"Issue {issue_key} updated successfully!")
    else:
        print(f"Failed to update issue: {response.status_code}, {response.text}")
        return response.text