from typing import TypedDict
from fastapi import FastAPI, WebSocket
from langchain_core.messages import BaseMessage
from typing import List, Union


class State(TypedDict):
    input: str
    output: str
    chat_history: List[BaseMessage]
    step:str
    websocket: WebSocket