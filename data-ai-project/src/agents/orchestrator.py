# Logic of the "Brain" which receives the input, identifies the intention and delegates.
# Its job:
# 1. Understand the user's intent (Are they searching? Creating? Summarizing?)
# 2. Extract the necessary parameters (Titles, URIs, Space IDs).
# 3. Call the ElementsAgent that was just built.
# 4. Format a friendly response

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate, MessagesPlaceholder
from langchain.tools import StructuredTool
from langchain_core.messages import HumanMessage, AIMessage
from database_manager import DatabaseManager
from agents.elements_agent import ElementsAgent

class Orchestrator:
    def __init__(self, db_manager: DatabaseManager, user_uri: str, space_uri: str):
        """Definition of the Orchestrator"""
        self.db = db_manager
        self.user_uri = user_uri
        self.space_uri = space_uri
        self.worker = ElementsAgent(db_manager, user_uri)

        # 1. Define the Tools for the LLM
        # We wrap the ElementsAgent methods so LangChain understands them
        def search_tool(query : str) -> str:
            return self.worker.search(self.space_uri, query)
        
        def create_tool(title : str) -> str:
            return self.worker.create(self.space_uri, "type:idea", title)
        
        def update_tool(element_uri : str, new_title : str) -> str:
            return self.worker.update_title(self.space_uri, element_uri, new_title)

        self.tools = [
            StructuredTool.from_function(
                func=search_tool,
                name="search_elements",
                description="Useful for finding existing ideas or elements by title."
            ),
            StructuredTool.from_function(
                # We'd need a way to fetch type_uri, or hardcode a default for the test
                func=create_tool,
                name="create_element",
                description="Useful for creating a new idea or element. Input should be a title."
            ),
            StructuredTool.from_function(
                func=update_tool,
                name="update_element_title",
                description="Useful for renaming an existing element. Required the element_uri and the new_title."
            )
        ]

        # 2. Setup the LLM and Prompt
        llm = ChatOpenAI(
            openai_api_base="https://api.groq.com/openai/v1",
            openai_api_key=os.environ.get("OPENAI_API_KEY"),
            model_name="llama-3.3-70b-versatile",
            temperature=0
        )
        prompt = PromptTemplate.from_template(
        """You are a database assistant.

    CURRENT CONTEXT:
    - Current user: {user_uri}
    - Current space: {space_uri}

    You have access to these tools:
    {tools}

    Use this format:
    Question: the input question
    Thought: what you should do
    Action: the tool name (one of [{tool_names}])
    Action Input: the input to the tool
    Observation: the result
    Thought: I now have the final answer
    Final Answer: your response

    IMPORTANT: If you already know the answer WITHOUT using a tool, use ONLY this format:
    Question: who am i?
    Thought: I know this from context, no tool needed.
    Final Answer: You are user:... in space:....

    Never write "Action: None". If no tool is needed, go straight to Final Answer.

    Chat history:
    {chat_history}

    Question: {input}
    Thought: {agent_scratchpad}"""
    ).partial(user_uri=self.user_uri, space_uri=self.space_uri)

        # 3. Construct the Agent
        agent = create_react_agent(llm, self.tools, prompt)
        self.agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True, handle_parsing_errors=True, max_iterations=5)
    
    def handle_message(self, user_input: str, chat_history: list) -> str:
        """This is called by main.py"""
        # We convert the objects 'ChatMessage' in LangChain format
        langchain_history = []
        #if not user_input.strip():
         #       return "Dites-moi quelque chose!"   
        for msg in chat_history[-5:]:
            role = getattr(msg, 'role', '').strip()
            content = getattr(msg, 'content', '')
            if role == 'user':
                langchain_history.append(HumanMessage(content=content))
            elif role in ['assistant', 'AI']:
                langchain_history.append(AIMessage(content=content))
        try :
            result = self.agent_executor.invoke({
                "input": user_input,
                "chat_history": langchain_history
            })
            return result["output"]
        except Exception as e:
            return f"Sorry, I had an issue with the question {str(e)}"
    
# why is it a good implementation:
# 1. True Agentic Behavior: The LLM decides which tool to call based on the description provided in StructuredTool
# 2. Scalability: If we want to add a "Delete" function, we just add one more tool to the list.
# 3. Chat History: It can handle follow-up questions (e.g., User: "Find ideas about cars" -> AI: "Found Idea_A" -> User: "Rename it to Toyota.").