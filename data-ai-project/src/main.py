"""
Main module for chatbot implementation.

Implement your chatbot logic here. The dashboard will call `handle_user_input()`
whenever a user sends a message.

Available functions:
- generate_interaction_id(): Generate unique ID to link messages
- get_chat_history(): Get list of previous messages for context
- send_user_message(content, interaction_id): Send a user message
- stream_assistant_response(content, interaction_id): Stream an assistant response
"""

import os
from chat_utils import (
    generate_interaction_id,
    get_chat_history,
    send_user_message,
    stream_assistant_response,
)
from database_manager import DatabaseManager
from agents.orchestrator import Orchestrator

# The DatabaseManager is initialized only once (Singleton)
db_manager = DatabaseManager()

def handle_user_input(user_input: str) -> None:
    """
    Process user input using a LangChain Orchestrator and stream the response.
    """
    # 1. Generate the interaction ID to link the question to the answer
    interaction_id = generate_interaction_id()

    # 2. Retrieve the history for the agent context
    history = get_chat_history()

    # 3. Display the user's message in the UI
    send_user_message(user_input, interaction_id)

    # 4. Define the context (For this, we can simulate a default user and space)
    # In a real app, this information would come from the user session.
    user_uri = "user:alice"
    space_uri = "space:acme-projects"

    try:
        # 5. Initialize the LangChain Orchestrator
        orchestrator = Orchestrator(
            db_manager=db_manager,
            user_uri=user_uri,
            space_uri=space_uri,
        )

        # Get the agent's response
        # We give 'history' so the agent can remember previous messages
        response = orchestrator.handle_message(user_input, history)
    
    except Exception as e:
        # Clean error handling for the UI
        response = f"Sorry, I encountered a technical error:{str(e)}"
    
    # 7. Stream the response to the dashboard
    print(f"DEBUG RESPONSE : {response}")
    stream_assistant_response(response, interaction_id)
