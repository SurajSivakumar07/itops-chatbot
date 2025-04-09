from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
from src.graph_builder.graph_builder import compiled_graph
from src.graph_struct.graph_struct import State
import os
import yaml
from pathlib import Path
from nemoguardrails import LLMRails, RailsConfig

# Env config
os.environ["LANGSMITH_ENDPOINT"] = os.getenv("LANGSMITH_ENDPOINT")
os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGSMITH_API_KEY")
os.environ["LANGCHAIN_TRACING_V2"] = "true"

# FastAPI app
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load YAML config
with open("./config.yml", "r") as file:
    intent_config = yaml.safe_load(file)

# Load NeMo Guardrails config
rails_path = Path("./config")
rails_config_obj = RailsConfig.from_path(str(rails_path))
llm_rails = LLMRails(config=rails_config_obj)


# Rule-based keyword blocker
def is_message_blocked(user_input: str) -> bool:
    forbidden_keywords = [
        "impersonate", "forget rules", "abuse", "explicit", "personal info", "execute code",
        "system prompt", "garbled", "hack"
    ]
    user_input_lower = user_input.lower()
    return any(keyword in user_input_lower for keyword in forbidden_keywords)


# Rule-based intent classifier
def classify_input(user_input: str, samples: dict) -> str:
    user_input_lower = user_input.lower()
    for intent in samples["sample_queries"]:
        intent_type = intent["type"]
        for example in intent["examples"]:
            if example in user_input_lower:
                return intent_type
    return "unknown"


# WebSocket handler
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    # Initialize chat history for this connection
    chat_history = []

    try:
        while True:
            await websocket.send_text(json.dumps({"status":"happy to help you"}))
            data = await websocket.receive_text()

            if is_message_blocked(data):
                await websocket.send_text(json.dumps({
                    "status": "Your message violates our company policy."
                }))
                continue

            # Classify intent
            intent = classify_input(data, intent_config)
            print("Detected intent:", intent)

            # Response based on rule
            if intent == "greeting":
                message = intent_config["messages"]["bot introduction"]
                await websocket.send_text(json.dumps({"status": message}))

            elif intent == "off topic":
                message = intent_config["messages"]["off topic message"]
                await websocket.send_text(json.dumps({"status": message}))
            elif(intent =="unknown" or intent == "jira related"):
                # Use Guardrails for fallback
                try:
                    guardrails_response = await llm_rails.generate_async(prompt=data)
                    await websocket.send_text(json.dumps({
                        "status": guardrails_response.text
                    }))
                except Exception as e:
                    print("Guardrails error, falling back to LangGraph:", e)
                    # Use LangGraph if guardrails fails
                    state: State = {
                        "input": data,
                        "output": "",
                        "chat_history": chat_history,  # Pass the persistent chat history
                        "step": "",
                        "websocket": websocket
                    }
                    response = await compiled_graph.ainvoke(state)

                    await websocket.send_text(json.dumps({"status": "I can help you with 1) Issue related2) Update ticket3) Close ticket4) Ticket status"}))



    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket Error: {e}")