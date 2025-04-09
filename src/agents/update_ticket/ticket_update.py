import json
from src.agents.update_ticket.update_ticket_methods import validate_key
from src.graph_struct.graph_struct import State
from src.agents.update_ticket.update_ticket_methods import extract_issue_key,extract_issue_details,update_jira_issue
async  def update_tikcet(state:State):

    websocket=state["websocket"]


    state["input"]=state["input"].lower()

    if(state["input"] == "update ticket"):
        await websocket.send_text(json.dumps({"status": "Please specify a ticket number and update.eg(10993 change description to or change summar to or change priority to) "}))
        state["input"]=await websocket.receive_text()
    result=""

    await websocket.send_text(json.dumps({"status": "checking ticket number"}))


    issue_key = extract_issue_key(state["input"])
    await websocket.send_text(json.dumps({"status":issue_key}))

    if  (issue_key == False):
        print("Error: No valid issue key found in the query.")
        await websocket.send_text(json.dumps({"status": "Error: No valid issue key found in the query."}))

        return {"input":state["input"],"output":"Key is not entered"}

    else:

        check=validate_key(issue_key)

        if(check == False):
            return {input:state["input"],"output":"Enter a valid ticket number."}
        issue_details = extract_issue_details(state["input"])
        print("Extracted Issue Details:", issue_details)


        if issue_details:
            result=update_jira_issue(
                issue_key,
                summary=issue_details.get("summary"),
                description=issue_details.get("description"),
                priority=issue_details.get("priority")
            )
            if(result):
                await websocket.send_text(json.dumps({"status":"The update was successful!"}))
            else:
                await websocket.send_text(json.dumps({"status":"Enter a valid ticket number."}))
    return {"input":state["input"],"output":result}