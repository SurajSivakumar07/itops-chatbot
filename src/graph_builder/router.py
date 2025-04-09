from src.graph_struct.graph_struct import State
from typing_extensions import Literal

# Router handler

def router_node(state: State):
    return {"input": state["input"], "output": ""}

# Router function decides the next step
def query_router(state: State) -> Literal["create_issue", "update_tikcet"]:
    """
    Determine which path to take in the graph based on the user input.

    Returns:
        A string literal indicating which node to route to next.
    """
    user_input = state["input"].lower()

    # Define keywords for different operations
    create_issue_keywords = ["create", "new", "make", "submit", "report"]
    update_issue_keywords = ["update", "modify", "change", "edit", "status"]
    close_issue_keywords = ["close", "done", "closed", "resolve", "resolved", "complete", "finish", "mark as done"]


    # Check if input contains keywords for creating issues
    if any(keyword in user_input for keyword in create_issue_keywords):
        return "create_issue"

    # Check if input contains keywords for updating issues
    if any(keyword in user_input for keyword in update_issue_keywords):
        return "update_tikcet"
    if any(keyword in user_input for keyword in close_issue_keywords):
        return "close_ticket"

    # Default to create_issue if no specific route is determined
    # You could also add more sophisticated routing logic here
    return "create_issue"
