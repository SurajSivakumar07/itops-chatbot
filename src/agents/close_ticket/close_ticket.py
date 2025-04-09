from langchain_core.messages import HumanMessage, AIMessage
import json
from src.agents.close_ticket.close_ticket_method import JiraTicketManager, extract_issue_key, validate_key
from src.graph_struct.graph_struct import State
from src.input_validation.input_validation import user_input


async def input_reenter(state: State):
    websocket = state.get("websocket")
    return await websocket.receive_text()


async def close_ticket(state: State):
    websocket = state.get("websocket")
    chat_history = state.get("chat_history", [])

    # Append user input to chat history
    chat_history.append(HumanMessage(content=state["input"]))

    # Log: inside update statement
    status_msg = "Inside close ticket statement"
    if websocket:
        await websocket.send_text(json.dumps({"status": status_msg}))
    chat_history.append(AIMessage(content=status_msg))
    if(user_input == "Close ticket"):
        await websocket.send_text(json.dumps({"status": "Enter the ticket number which is need to be closed"}))
        # Await input from user
        state["input"] = await input_reenter(state)


    print("The ticket number is", state["input"])

    # Process the command to close the ticket
    manager = JiraTicketManager()
    command_result = manager.process_command(state["input"])

    # Extract issue key
    extract_key = extract_issue_key(state["input"])

    if (extract_key == False):
        await websocket.send_text(json.dumps({"status": 'Ticket number not found,Enter a valid ticket number'}))
        state["input"] = await input_reenter(state)

    await websocket.send_text(json.dumps({"status": "Validating the key"}))

    if validate_key(extract_key):
        result = manager.close_ticket(extract_key)
        print("The result is ", result)
        await websocket.send_text(json.dumps({"status": result["message"]}))
    else:
        result = "Invalid ticket key."
        await websocket.send_text(json.dumps({"status": result}))

    # Return updated state
    return {
        "input": state["input"],
        "output": result,
        # "chat_history": chat_history
    }
