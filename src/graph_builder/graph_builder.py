from langgraph.graph import StateGraph, END

from src.agents.close_ticket.close_ticket import close_ticket
from src.agents.ticket.create_issue import create_issue
from src.graph_struct.graph_struct import State
from src.graph_builder.router import query_router,router_node

from src.agents.update_ticket.ticket_update import update_tikcet

graph = StateGraph(State)

# Add nodes to the graph
graph.add_node("router", router_node)
graph.add_node("create_issue", create_issue)
graph.add_node("update_tikcet", update_tikcet)
graph.add_node("close_ticket", close_ticket)

# Set entry point
graph.set_entry_point("router")

# Add conditional edges
graph.add_conditional_edges(
    "router",
    query_router,
    {"create_issue": "create_issue",
     "update_tikcet": "update_tikcet",
     "close_ticket": "close_ticket",}
)

# Add edges
graph.add_edge("create_issue", END)
graph.add_edge("update_tikcet", END)
graph.add_edge("close_ticket", END)
# Compile the graph
compiled_graph = graph.compile()
