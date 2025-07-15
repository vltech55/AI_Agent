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
If you need to look up some information before asking a follow up question, you are allowed to do that!

There are two tools you can use to get information:
***
1. retrieve_information: This tool performs semantic/hybrid search over product descriptions, ingredients, and details. Use this for natural language queries like "chocolate cake mix" or "gluten-free options".
2. query_information: This tool accepts natural language queries that get converted to MongoDB queries. Use this for specific queries like "most expensive products" or "products under $10". Do NOT pass MongoDB syntax directly - use natural language.

If the user wants exact count, price, images, type, or list of products and query with exact information. You should use query_information tool.
If the user wants you to recommend, which means user don't know exact information. You should use retrieve_information tool.
You can use both tools together.
When you using query_information tool, first get the total count of results and then get the documents. The response must have the total count of the result.
Here is the example:
user query: show me all the products under $50
**
step 1:
query: How many products are there under $50
pipeline: [{{"$match": {{"price": {{"$lt": 50}}}}}}, {{"$count": "products_under_50"}}]
get the total count of the result.

step 2:
query: Show me the list of products under $50
pipeline: [{{"$match": {{"price": {{"$lt": 50}}}}}}, {{"$limit": 10}}]
get the list of products under $50.

step 3:
show the total count of the result and only 10 of the list of products under $50.
**
***

Here is the important rules that you have to follow:
***
1. You have to make response as fast as you can.
2. Always provide the total count of the results.
3. After gathering information, you have to generate a simple and exact response from the information you have gathered to the user's query.
4. It must be well-fomatted, well-structured and easy to understand.
5. If the response is less-detailed, you should provide the sales_info information, until less-detailed then provide the description, and then images, and then details, etc.
***

Make sure that:
1. You are answering the user's query exactly.
2. You are providing specific product recommendations with details.
3. Your response is well formatted and easy to understand.
4. Always sort the products by price, reviews, etc. If there is no sort, you should sort by price. Decide ascending or descending according to the user's query.
5. According to the user's query, you should provide recommendations.
6. If the user's query is not clear, you should ask for more information.
7. If the user's query is not related to the products, you should say that you are not sure about the product.

Example Tone and Style:
1. "I'd be delighted to help you choose the perfect mix! Are you baking for a special occasion or just looking for something new to try at home?"
2. "Absolutely! Our gluten-free bread mix is one of our top sellers, and it's super easy to use. Would you like me to walk you through the ingredients or recipe?"
3. "Great choice—our seasonal cookie bundle is on sale right now! Let me share a bit about what's included..."
4. "All of our mixes are made with premium, non-GMO ingredients—let me know if you have any specific dietary needs, and I'll help you find the perfect product!"

Always keep the focus on making the customer's baking experience easy, delicious, and enjoyable with our KING ARTHUR mixes.
"""

mongo_schema = """"""
example_document = """"""
custom_fields_description = """Here's an brief explanation of each field:

{
name: The name of the product.
SKU: (Stock Keeping Unit)A unique identifier for the product used for inventory management.
price: The price of the product. This field is for additional information. You should not use this field for search but only for sort. All the search about price should be done with the sales_info field.
url: The page of website https://shop.kingarthurbaking.com/ that describes about this product. This field is usually https://shop.kingarthurbaking.com/{path}
aria_label: The label that showed in the https://shop.kingarthurbaking.com/ usually contains name and price info.
entity_id: The number to identify the product. It is used to get the product review details.
plain_text_description: The full, detailed description of the product. *This field is useful for providing information"
path: The subdomain of the item page.
brand: The brand of the product. It can be one of two values "KINGARTHUR" and "FRONTIERSO"
categories: The list of json that indicates the subclasses that the product belong. *Don't use this field for search, just for additional information. You have to search about the categories with the custom_fields" for example if it [{"name": "Mixes", "path": "/mixes"}, {"name": "Gluten-Free", "path": "/gluten-free"}], then we can find the product in two subclasses the pages are https://shop.kingarthurbaking.com/mixes and https://shop.kingarthurbaking.com/gluten-free. This field is low-level information because we are only concerning about products in https://shop.kingarthurbaking.com/mixes. This field can be use for additional information.

custom_fields: The field that represents the essential and important information for the product.
    {
        swym-disabled: Indicates whether the product is impacted by certain external services, possibly related to wishlist services (Swym).
        _Promo_Exclusion: Indicates if the product is excluded from promotions.
        Various badge fields(e.g., _badge_glutenfree, _badge_kosherpareve): These fields indicate different certifications or attributes, such as whether the product is gluten-free, kosher, organic, made in the USA, etc. All are marked "No," meaning these attributes do not apply to the product.
        _Parent_Category: The big category to which this product belongs. *This is not main category.*
        _Child_Category: A subcategory within the parent category. This is the main category that classifies the products. It can be one of 10 different categories. ["0", "Bread", "Cake & Pie", "Cookies", "Dessert Cups", "Doughnuts", "Doughnuts & Muffins", "Frostings & Fillings", "Gluten-Free", "Mix & Pan Sets"] * This field is important for providing information to users*
        _Online_Exclusive: Indicates whether the product is exclusive to online sales. A value of 0 suggests it's not online exclusive.
        _sale_label: Indicates if the product is on sale. This means the "SALE" badge is showed on the image of the product in the main page.
        _clearance_label: Indicates if the product is on clearance. No Visual Effects.
        _new_label: Shows that the product is considered new. This means the "NEW" badge is showed on the image of the product in the main page.
        _label_path, _package_path: Paths to the product's label and packaging files, which may be used for display purposes.
        _type_label: Descriptions of the product type (Dessert, Snack). It can be one of 14 different things ["Biscuits", "Bread", "Brownies", "Cake", "Cookie", "Cookies", "Dog Biscuits", "Doughnuts", "Frosting", "Muffins & Quick Bread", "Pancakes & Waffles", "Pie", "Scone", "Scones"]
        _flavor_label: The flavor of the product. It is usually used for Filtering. It can be one of 15 different things. ["Apple", "Apricot", "Banana", "Berry", "Blueberry", "Buttermilk", "Chocolate", "Cinnamon", "Coconut", "Cranberry-Orange", "Eggnog", "Fruit", "Fruit & Nut", "Garlic", "Gingerbread"] *This field is important for providing information to users*
        _category_label: The category of the product. It can be one of 8 different categories. ["Bread Baking", "Breakfast", "Celebration", "Dessert", "Holiday", "Pizza", "Scones", "Snack"] It is usually used for Filtering. *This field is important for providing information to users*
        _dietary_label: The dietary label of the product. It can be one of 2 different things ["Gluten-Free", "Keto"]. It is usually used for Filtering. *This field is important for providing information to users*
        _review_avg_score: The average customer review score.
        _review_count: The number of reviews the product has received.
        _Special_Savings, _special_savings_label: Indicates the absence of any special savings associated with the product.
    }
ingredients: The ingredients that the product have
Contains: The material that the product have
allergen_link: The brief information about the allergy with this product.
details: The list of detail about the product
images: The list of image url and alt_text of the product.
review_summary: Information about the reviews
    {
        number_of_reviews: The number of reviews the product has received. Same as custom_fields._review_count
        average_rating: The average customer review score. Same as custom_fields._review_avg_score
        1: The number of star 1 reviews
        2: The number of star 2 reviews
        3: The number of star 3 reviews
        4: The number of star 4 reviews
        5: The number of star 5 reviews
    }
sales_info: Information about the price.
    {
        orig_price: The original price without the Tax
        sr_only: The price with the Tax
        saving: The different between sr_only and org_price. This indicates the price is fallen and we can buy it cheaper.
        bulk_promo: The information about the services we have with the sale. for example. "Buy Any 5+/Save $4" It means if we buy this product more than 5. We can save $4.
    }
nutrition_info: Information about the Nutritions that the price have.
    {
        nutrition_link: link to the pdf file that describes about the nutrition.
    }

"""

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

                example queries and mongo_query and example response according to the query:
                ***
                query: most expensive product
                mongo_query: [{'$sort': {'$sales_info.orig_price': -1}}, {'$limit': 1}]
                example response: ["name", "price", "plain_text_description", "images", "details", "Contains"]

                query: most expensive 10 products
                mongo_query: [{'$sort': {'$sales_info.orig_price': -1}}, {'$limit': 10}]
                example response: ["name", "price", "plain_text_description"]

                query: most fallen price product
                mongo_query: [{'$sort': {'$sales_info.savings': -1}}, {'$limit': 1}]
                example response: ["name", "price", "plain_text_description"]

                query: show the image
                mongo_query: ""
                example response: ["name", "images", "details"]

                query: best seller products
                mongo_query: ""
                example response: ["name", "price", "plain_text_description", "custom_fields"]

                query: total products count group by flavor
                mongo_query: [{"$group": {"_id": "$custom_fields._flavor_label", "count": {"$sum": 1}}}]
                example response: ["_id", "count"]

                query: most fallen price product
                mongo_query: [{"$sort": {"$sales_info.savings": -1}}, {"$limit": 1}]
                example response: ["name", "plain_text_description", "sales_info"]

                query: fallen price among top 10 expensive products
                mongo_query: [{"$sort": {"$sales_info.orig_price": -1}}, {"$limit": 10}, {"$sort": {"$sales_info.savings": -1}}]
                example response: ["name", "plain_text_description", "sales_info"]

                query: the product with the most reviews
                mongo_query: [{"$sort": {"review_summary.number_of_reviews": -1}}, {"$limit": 1}]
                example response: ["name", "price", "plain_text_description", "review_summary"]

                query: the different brands of products
                mongo_query: [{"$group": {"_id": "$brand"}},{"$project": {"_id": 0, "brand": "$_id"}}]
                example response: ["brand"]

                query: total products count
                mongo_query: [{"$count": "total_products"}]
                example response: ["total_products"]
                ***
                You should bring all fields that are not in the schema but coming from the MongoDB query all the fields fromthe "$project" part. 

                We have token limit with you. So you should bring fields as least as possible.
                I will send you the data with the fields you have brought next time.

                Response format:   starts with [ and ends with ]
                Format your response as a list of strings. Do not include any other information.
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
                        {{"$match": {{"custom_fields._Child_Category": {{"$ne": null}}}}}},
                        {{"$group": {{"_id": "$custom_fields._Child_Category"}}}},
                        {{"$count": "distinct_child_categories"}}
                    ]

                    query: How many products categories do you have? Make a list of them.
                    pipeline:
                    [
                        {{"$match": {{"custom_fields._Child_Category": {{"$ne": null}}}}}},
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

                    query: show the list of different brands of products
                    pipeline:[
                        {{"$match": {{"brand": {{"$ne": null}}}}}},
                        {{"$group": {{"_id": "$brand"}}}},
                        {{"$project": {{"brand": "$_id", "_id": 0}}}}
                    ]

                    query: show all the products under $50
                    pipeline:[
                        {{"$match": {{"price": {{"$lt": 50}}}}}},
                        {{"$sort": {{"price": -1}}}},
                        {{"$limit": 10}}
                    ]

                    query: show all the products more expensive than $50
                    pipeline:[
                        {{"$match": {{"price": {{"$gt": 50}}}}}},
                        {{"$sort": {{"price": 1}}}},
                        {{"$limit": 10}}
                    ]

                    query: how many products are there under $50
                    pipeline:[
                        {{"$match": {{"price": {{"$lt": 50}}}}}},
                        {{"$count": "products_under_50"}}
                    ]

                    ***
                    Always use $match to filter the documents especially for avoiding none or null values.
                    Always use $limit to limit the documents and reduce the response.
                    Always use $sort to sort the documents by the price. ascending or descending is due to the user query.
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
                print(f"[{self.user_id}] Response content: {response_content}")
                
                # Try to extract JSON from the response
                try:
                    # Try to parse directly
                    mongo_query = json.loads(response_content)
                    print(f"[{self.user_id}] Parsed MongoDB query: {mongo_query}")
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

                print(f"[{self.user_id}] Search results: {search_results}")
                    
                self.extract_fields = self.generate_necessary_fields(query, response_content)
                
                if search_results:
                    print(f"[{self.user_id}] Search results: {search_results}")
                    # Format results for the LLM
                    formatted_results = []
                    for result in search_results:
                        print(f"[{self.user_id}] Result: {result}")
                        
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
    
    def _truncate_conversation_history(self, messages: List[Any], max_tokens: int = 200000) -> List[Any]:
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