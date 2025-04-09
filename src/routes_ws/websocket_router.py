from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json
from src.graph_builder.graph_builder import compiled_graph
from src.graph_struct.graph_struct import State
from src.graph_builder.router import query_router

websocket_router = APIRouter()

@websocket_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            # Step 1: Receive message from client
            data = await websocket.receive_text()
            request_data = json.loads(data)
            user_input = request_data.get("message", "")

            if not user_input:
                await websocket.send_text(json.dumps({"status": "error", "message": "No message provided"}))
                continue

            # Step 2: Determine which agent should handle this
            selected_agent = query_router({"input": user_input,"output":""})  # Route to correct agent

            # Step 3: Create state object
            state = State(input=user_input, output="")

            # Step 4: Start processing & send initial status
            await websocket.send_text(json.dumps({"status": "processing", "message": f"Routing to {selected_agent}..."}))

            # Step 5: Execute the correct agent in LangGraph
            async for result in compiled_graph.astream(state):
                await websocket.send_text(json.dumps(result))

            # Step 6: Send completion message
            await websocket.send_text(json.dumps({"status": "completed", "message": "Execution complete"}))

    except WebSocketDisconnect:
        print("Client disconnected")
