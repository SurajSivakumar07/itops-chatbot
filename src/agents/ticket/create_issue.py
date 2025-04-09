from src.agents.ticket.knowledge_article import ka_search
from src.agents.ticket.similar_search import similar_search
from src.predict_priority.predict_priority import predict_priority
from src.graph_struct.graph_struct import State
from src.agents.ticket.create_issue_methods import extract_issue_details, search_jira_issues, create_jira_issue, \
    JIRA_URL, serach_knowledge_article
import json
from src.agents.update_ticket.update_ticket_methods import update_jira_issue
from langchain_core.messages import HumanMessage, AIMessage
from src.agents.ticket.create_llm import predict

# from src.agents.ticket.similar_search import similar_search
# async def create_issue(state):
#     websocket = state.get("websocket")
#     chat_history = state.get("chat_history", [])
#
#     if (state["input"] == "Issue related"):
#         await websocket.send_text(json.dumps({"status": "Enter the issue you're facing"}))
#         state["input"] = await websocket.receive_text()
#
#     user_input = state["input"]
#     chat_history.append(HumanMessage(content=user_input))  # Append user message
#
#     summary, description = extract_issue_details(user_input)
#
#     # Sending message to frontend
#     status_1 = "Searching for similar Jira issues..."
#     if websocket:
#         await websocket.send_text(json.dumps({"status": status_1}))
#     chat_history.append(AIMessage(content=status_1))
#
#     similar_issues_found = search_jira_issues(summary)
#     try:
#         similar_query = similar_search(user_input)
#
#         await websocket.send_text(json.dumps({
#             "similar_issues": similar_query
#         }))
#     except ValueError as e:
#         error_message = str(e)
#         print(error_message)
#
#     #searching for similar issues
#     if(similar_issues_found is None):
#         await websocket.send_text(json.dumps({"status": "No issues found"}))
#     if websocket:
#         await websocket.send_text(json.dumps({
#             "similar_issues": similar_issues_found
#         }))
#     # chat_history.append(AIMessage(content=f"{status_2}: {similar_issues_found}"))
#
#     status_3 = "Searching for related Jira articles..."
#     if websocket:
#         await websocket.send_text(json.dumps({"status": status_3}))
#     chat_history.append(AIMessage(content=status_3))
#
#     # known_issues_found = serach_knowledge_article(summary)
#     known_issues_found = ka_search(user_input)
#     if websocket:
#         await websocket.send_text(json.dumps({
#             "messeage": "Results retrieved",
#             "articles": known_issues_found,
#             "similar_issues": similar_issues_found
#         }))
#     chat_history.append(AIMessage(content=f"Knowledge Base: {known_issues_found}"))
#
#     # Asking for confirmation to create a ticket
#     ask_create = "Would you like to create a ticket?"
#     if websocket:
#         await websocket.send_text(json.dumps({"status": ask_create}))
#     chat_history.append(AIMessage(content=ask_create))
#
#     response = await websocket.receive_text()
#
#     user_response = predict(response)
#     chat_history.append(HumanMessage(content=user_response))
#
#     if user_response == "yes":
#         creating_ticket = "Creating a ticket..."
#         if websocket:
#             await websocket.send_text(json.dumps({"status": creating_ticket}))
#         chat_history.append(AIMessage(content=creating_ticket))
#
#         ticket_response = create_jira_issue(summary, description)
#
#         created_msg = f"Ticket Created: {ticket_response}"
#         if websocket:
#             await websocket.send_text(json.dumps({
#                 "status": "Ticket Created",
#                 "ticket_details": ticket_response
#             }))
#
#         # Predict priority
#         update_priority = "Updating the priority..."
#         if websocket:
#             await websocket.send_text(json.dumps({"status": update_priority}))
#
#         predicted = predict_priority(summary + description)
#         if websocket:
#             await websocket.send_text(json.dumps({"status": predicted}))
#
#         # Update Jira issue
#         ticket_updated = update_jira_issue(
#             issue_key=ticket_response["ticket_id"],
#             priority=predicted
#         )
#
#
#
#     return {
#         "input": user_input,
#         "websocket": websocket
#     }
#
async def create_issue(state):
    websocket = state.get("websocket")
    chat_history = state.get("chat_history", [])

    if state["input"] == "Issue related":
        await websocket.send_text(json.dumps({"status": "Enter the issue you're facing"}))
        state["input"] = await websocket.receive_text()

    user_input = state["input"]
    chat_history.append(HumanMessage(content=user_input))  # Append user message

    # Immediately send "Extracting issue details" message
    await websocket.send_text(json.dumps({"status": "Extracting issue details..."}))
    summary, description = extract_issue_details(user_input)

    # Immediately send "Searching for similar Jira issues" message
    await websocket.send_text(json.dumps({"status": "Searching for similar Jira issues..."}))
    chat_history.append(AIMessage(content="Searching for similar Jira issues..."))

    # Get similar issues from Jira
    similar_issues_found = search_jira_issues(summary)

    # Immediately send semantic search status message
    try:
        await websocket.send_text(json.dumps({"status": "Running semantic search for similar issues..."}))
        similar_query = similar_search(user_input)
        await websocket.send_text(json.dumps({
            "similar_issues": similar_query
        }))
    except ValueError as e:
        error_message = str(e)
        print(f"Error in similar_search: {error_message}")
        await websocket.send_text(json.dumps({"status": f"Error in search: {error_message}"}))

    # Send similar Jira issues to the frontend
    if similar_issues_found is None:
        await websocket.send_text(json.dumps({"status": "No similar issues found"}))
    else:
        await websocket.send_text(json.dumps({
            "similar_issues": similar_issues_found
        }))

    # Send status for searching related knowledge articles
    await websocket.send_text(json.dumps({"status": "Searching for related knowledge articles..."}))
    chat_history.append(AIMessage(content="Searching for related knowledge articles..."))

    # Search knowledge articles
    known_issues_found = ka_search(user_input)

    # Send results to frontend immediately
    await websocket.send_text(json.dumps({
        "message": "Results retrieved",
        "articles": known_issues_found,
        "similar_issues": similar_issues_found
    }))
    chat_history.append(AIMessage(content=f"Knowledge Base: {known_issues_found}"))

    # Ask for confirmation to create a ticket
    ask_create = "Would you like to create a ticket?"
    await websocket.send_text(json.dumps({"status": ask_create}))
    chat_history.append(AIMessage(content=ask_create))

    response = await websocket.receive_text()
    user_response = predict(response)
    chat_history.append(HumanMessage(content=user_response))

    if user_response == "yes":
        # Immediately send "Creating a ticket" message
        await websocket.send_text(json.dumps({"status": "Creating a ticket..."}))
        chat_history.append(AIMessage(content="Creating a ticket..."))

        ticket_response = create_jira_issue(summary, description)

        await websocket.send_text(json.dumps({
            "status": "Ticket Created",
            "ticket_details": ticket_response
        }))

        # Predict and update priority - send status immediately
        await websocket.send_text(json.dumps({"status": "Updating the priority..."}))

        predicted = predict_priority(summary + description)
        await websocket.send_text(json.dumps({"status": f"Priority set to: {predicted}"}))

        # Update Jira issue with the predicted priority
        ticket_updated = update_jira_issue(
            issue_key=ticket_response["ticket_id"],
            priority=predicted
        )

        # Immediately send success message for ticket update
        await websocket.send_text(json.dumps({"status": "Ticket updated successfully"}))

    return {
        "input": user_input,
        "websocket": websocket,
        "chat_history": chat_history
    }
