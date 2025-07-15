import json
import logging
from typing import List, Dict, Optional, Tuple, Any, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field
import re
from datetime import datetime
from bson import ObjectId
import threading
import uuid

from .database import MongoDBManager
# Removed AtlasVectorSearchService - using database search methods directly
from .config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global lock for thread-safe agent operations
_agent_lock = threading.Lock()

# Thread-safe checkpointer cache
_checkpointer_cache = {}
_checkpointer_lock = threading.Lock()

prompt = """You are a smart AI Assistant for King Arthur Baking.
You are allowed to make multiple calls (either together or in sequence).
Only look up information when you are sure of what you want.

There are two tools you can use to get information:
1. retrieve_information: This tool performs semantic/hybrid search over product descriptions, ingredients, and details. Use this for natural language queries like "chocolate cake mix" or "gluten-free options".
2. query_information: This tool accepts natural language queries that get converted to MongoDB queries. Use this for specific queries like "most expensive products" or "products under $10". Do NOT pass MongoDB syntax directly - use natural language.

If the user wants exact count, price, images, type, or list of products and query with exact information. You should use query_information tool.
If the user wants you to recommend, which means user don't know exact information. You should use retrieve_information tool.

Here is some special cases:
If there is no result from query_information tool, you should use retrieve_information tool first, take one result and understand it and then use query_information tool with the information you have gathered.

If you need to look up some information before asking a follow up question, you are allowed to do that!
You have to make response as fast as you can.

After gathering information, you have to generate a response to the user's query.
Make sure that:
1. You are answering the user's query exactly.
2. You are providing specific product recommendations with details.
3. Your response is well formatted and easy to understand.
4. Always sort the products by price, reviews, etc. If there is no sort, you should sort by price. Decide ascending or descending according to the user's query.
5. According to the user's query, you should provide recommendations.
6. If the user's query is not clear, you should ask for more information.
7. If the user's query is not related to the products, you should say that you are not sure about the product.
"""

mongo_schema = """"""
example_document = """"""
custom_fields_description = """Here's an explanation of each field:

1. SKU (Stock Keeping Unit): 213793
A unique identifier for the product used for inventory management.

2. UPC (Universal Product Code): 071012000630
A barcode symbol that's widely used to identify products in retail.

3. Maximum Purchase: 12 units
The maximum quantity of the product that can be purchased at one time.

4. swym-disabled: false
Indicates whether the product is impacted by certain external services, possibly related to wishlist services (Swym).

5. _Promo_Exclusion: No
Indicates if the product is excluded from promotions.

6. Various badge fields: (e.g., _badge_glutenfree, _badge_kosherpareve)
These fields indicate different certifications or attributes, such as whether the product is gluten-free, kosher, organic, made in the USA, etc. All are marked "No," meaning these attributes do not apply to the product.

7. _Parent_Category: Mixes
The main category to which this product belongs.

8. _Child_Category: Cookies
A subcategory within the parent category.

9. _Online_Exclusive: 0
Indicates whether the product is exclusive to online sales. A value of 0 suggests it's not online exclusive.

10. _sale_label, _clearance_label: No
Indicates if the product is on sale or clearance. Both are set to "No."

11. _free_ship_label, _ground_ship_label: No
Indicates if the product qualifies for free or ground shipping. Both labels are set to "No."

12. _new_label: Yes
Shows that the product is considered new.

13. _label_path, _package_path:
Paths to the product's label and packaging files, which may be used for display purposes.

14. _type_label, _flavor_label, _category_label:
Descriptions of the product type, flavor (Lemon), and relevant categories (Dessert, Snack).

15. _review_avg_score: 4.7
The average customer review score, which is quite high.

16. _review_count: 14
The number of reviews the product has received.

17. _Special_Savings, _special_savings_label: No
Indicates the absence of any special savings associated with the product."""

try:
    with open('src/schema-king_arthur_baking_db-mixes-mongoDBJSON.json', 'r') as file:
        mongo_schema = json.load(file)
except FileNotFoundError:
    logger.warning("Schema file not found, using empty schema")
    mongo_schema = {}

try:
    with open('src/document-king_arthur_baking_db-minxes.json', 'r') as file:
        example_document = json.load(file)
except FileNotFoundError:
    logger.warning("Example document file not found, using empty document")
    example_document = {}

class AgentState(BaseModel):
    """State for the AI agent."""
    messages: List[Any] = Field(default_factory=list)
    user_query: str = ""
    search_results: List[Dict] = Field(default_factory=list)
    analysis: str = ""
    response: str = ""
    tool_calls: List[str] = Field(default_factory=list)
    context: Dict = Field(default_factory=dict)
    step: str = "start"

def get_thread_safe_checkpointer(thread_id: str) -> MemorySaver:
    """Get or create a thread-safe checkpointer for the given thread ID."""
    with _checkpointer_lock:
        if thread_id not in _checkpointer_cache:
            _checkpointer_cache[thread_id] = MemorySaver()
            logger.info(f"Created new checkpointer for thread {thread_id}")
        return _checkpointer_cache[thread_id]

class KingArthurBakingAgent:
    """AI Agent for King Arthur Baking mixes with advanced retrieval and reasoning."""
    
    def __init__(self, db_manager: Optional['MongoDBManager'] = None, user_id: Optional[str] = None):
        self.user_id = user_id or str(uuid.uuid4())[:8]
        self.system_prompt = prompt
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.temperature
        )
        self.query_generator = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.temperature
        )
        self.field_generator = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.temperature
        )
        # Use provided database manager or create new one
        self.db_manager = db_manager if db_manager is not None else MongoDBManager()
        # Create the tool with access to db_manager
        self.tools = [self._create_retrieve_tool(), self._create_mongo_query_tool()]
        self.extract_fields = []
        self.llm = self.llm.bind_tools(self.tools)
        # Use database search methods directly
        self.graph = self.create_graph()
        self._lock = threading.Lock()  # Per-agent instance lock
        logger.info(f"Initialized agent for user {self.user_id}")
    
    def _create_retrieve_tool(self):
        """Create a tool for retrieving information from the database."""
        @tool
        def retrieve_information(query: str) -> str:
            """Hybrid search for information from Atlas."""
            try:
                print(f"[{self.user_id}] Retrieving information for {query}")
                
                self.extract_fields = self.generate_necessary_fields(query, "")
                search_results = self.db_manager.hybrid_search(query)
                if search_results:
                    # Format results for the LLM
                    formatted_results = []
                    for result in search_results:
                        formatted_results.append(json.dumps(self.bson_object_id_to_str(result), indent=2))
                        # formatted_results.append(f"Product: {result.get('name', 'Unknown')}\n"
                        #                        f"Description: {result.get('description', 'No description')}\n"
                        #                        f"Price: {result.get('price', 'Price not available')}\n")
                    return "\n".join(formatted_results)
                else:
                    return "No products found matching your query."
            except Exception as e:
                return f"Error searching for products: {str(e)}"
        
        return retrieve_information
    
    def generate_necessary_fields(self, query: str, mongo_query: str) -> List[str]:
        """Generate the final response to the user."""
        try:
            response_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content="""You are a friendly and knowledgeable baking assistant for King Arthur Baking.
                
                Understand the user query and generate a list of fields that need to be brought from the MongoDB collection.
                Make sure that you are bringing the fields that are relevant to the user query.
                And bringing fields as least as possible.

                Here is the MongoDB Collection schema:
                {mongo_schema}

                It is scraped data from https://shop.kingarthurbaking.com/mixes.

                And here is the custom fields description:
                {custom_fields_description}                    
                
                And here is the example document:
                {example_document}
                You have to understand the mongodb schema and the example document.

                You can list any field from the schema.

                example queries and fields:
                ***
                query: most expensive product
                mongo_query: [{'$sort': {'$sales_info.orig_price': -1}}, {'$limit': 1}]
                fields: ["name", "price", "plain_text_description", "images", "details", "Contains"]

                query: most expensive 10 products
                mongo_query: [{'$sort': {'$sales_info.orig_price': -1}}, {'$limit': 10}]
                fields: ["name", "price", "plain_text_description"]

                query: most fallen price product
                mongo_query: [{'$sort': {'$sales_info.savings': -1}}, {'$limit': 1}]
                fields: ["name", "price", "plain_text_description"]

                query: show the image
                mongo_query: ""
                fields: ["name", "images", "details"]

                query: best seller products
                mongo_query: ""
                fields: ["name", "price", "plain_text_description", "custom_fields"]

                query: total products count group by flavor
                mongo_query: [{"$group": {"_id": "$custom_fields._flavor_label", "count": {"$sum": 1}}}]
                fields: ["_id", "count"]

                query: most fallen price product
                mongo_query: [{"$sort": {"$sales_info.savings": -1}}, {"$limit": 1}]
                fields: ["name", "plain_text_description", "sales_info"]

                query: the product with the most reviews
                mongo_query: [{"$sort": {"_review_count": -1}}, {"$limit": 1}]
                fields: ["name", "price", "plain_text_description", "review_summary"]

                query: total products count
                mongo_query: [{"$count": "total_products"}]
                fields: ["total_products"]
                ***
                You should bring all fields that are not in the schema but coming from the MongoDB query.

                We have token limit with you. So you should bring fields as least as possible.
                I will send you the data with the fields you have brought next time.

                Format your response as a list of strings.
                """),
                HumanMessage(content=f"""
                    User Query: {query}
                    MongoDB Query: {mongo_query}
                """)
            ])

            print(f"[{self.user_id}] Generating necessary fields")
            
            response = self.field_generator.invoke(response_prompt.format_messages())
            print(f"[{self.user_id}] Generated necessary fields: {response.content}")
            try:
                # Ensure response.content is a string before parsing
                content = str(response.content) if hasattr(response, 'content') else str(response)
                return json.loads(content)
            except (json.JSONDecodeError, TypeError) as e:
                logger.error(f"[{self.user_id}] Error parsing necessary fields: {e}")
                return ["name", "price", "plain_text_description"]  # Fallback fields             
            
        except Exception as e:
            logger.error(f"[{self.user_id}] Error generating response: {e}")
            response = "I apologize, but I encountered an error while generating a response. Please try again."
            return []
    
    def bson_object_id_to_str(self, doc):
        """Convert BSON ObjectId and datetime objects to strings for JSON serialization."""
        from bson import ObjectId

        extracted_doc = {}

        for field in self.extract_fields:
            print(f"[{self.user_id}] Processing field: {field}")
            if field in doc and doc[field] is not None:
                extracted_doc[field] = str(doc[field])

        print(f"[{self.user_id}] Extracted document: {extracted_doc}")
        
        return extracted_doc

    def _create_mongo_query_tool(self):
        """Create a tool for retrieving information from the database."""
        @tool
        def query_information(query: str) -> str:
            """Convert natural language queries to MongoDB queries and execute them.
            
            Args:
                query (str): Natural language query like 'most expensive products', 'products under $10', 'highest rated mixes'
                
            Note: Pass natural language queries, NOT MongoDB syntax. Examples:
            - 'most expensive products' 
            - 'products under $20'
            - 'highest rated chocolate mixes'
            """
            try:
                # Handle both string and dict inputs for backward compatibility
                if isinstance(query, dict):
                    # If a dict is passed, it might be a direct MongoDB query
                    print(f"[{self.user_id}] WARNING: Received dict instead of string query: {query}")
                    # Try to convert common dict patterns to natural language
                    if 'price' in query and '$exists' in str(query):
                        query = "products with price information"
                    elif not query:  # empty dict
                        query = "all products"
                    else:
                        query = "products matching criteria"
                    print(f"[{self.user_id}] Converted to natural language query: {query}")
                
                # Validate the query parameter
                if not query or not isinstance(query, str) or not query.strip():
                    return "Error: Empty or invalid query provided. Please provide a valid search query."
                
                query = query.strip()
                print(f"[{self.user_id}] Generating MongoDB query for '{query}'")
                
                query_prompt = ChatPromptTemplate.from_messages([
                    SystemMessage(content=f"""
                    You are an MongoDB expert that analyzes user queries about products and generates MongoDB pipeline.
                    
                    Analyze the user query and generate a MongoDB aggregation pipeline for search. Here is the MongoDB Collection schema:
                    {mongo_schema}

                    It is scraped data from https://shop.kingarthurbaking.com/mixes.

                    And here is the custom fields description:
                    {custom_fields_description}                    
                    
                    And here is the example document:
                    {example_document}
                    You have to understand the mongodb schema and the example document.

                    example queries and pipelines:
                    ***
                    query: most expensive product
                    pipeline:
                    [
                        {{"$sort": {{"$sales_info.orig_price": -1}}}},
                        {{"$limit": 1}}
                    ]

                    query: most expensive 10 products
                    pipeline:
                    [
                        {{"$sort": {{"$sales_info.orig_price": -1}}}},
                        {{"$limit": 10}}
                    ]

                    query: most fallen price product
                    pipeline:
                    [
                        {{"$sort": {{"$sales_info.savings": -1}}}},
                        {{"$limit": 1}}
                    ]

                    query: most fallen price 10 products
                    pipeline:
                    [
                        {{"$sort": {{"$sales_info.savings": -1}}}},
                        {{"$limit": 10}}
                    ]

                    query: How many products categories do you have?
                    pipeline:
                    [
                        {{"$match": {{"custom_fields._Child_Category": {{"$ne": None}}}}}},
                        {{"$group": {{"_id": "$custom_fields._Child_Category"}}}},
                        {{"$count": "distinct_child_categories"}}
                    ]

                    query: How many products categories do you have? Make a list of them.
                    pipeline:
                    [
                        {{"$match": {{"custom_fields._Child_Category": {{"$ne": None}}}}}},
                        {{"$group": {{"_id": "$custom_fields._Child_Category"}}}},
                        {{"$group": {{"_id": None, "uniqueChildCategories": {{"$addToSet": "$_id"}}, "count": {{"$sum": 1}}}}}},
                        {{"$project": {{"uniqueChildCategories": 1, "count": 1}}}}
                    ]

                    query: How many flavors are there?
                    pipeline:
                    [
                        {{"$match": {{"custom_fields._flavor_label": {{"$exists": True, "$ne": ''}}}}}},
                        {{"$group": {{"_id": None, "distinct_flavors": {{"$addToSet": "$custom_fields._flavor_label"}}}}}},
                        {{"$project": {{"number_of_flavors": {{"$size": "$distinct_flavors"}}}}}}
                    ]

                    query: Show me the list of flavors.
                    pipeline:
                    [
                        {{"$group": {{"_id": None, "flavors": {{"$addToSet": "$custom_fields._flavor_label"}}}}}},
                        {{"$project": {{"_id": 0, "flavors": 1}}}}
                    ]

                    query: show the products group by flavors.
                    pipeline:
                    [
                        {{"$project": {{"name": 1, "custom_fields._flavor_label": 1}}}},
                        {{"$group": {{"_id": "$custom_fields._flavor_label", "products": {{"$push": {{"product_name": "$name"}}}}}}}}
                    ]
                    ***
                    If there might be lots of documents as a result you should use limit and sort.

                    Generate a valid MongoDB aggregation pipeline (as JSON array) that can be used with collection.aggregate(pipeline).
                    Collection is the pymongo collection. The package is pymongo>=4.6.1.
                    pipeline should be a valid JSON array. Starts with [ and ends with ].
                    Return ONLY the JSON array, no explanations. No other characters in front or back of the array.
                    """),
                    HumanMessage(content=f"User query: {query}")
                ])
                
                response = self.query_generator.invoke(query_prompt.format_messages())
                print(f"[{self.user_id}] Generated MongoDB query: {response.content}")
                
                # Parse the response as JSON
                import json
                response_content = str(response.content) if hasattr(response, 'content') else str(response)
                
                # Try to extract JSON from the response
                try:
                    # Try to parse directly
                    mongo_query = json.loads(response_content)
                except json.JSONDecodeError:
                    # Try to extract JSON from markdown code blocks
                    import re
                    json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response_content, re.DOTALL)
                    if json_match:
                        mongo_query = json.loads(json_match.group(1))
                    else:
                        # Try to find JSON array in the text
                        json_match = re.search(r'\[.*\]', response_content, re.DOTALL)
                        if json_match:
                            mongo_query = json.loads(json_match.group(0))
                        else:
                            raise ValueError("Could not extract valid JSON from response")
                
                print(f'[{self.user_id}] Parsed MongoDB query: {mongo_query}')
                
                # Execute the MongoDB query using the database manager
                if self.db_manager.collection is not None:
                    search_results = list(self.db_manager.collection.aggregate(mongo_query))
                else:
                    search_results = []
                    
                self.extract_fields = self.generate_necessary_fields(query, response_content)
                
                if search_results:
                    # Format results for the LLM
                    formatted_results = []
                    for result in search_results:
                        
                        formatted_results.append(json.dumps(self.bson_object_id_to_str(result), indent=2))
                        # formatted_results.append(f"Product: {result.get('name', 'Unknown')}\n"
                        #                        f"Description: {result.get('description', 'No description')}\n"
                        #                        f"Price: {result.get('price', 'Price not available')}\n")
                    return "\n".join(formatted_results)
                else:
                    return "No products found matching your query."
            except Exception as e:
                return f"Error searching for products: {str(e)}"
        
        return query_information
        
    def create_graph(self):
        """Create the LangGraph workflow with thread-safe checkpointer."""
        workflow = StateGraph(AgentState)

        workflow.add_node("agent", self.call_model)
        workflow.add_node("tools", self.execute_tools)

        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges("agent", self.should_continue)  # Decision after the "agent" node
        workflow.add_edge("tools", "agent")
        
        # Note: We'll use per-thread checkpointers when invoking the graph
        return workflow.compile()
    
    def call_model(self, state: AgentState) -> AgentState:
        logger.info(f"[{self.user_id}] Calling model with state: {state.messages[-1].content if state.messages else 'empty'}")
        with self._lock:
            messages = state.messages
            response = self.llm.invoke(messages)
            # Only append the response if it's not already in the messages
            if not messages or messages[-1] != response:
                state.messages.append(response)
            return state
    
    def should_continue(self, state: AgentState):
        messages = state.messages
        last_message = messages[-1]
        # If the LLM makes a tool call, go to the "tools" node
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"
        # Otherwise, finish the workflow
        return END
    
    def execute_tools(self, state: AgentState) -> AgentState:
        """Execute tools and add results to messages."""
        from langchain_core.messages import ToolMessage
        
        with self._lock:
            messages = state.messages
            last_message = messages[-1]
            
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                tool_results = []
                for tool_call in last_message.tool_calls:
                    # Find the tool by name
                    tool_name = tool_call.get('name', '')
                    tool_args = tool_call.get('args', {})
                    
                    # Add debugging for tool calls
                    print(f"[{self.user_id}] Executing tool '{tool_name}' with args: {tool_args}")
                    
                    # Validate tool arguments before execution
                    if tool_name in ['query_information', 'retrieve_information']:
                        query_param = tool_args.get('query', '')
                        if not query_param or not isinstance(query_param, str) or not query_param.strip():
                            print(f"[{self.user_id}] WARNING: Empty or invalid query parameter for tool '{tool_name}': {query_param}")
                            tool_result = f"Error: Tool '{tool_name}' received empty or invalid query parameter."
                            # Create tool message
                            tool_message = ToolMessage(
                                content=tool_result,
                                tool_call_id=tool_call.get('id', ''),
                                name=tool_name
                            )
                            tool_results.append(tool_message)
                            continue
                    
                    # Find and execute the appropriate tool
                    tool_result = None
                    for tool in self.tools:
                        if tool.name == tool_name:
                            try:
                                # Call the tool using invoke method
                                tool_result = tool.invoke(tool_args)
                                break
                            except Exception as e:
                                print(f"[{self.user_id}] ERROR: Tool execution failed for '{tool_name}': {str(e)}")
                                tool_result = f"Error executing {tool_name}: {str(e)}"
                                break
                    
                    if tool_result is None:
                        tool_result = f"Tool '{tool_name}' not found"
                    
                    # Create tool message
                    tool_message = ToolMessage(
                        content=tool_result,
                        tool_call_id=tool_call.get('id', ''),
                        name=tool_name
                    )
                    tool_results.append(tool_message)
                
                # Add tool results to messages
                state.messages.extend(tool_results)
            
            return state

    def get_recommendations(self, state: AgentState) -> AgentState:
        """Get product recommendations based on preferences."""
        try:
            keywords = state.context.get("keywords", [])
            preferences = keywords + state.context.get("requirements", [])
            
            recommendations = self.db_manager.get_product_recommendations(
                preferences, limit=8
            )
            
            state.search_results = recommendations
            state.tool_calls.append("get_recommendations")
            state.step = "recommended"
            
            logger.info(f"[{self.user_id}] Generated {len(recommendations)} recommendations")
            return state
            
        except Exception as e:
            logger.error(f"[{self.user_id}] Error getting recommendations: {e}")
            state.search_results = []
            return state
  
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)."""
        return int(len(text.split()) * 1.3)  # Rough estimate: 1.3 tokens per word
    
    def _truncate_conversation_history(self, messages: List[Any], max_tokens: int = 30000) -> List[Any]:
        """Truncate conversation history to stay within token limits."""
        if not messages:
            return messages
        
        # Always keep the system message if it exists
        system_messages = [msg for msg in messages if isinstance(msg, SystemMessage)]
        other_messages = [msg for msg in messages if not isinstance(msg, SystemMessage)]
        
        # Calculate tokens for system messages
        system_tokens = sum(self._estimate_tokens(str(msg.content)) for msg in system_messages)
        remaining_tokens = max_tokens - system_tokens - 4000  # Reserve 4000 tokens for response
        
        if remaining_tokens <= 0:
            # If system message is too long, just keep basic system prompt
            return [SystemMessage(content=self.system_prompt)]
        
        # Keep recent messages within token limit
        truncated_messages = []
        current_tokens = 0
        
        # Start from the end (most recent) and work backwards
        for msg in reversed(other_messages):
            msg_tokens = self._estimate_tokens(str(msg.content))
            if current_tokens + msg_tokens <= remaining_tokens:
                truncated_messages.insert(0, msg)
                current_tokens += msg_tokens
            else:
                break
        
        # Combine system messages with truncated conversation
        return system_messages + truncated_messages

    def chat(self, user_query: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
        """Main chat interface with thread-safe operations."""
        try:
            # Use provided thread_id or create a new one
            if thread_id is None:
                thread_id = f"chat_{self.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Get thread-safe checkpointer for this thread
            checkpointer = get_thread_safe_checkpointer(thread_id)
            
            # Create configuration for the checkpointer (compatible with RunnableConfig)
            from langchain_core.runnables import RunnableConfig
            config = RunnableConfig(configurable={"thread_id": thread_id})
            
            # Create a new graph instance with the specific checkpointer for this thread
            workflow = StateGraph(AgentState)
            workflow.add_node("agent", self.call_model)
            workflow.add_node("tools", self.execute_tools)
            workflow.add_edge(START, "agent")
            workflow.add_conditional_edges("agent", self.should_continue)
            workflow.add_edge("tools", "agent")
            graph_with_checkpointer = workflow.compile(checkpointer=checkpointer)
            
            # Try to get existing state from checkpointer
            try:
                # Get the current state from the checkpointer
                current_state = graph_with_checkpointer.get_state(config)
                if current_state and current_state.values.get("messages"):
                    # Add new user message to existing conversation
                    existing_messages = current_state.values["messages"]
                    new_message = HumanMessage(content=user_query)
                    existing_messages.append(new_message)
                    
                    # Truncate conversation history to avoid token limits
                    truncated_messages = self._truncate_conversation_history(existing_messages)
                    
                    initial_state = AgentState(
                        user_query=user_query,
                        messages=truncated_messages,
                        search_results=current_state.values.get("search_results", []),
                        analysis=current_state.values.get("analysis", ""),
                        response=current_state.values.get("response", ""),
                        tool_calls=current_state.values.get("tool_calls", []),
                        context=current_state.values.get("context", {}),
                        step=current_state.values.get("step", "start")
                    )
                else:
                    # First message in conversation
                    initial_state = AgentState(
                        user_query=user_query,
                        messages=[
                            SystemMessage(content=self.system_prompt),
                            HumanMessage(content=user_query)
                        ]
                    )
            except:
                # Fallback to new conversation if checkpointer fails
                initial_state = AgentState(
                    user_query=user_query,
                    messages=[
                        SystemMessage(content=self.system_prompt),
                        HumanMessage(content=user_query)
                    ]
                )
            
            # Run the graph with proper configuration
            final_state = graph_with_checkpointer.invoke(initial_state, config)
            
            # Extract and format the response properly
            try:
                # Get the last assistant message
                messages = final_state.get("messages", []) if isinstance(final_state, dict) else getattr(final_state, "messages", [])
                
                assistant_content = ""
                products = []
                
                # Find the last AI/assistant message
                for msg in reversed(messages):
                    if hasattr(msg, '__class__') and 'AI' in msg.__class__.__name__:
                        assistant_content = str(msg.content)
                        break
                
                # Extract products from search results if available
                search_results = final_state.get("search_results", []) if isinstance(final_state, dict) else getattr(final_state, "search_results", [])
                
                # Format search results as products
                if search_results:
                    for result in search_results[:5]:  # Limit to 5 products
                        if isinstance(result, dict):
                            product = {
                                "name": result.get("name", "Unknown Product"),
                                "price": result.get("price", "Price not available"),
                                "description": str(result.get("plain_text_description", result.get("description", "No description")))[:200],
                                "url": result.get("url", "")
                            }
                            products.append(product)
                
                # Return properly formatted response
                return {
                    "messages": messages,
                    "response": assistant_content,
                    "products": products,
                    "search_results": search_results,
                    "analysis": final_state.get("analysis", "") if isinstance(final_state, dict) else getattr(final_state, "analysis", ""),
                    "tool_calls": final_state.get("tool_calls", []) if isinstance(final_state, dict) else getattr(final_state, "tool_calls", []),
                    "step": final_state.get("step", "completed") if isinstance(final_state, dict) else getattr(final_state, "step", "completed")
                }
                
            except Exception as format_error:
                logger.error(f"[{self.user_id}] Error formatting response: {format_error}")
                # Fallback response
                return {
                    "messages": messages if 'messages' in locals() else [],
                    "response": assistant_content if 'assistant_content' in locals() else "I processed your request.",
                    "products": [],
                    "search_results": [],
                    "analysis": "",
                    "tool_calls": [],
                    "step": "completed"
                }
            
        except Exception as e:
            logger.error(f"[{self.user_id}] Error in chat: {e}")
            return {
                "response": "I apologize, but I encountered an error. Please try again.",
                "products": [],
                "analysis": "",
                "tool_calls": [],
                "step": "error"
            }
    
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics."""
        try:
            db_stats = self.db_manager.get_stats()
            
            return {
                "user_id": self.user_id,
                "database_stats": db_stats,
                "model_info": {
                    "llm_model": settings.llm_model,
                    "embedding_model": settings.embedding_model,
                    "temperature": settings.temperature
                },
                "capabilities": [
                    "Product Search",
                    "Semantic Search",
                    "Product Recommendations",
                    "Product Comparison",
                    "Baking Advice"
                ]
            }
            
        except Exception as e:
            logger.error(f"[{self.user_id}] Error getting stats: {e}")
            return {}

def main():
    """Main function to test the agent."""
    agent = KingArthurBakingAgent()
    
    # Test queries
    test_queries = [
        "I'm looking for a chocolate cake mix",
        "Can you recommend some easy baking mixes for beginners?",
        "Compare different pancake mixes",
        "What ingredients are in your bread mixes?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*50}")
        print(f"Query: {query}")
        print('='*50)
        
        result = agent.chat(query)
        print(f"Response: {result['response']}")
        print(f"Products found: {len(result['products'])}")
        print(f"Tools used: {result['tool_calls']}")

if __name__ == "__main__":
    main() 