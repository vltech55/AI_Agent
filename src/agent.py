import json
import logging
from typing import List, Dict, Optional, Tuple, Any
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field
import re
from datetime import datetime

from .database import MongoDBManager
# Removed AtlasVectorSearchService - using database search methods directly
from .config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

class KingArthurBakingAgent:
    """AI Agent for King Arthur Baking mixes with advanced retrieval and reasoning."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            openai_api_key=settings.openai_api_key
        )
        self.db_manager = MongoDBManager()
        # Use database search methods directly
        self.graph = self.create_graph()
        
    def create_graph(self) -> StateGraph:
        """Create the LangGraph workflow."""
        workflow = StateGraph(AgentState)
        
        # Define nodes
        workflow.add_node("analyze_query", self.analyze_query)
        workflow.add_node("search_products", self.search_products)
        workflow.add_node("reason_about_results", self.reason_about_results)
        workflow.add_node("generate_response", self.generate_response)
        workflow.add_node("get_recommendations", self.get_recommendations)
        workflow.add_node("compare_products", self.compare_products)
        
        # Define edges
        workflow.set_entry_point("analyze_query")
        
        # Conditional routing based on query analysis
        workflow.add_conditional_edges(
            "analyze_query",
            self.route_query,
            {
                "search": "search_products",
                "recommendations": "get_recommendations",
                "compare": "compare_products"
            }
        )
        
        # Continue to reasoning after search/recommendations/compare
        workflow.add_edge("search_products", "reason_about_results")
        workflow.add_edge("get_recommendations", "reason_about_results")
        workflow.add_edge("compare_products", "reason_about_results")
        
        # Generate final response
        workflow.add_edge("reason_about_results", "generate_response")
        workflow.add_edge("generate_response", END)
        
        return workflow.compile()
    
    def analyze_query(self, state: AgentState) -> AgentState:
        """Analyze the user query to determine intent and extract key information."""
        try:
            analysis_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content="""You are an AI assistant that analyzes user queries about baking mixes.
                
                Analyze the user query and determine:
                1. Intent: search, recommendations, compare, or general
                2. Keywords: Extract relevant baking terms, ingredients, or product types
                3. Specific requirements: dietary restrictions, difficulty level, etc.
                4. Context: Any additional context or preferences
                
                Format your response as JSON with these fields:
                - intent: one of [search, recommendations, compare, general]
                - keywords: list of relevant terms
                - requirements: list of specific requirements
                - context: any additional context
                """),
                HumanMessage(content=f"User query: {state.user_query}")
            ])
            
            response = self.llm.invoke(analysis_prompt.format_messages())
            
            # Try to parse as JSON, fallback to simple analysis
            try:
                analysis = json.loads(response.content)
            except:
                analysis = {
                    "intent": "search",
                    "keywords": re.findall(r'\b\w+\b', state.user_query.lower()),
                    "requirements": [],
                    "context": ""
                }
            
            state.analysis = response.content
            state.context = analysis
            state.step = "analyzed"
            
            logger.info(f"Query analyzed - Intent: {analysis.get('intent', 'unknown')}")
            return state
            
        except Exception as e:
            logger.error(f"Error analyzing query: {e}")
            state.context = {"intent": "search", "keywords": [], "requirements": [], "context": ""}
            return state
    
    def route_query(self, state: AgentState) -> str:
        """Route the query based on analysis."""
        intent = state.context.get("intent", "search")
        
        if intent == "recommendations":
            return "recommendations"
        elif intent == "compare":
            return "compare"
        else:
            return "search"
    
    def search_products(self, state: AgentState) -> AgentState:
        """Search for products based on the query."""
        try:
            # Use hybrid search for best results
            search_results = self.db_manager.hybrid_search(state.user_query, limit=10)
            
            # If no results, try with keywords
            if not search_results:
                keywords = " ".join(state.context.get("keywords", []))
                if keywords:
                    search_results = self.db_manager.hybrid_search(keywords, limit=10)
            
            state.search_results = search_results
            state.tool_calls.append("hybrid_search")
            state.step = "searched"
            
            logger.info(f"Found {len(search_results)} products")
            return state
            
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            state.search_results = []
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
            
            logger.info(f"Generated {len(recommendations)} recommendations")
            return state
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            state.search_results = []
            return state
    
    def compare_products(self, state: AgentState) -> AgentState:
        """Compare products based on the query."""
        try:
            # Extract product names or IDs from query
            query_lower = state.user_query.lower()
            
            # First, search for products mentioned in the query
            products_to_compare = self.db_manager.hybrid_search(state.user_query, limit=5)
            
            # If we have products, get similar ones for comparison
            if products_to_compare:
                comparison_results = []
                for product in products_to_compare[:3]:  # Compare top 3
                    similar = self.db_manager.find_similar_products(
                        str(product['_id']), limit=2
                    )
                    comparison_results.extend([product] + similar)
                
                # Remove duplicates
                seen_ids = set()
                unique_results = []
                for product in comparison_results:
                    product_id = str(product['_id'])
                    if product_id not in seen_ids:
                        seen_ids.add(product_id)
                        unique_results.append(product)
                
                state.search_results = unique_results[:6]  # Limit to 6 for comparison
            else:
                state.search_results = []
            
            state.tool_calls.append("compare_products")
            state.step = "compared"
            
            logger.info(f"Prepared {len(state.search_results)} products for comparison")
            return state
            
        except Exception as e:
            logger.error(f"Error comparing products: {e}")
            state.search_results = []
            return state
    
    def reason_about_results(self, state: AgentState) -> AgentState:
        """Reason about the search results and provide insights."""
        try:
            if not state.search_results:
                state.analysis = "No relevant products found for the query."
                return state
            
            # Prepare context for reasoning
            products_summary = []
            for product in state.search_results:
                summary = {
                    "name": product.get("name", "Unknown"),
                    "description": product.get("description", "")[:200] + "..." if len(product.get("description", "")) > 200 else product.get("description", ""),
                    "price": product.get("price", ""),
                    "ingredients": product.get("ingredients", "")[:100] + "..." if len(product.get("ingredients", "")) > 100 else product.get("ingredients", ""),
                    "features": product.get("features", [])[:3]  # Top 3 features
                }
                products_summary.append(summary)
            
            reasoning_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content="""You are an expert baking assistant. Analyze the search results and provide insights.
                
                Based on the user query and the found products, provide:
                1. How well the products match the user's needs
                2. Key differences between products
                3. Recommendations based on different use cases
                4. Any notable ingredients or features
                5. Suggestions for the user
                
                Be helpful, informative, and focus on practical baking advice.
                """),
                HumanMessage(content=f"""
                User Query: {state.user_query}
                
                Found Products:
                {json.dumps(products_summary, indent=2)}
                
                Provide your analysis and insights:
                """)
            ])
            
            response = self.llm.invoke(reasoning_prompt.format_messages())
            state.analysis = response.content
            state.step = "reasoned"
            
            logger.info("Completed reasoning about results")
            return state
            
        except Exception as e:
            logger.error(f"Error reasoning about results: {e}")
            state.analysis = "Error analyzing the search results."
            return state
    
    def generate_response(self, state: AgentState) -> AgentState:
        """Generate the final response to the user."""
        try:
            # Prepare product details for response
            product_details = []
            for product in state.search_results:
                details = {
                    "name": product.get("name", "Unknown"),
                    "description": product.get("description", ""),
                    "price": product.get("price", ""),
                    "ingredients": product.get("ingredients", ""),
                    "instructions": product.get("instructions", ""),
                    "features": product.get("features", []),
                    "url": product.get("url", "")
                }
                product_details.append(details)
            
            response_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content="""You are a friendly and knowledgeable baking assistant for King Arthur Baking.
                
                Generate a helpful response that:
                1. Directly answers the user's question
                2. Provides specific product recommendations with details
                3. Includes practical baking tips when relevant
                4. Mentions prices and key features
                5. Suggests where to find more information
                
                Format your response in a conversational, helpful tone.
                Include specific product names, prices, and key details.
                """),
                HumanMessage(content=f"""
                User Query: {state.user_query}
                
                Analysis: {state.analysis}
                
                Products Found:
                {json.dumps(product_details, indent=2)}
                
                Generate a helpful response:
                """)
            ])
            
            response = self.llm.invoke(response_prompt.format_messages())
            state.response = response.content
            state.step = "completed"
            
            logger.info("Generated final response")
            return state
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            state.response = "I apologize, but I encountered an error while generating a response. Please try again."
            return state
    
    def chat(self, user_query: str) -> Dict[str, Any]:
        """Main chat interface."""
        try:
            # Initialize state
            initial_state = AgentState(
                user_query=user_query,
                messages=[HumanMessage(content=user_query)]
            )
            
            # Run the graph
            final_state = self.graph.invoke(initial_state)
            
            # Handle both AgentState objects and dictionaries
            if isinstance(final_state, dict):
                return {
                    "response": final_state.get("response", "I apologize, but I couldn't generate a proper response."),
                    "products": final_state.get("search_results", []),
                    "analysis": final_state.get("analysis", ""),
                    "tool_calls": final_state.get("tool_calls", []),
                    "step": final_state.get("step", "unknown")
                }
            else:
                return {
                    "response": final_state.response,
                    "products": final_state.search_results,
                    "analysis": final_state.analysis,
                    "tool_calls": final_state.tool_calls,
                    "step": final_state.step
                }
            
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return {
                "response": "I apologize, but I encountered an error. Please try again.",
                "products": [],
                "analysis": "",
                "tool_calls": [],
                "step": "error"
            }
    
    def get_graph_visualization(self) -> Dict[str, Any]:
        """Get a visualization of the agent's graph structure."""
        try:
            # Create a simple representation of the graph
            graph_data = {
                "nodes": [
                    {"id": "analyze_query", "label": "Analyze Query", "type": "process"},
                    {"id": "search_products", "label": "Search Products", "type": "action"},
                    {"id": "get_recommendations", "label": "Get Recommendations", "type": "action"},
                    {"id": "compare_products", "label": "Compare Products", "type": "action"},
                    {"id": "reason_about_results", "label": "Reason About Results", "type": "process"},
                    {"id": "generate_response", "label": "Generate Response", "type": "output"}
                ],
                "edges": [
                    {"from": "analyze_query", "to": "search_products", "condition": "search"},
                    {"from": "analyze_query", "to": "get_recommendations", "condition": "recommendations"},
                    {"from": "analyze_query", "to": "compare_products", "condition": "compare"},
                    {"from": "search_products", "to": "reason_about_results"},
                    {"from": "get_recommendations", "to": "reason_about_results"},
                    {"from": "compare_products", "to": "reason_about_results"},
                    {"from": "reason_about_results", "to": "generate_response"}
                ]
            }
            
            return graph_data
            
        except Exception as e:
            logger.error(f"Error getting graph visualization: {e}")
            return {"nodes": [], "edges": []}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics."""
        try:
            db_stats = self.db_manager.get_stats()
            
            return {
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
            logger.error(f"Error getting stats: {e}")
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