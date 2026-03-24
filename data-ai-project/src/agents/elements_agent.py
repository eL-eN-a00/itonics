# Business logic for Search/Create/Update on the elements table.
# the "worker" that knoxs how to use the database functions I just wrote.
# It won't decide what to do (that's the Orchestrator's job later), but it will execute the commands.

import uuid
from typing import Dict, Any, List, Optional
from database_manager import DatabaseManager

class ElementsAgent:
    def __init__(self, db_manager: DatabaseManager, user_uri: str):
        """Definition of the Elements Agent"""
        self.db = db_manager
        self.user_uri = user_uri
    
    def search(self, space_uri: str, query: str) -> str:
        """Searches for elements and returns a formatted string."""
        # 1. Security Check
        if not self.db.check_permission(self.user_uri, space_uri, 'read'):
            return "Error: You do not have permission to read in this space."
    
        # 2. Execution
        results = self.db.search_elements(space_uri, query)

        if not results:
            return f"No elements found matching '{query}'."
        
        # 3. Formatting for the LLM/User
        output = "I found the following elements:\n"
        for item in results:
            output += f"- [{item['uri']}] {item['title']} (Created: {item['creation_date']})\n"
        return output
    
    def create(self, space_uri: str, type_uri: str, title: str) -> str:
        """Creates a bew element after verifying permissions."""
        # 1. Security Check
        if not self.db.check_permission(self.user_uri, space_uri, 'write'):
            return "Error: You do not have permission to create elements here."
        
        # 2. Execution
        new_uri = f"element_{uuid.uuid4().hex[:8]}"
        try:
            self.db.create_element(new_uri, title, type_uri, space_uri, self.user_uri)
            return f"Succcessfully created element '{title}' with URI: {new_uri}"
        except Exception as e:
            return f"Failed to create element: {str(e)}"
    
    def update_title(self, space_uri: str, element_uri: str, new_title: str) -> str:
        """Updates an element title if the user has write access to the space."""
        # 1. Security Check
        if not self.db.check_permission(self.user_uri, space_uri, 'write'):
            return "Error: You do not have permission to modify elements in this space."
        
        # 2. Execution
        success = self.db.update_element_title(element_uri, new_title)

        if success:
            return f"Updated element {element_uri} to new title: '{new_title}'"
        return f"Could not find element with URI {element_uri} to update."


# This structure's assets
# encapsulation: the agent doesn't care how the DB works; it just calls methods.
#error handling: it returns human-readable strings (or LLM-readable strings) so the chat interface can display them easily.
#statelessness: by passing the user_uri and space_uri into these methods, it is ensured that every single action is audited against the permission table.