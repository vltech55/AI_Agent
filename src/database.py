import json
import logging
from typing import List, Dict, Optional, Any
from pymongo.operations import SearchIndexModel
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError, PyMongoError
from datetime import datetime
import openai
import threading
import time
from functools import lru_cache

from .config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global connection pool - shared across all instances for efficiency
_connection_pool = None
_pool_lock = threading.Lock()

class MongoDBManager:
    """Thread-safe MongoDB manager with connection pooling for multi-user access."""
    
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self.collection: Optional[Collection] = None
        self._lock = threading.Lock()  # Instance-level lock for thread safety
        self.connect()

    def connect(self):
        """Connect to MongoDB Atlas with optimized connection pooling for multi-user access."""
        global _connection_pool, _pool_lock
        
        try:
            with _pool_lock:
                # Use shared connection pool if available
                if _connection_pool is None:
                    logger.info("Creating new MongoDB connection pool for multi-user access...")
                    
                    # Strategy: Optimized connection string with enhanced pooling for concurrent users
                    base_uri = settings.mongodb_uri
                    
                    # Enhanced SSL and pooling parameters for production multi-user deployment
                    ssl_params = [
                        "tls=true",
                        "tlsAllowInvalidCertificates=true", 
                        "tlsAllowInvalidHostnames=true",
                        "serverSelectionTimeoutMS=3000",    # Fast failure detection
                        "socketTimeoutMS=15000",            # Increased for concurrent operations
                        "connectTimeoutMS=3000",            # Fast connection timeout
                        "maxPoolSize=100",                  # Large pool for many concurrent users
                        "minPoolSize=10",                   # Keep minimum connections alive
                        "maxIdleTimeMS=45000",              # Connection idle timeout
                        "waitQueueTimeoutMS=3000",          # Queue timeout for connection requests
                        "maxConnecting=10",                 # Limit concurrent connection attempts
                        "heartbeatFrequencyMS=5000",        # Regular health checks
                        "retryWrites=true",                 # Enable retryable writes
                        "retryReads=true",                  # Enable retryable reads
                        "readPreference=secondaryPreferred" # Distribute read load
                    ]
                    
                    if '?' in base_uri:
                        # Check if SSL params already exist
                        if 'tls=' not in base_uri:
                            ssl_uri = f"{base_uri}&{'&'.join(ssl_params)}"
                        else:
                            ssl_uri = base_uri
                    else:
                        ssl_uri = f"{base_uri}?{'&'.join(ssl_params)}"
                    
                    _connection_pool = MongoClient(ssl_uri)
                    
                    # Test the connection pool
                    _connection_pool.admin.command('ping')
                    logger.info("Successfully created MongoDB connection pool for multi-user access")
                
                # Use the shared connection pool
                self.client = _connection_pool
                self.db = self.client[settings.mongodb_db_name]
                self.collection = self.db[settings.mongodb_collection_name]
                
                logger.info(f"Connected to MongoDB using shared pool (thread: {threading.current_thread().name})")
                
                # Create indexes (only if collection is available)
                if self.collection is not None:
                    try:
                        # Use a background thread for index creation to avoid blocking
                        threading.Thread(
                            target=self._create_indexes_async,
                            daemon=True,
                            name="IndexCreator"
                        ).start()
                    except Exception as index_error:
                        logger.warning(f"Index creation scheduling failed (non-critical): {index_error}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            logger.error("Please check your MongoDB URI and network connectivity")
            logger.error("For Hugging Face Spaces deployment, ensure SSL parameters are in the connection string")
            
            # Set to None on failure but don't raise - let app continue with degraded functionality
            with self._lock:
                self.client = None
                self.db = None
                self.collection = None

    def _create_indexes_async(self):
        """Create indexes in background thread to avoid blocking user operations."""
        try:
            time.sleep(1)  # Brief delay to let connections stabilize
            self.create_indexes()
        except Exception as e:
            logger.warning(f"Background index creation failed (non-critical): {e}")

    def create_indexes(self):
        """Create necessary indexes for the collection with thread safety."""
        if self.collection is None:
            return
            
        try:
            with self._lock:
                # Check if indexes already exist to avoid recreation
                existing_indexes = [idx['name'] for idx in self.collection.list_indexes()]
                
                if 'text_index' not in existing_indexes:
                    search_idx = SearchIndexModel(
                        definition={
                            "mappings": {
                                "dynamic": True
                            }
                        },
                        name="text_index",
                    )
                    
                    if 'vector_index' not in existing_indexes:
                        vector_idx = SearchIndexModel(
                            definition={
                                "fields": [
                                {
                                    "type": "vector",
                                    "numDimensions": 1536,
                                    "path": "embedding",
                                    "similarity": "cosine"
                                }
                                ]
                            },
                            name="vector_index",
                            type="vectorSearch",
                        )
                        indexes = [search_idx, vector_idx]
                    else:
                        indexes = [search_idx]
                    
                    self.collection.create_search_indexes(models=indexes)
                    logger.info("Indexes created successfully")
                else:
                    logger.info("Indexes already exist, skipping creation")

        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")

    @lru_cache(maxsize=1000)  # Cache embeddings to reduce API calls
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI with caching."""
        try:
            # Normalize text for better cache hits
            normalized_text = text.strip().lower()
            
            client = openai.OpenAI(api_key=settings.openai_api_key)
            response = client.embeddings.create(
                model=settings.embedding_model,
                input=normalized_text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return []
    
    def generate_searchable_text(self, product: Dict) -> str:
        """Generate searchable text for a product."""
        name = product.get('name', '')
        description = product.get('plain_text_description', '')
        ingredients = product.get('ingredients', '')
        details = ', '.join(product.get('details', ''))
        contains = ', '.join(product.get('Contains', ''))
        custom_fields = product.get('custom_fields', '')
        allergens = product.get('allergen_link', '')
        nutrition = json.dumps(product.get('nutrition', ''))

        searchable_text = f"This is a mix named {name}. {description}. The ingredients are {ingredients}. Here is the details: {details}. This mix contains {contains}. The custom fields are {custom_fields}. If you want to know more about the allergens, please visit {allergens}. The nutrition information is {nutrition}"
        return searchable_text

    def prepare_document(self, product: Dict) -> Dict:
        """Prepare document for MongoDB insertion with embeddings."""
        try:
            # Create searchable text by combining key fields
            searchable_text = self.generate_searchable_text(product)
            
            # Generate embedding with caching
            embedding = self.generate_embedding(searchable_text)
            
            # Prepare document
            document = {
                **product,
                'searchable_text': searchable_text,
                'embedding': embedding,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            return document
            
        except Exception as e:
            logger.error(f"Error preparing document: {e}")
            return product

    def insert_product(self, product: Dict) -> bool:
        """Insert a single product into the database with thread safety."""
        if self.collection is None:
            logger.error("No database connection available")
            return False
            
        try:
            with self._lock:
                document = self.prepare_document(product)
                self.collection.insert_one(document)
                logger.info(f"Inserted product: {product.get('name', 'Unknown')}")
                return True
            
        except DuplicateKeyError:
            logger.warning(f"Product already exists: {product.get('name', 'Unknown')}")
            return False
            
        except Exception as e:
            logger.error(f"Error inserting product: {e}")
            return False

    def insert_products(self, products: List[Dict]) -> int:
        """Insert multiple products into the database with batch processing."""
        if self.collection is None:
            logger.error("No database connection available")
            return 0
            
        inserted_count = 0
        batch_size = 50  # Process in batches for better performance
        
        try:
            with self._lock:
                for i in range(0, len(products), batch_size):
                    batch = products[i:i + batch_size]
                    prepared_docs = []
                    
                    for product in batch:
                        try:
                            doc = self.prepare_document(product)
                            prepared_docs.append(doc)
                        except Exception as e:
                            logger.error(f"Error preparing product {product.get('name', 'Unknown')}: {e}")
                    
                    if prepared_docs:
                        try:
                            result = self.collection.insert_many(prepared_docs, ordered=False)
                            inserted_count += len(result.inserted_ids)
                        except Exception as e:
                            logger.error(f"Error inserting batch: {e}")
                            # Fall back to individual inserts for this batch
                            for doc in prepared_docs:
                                try:
                                    self.collection.insert_one(doc)
                                    inserted_count += 1
                                except DuplicateKeyError:
                                    pass  # Skip duplicates
                                except Exception as insert_error:
                                    logger.error(f"Error inserting individual document: {insert_error}")
            
            logger.info(f"Inserted {inserted_count} products out of {len(products)}")
            return inserted_count
            
        except Exception as e:
            logger.error(f"Error in batch insert: {e}")
            return inserted_count

    def load_from_json(self, filename: str = "data/products_data.json") -> int:
        """Load products from JSON file and insert into database."""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                products = json.load(f)
            
            return self.insert_products(products)
            
        except FileNotFoundError:
            logger.error(f"JSON file not found: {filename}")
            return 0
        except Exception as e:
            logger.error(f"Error loading from JSON: {e}")
            return 0

    def search_products(self, query: str, limit: int = 10) -> List[Dict]:
        """Search products using text search with thread safety."""
        if self.collection is None:
            logger.error("No database connection available")
            return []
            
        try:
            with self._lock:
                results = self.collection.find(
                    {"$text": {"$search": query}},
                    {"score": {"$meta": "textScore"}}
                ).sort([("score", {"$meta": "textScore"})]).limit(limit)
                
                return list(results)
            
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            
            # If text index is missing, try to create it and retry
            if "text index required" in str(e):
                logger.info("Text index missing. Attempting to create it...")
                try:
                    self.create_indexes()
                    # Retry the search
                    with self._lock:
                        results = self.collection.find(
                        {"$text": {"$search": query}},
                        {"score": {"$meta": "textScore"}}
                    ).sort([("score", {"$meta": "textScore"})]).limit(limit)
                    return list(results)
                except Exception as retry_error:
                    logger.error(f"Retry after index creation failed: {retry_error}")
                    
            # Fallback to regex search
            try:
                logger.info("Falling back to regex search")
                regex_pattern = {"$regex": query, "$options": "i"}
                results = self.collection.find({
                    "$or": [
                        {"name": regex_pattern},
                        {"description": regex_pattern},
                        {"ingredients": regex_pattern}
                    ]
                }).limit(limit)
                
                return list(results)
                
            except Exception as fallback_error:
                logger.error(f"Fallback regex search failed: {fallback_error}")
                return []

    def semantic_search(self, query: str, limit: int = 10, threshold: float = 0.3) -> List[Dict]:
        """Perform semantic search using MongoDB vector search."""
        if self.collection is None:
            logger.error("No database connection available")
            return []
            
        try:
            # Generate embedding for the query
            query_embedding = self.generate_embedding(query)
            
            if not query_embedding:
                logger.warning("Could not generate embedding for query, falling back to text search")
                return self.search_products(query, limit)
            
            # Use MongoDB vector search
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": "vector_index",
                        "queryVector": query_embedding,
                        "path": "embedding",
                        "numCandidates": limit * 5,
                        "limit": limit
                    }
                },
                {
                    "$project": {
                        "_id": 1,
                        "name": 1,
                        "description": 1,
                        "ingredients": 1,
                        "details": 1,
                        "Contains": 1,
                        "custom_fields": 1,
                        "allergen_link": 1,
                        "review_summary": 1,
                        "images": 1,
                        "sales_info": 1,
                        "url": 1,
                        "score": {"$meta": "vectorSearchScore"}
                    }
                }
            ]
            
            results = list(self.collection.aggregate(pipeline))
            
            # Filter by threshold if specified
            filtered_results = [r for r in results if r.get('score', 0) >= threshold]
            
            logger.info(f"Semantic search found {len(filtered_results)} results for query: {query}")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            # Fallback to text search
            return self.search_products(query, limit)

    def hybrid_search(self, query: str, limit: int = 10) -> List[Dict]:
        """Combine semantic search with text search for better results using MongoDB $rankFusion."""
        if self.collection is None:
            logger.error("No database connection available")
            return []
            
        try:
            # Generate embedding for the query
            query_embedding = self.generate_embedding(query)
            
            if not query_embedding:
                logger.warning("Could not generate embedding, using text search only")
                return self.search_products(query, limit)
            
            # Use MongoDB rank fusion to combine vector and text search
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": "vector_index",
                        "queryVector": query_embedding,
                        "path": "embedding",
                        "numCandidates": limit * 5,
                        "limit": limit
                    }
                },
                {
                    "$project": {
                        "_id": 1,
                        "name": 1,
                        "price": 1,
                        "plain_text_description": 1,
                        "ingredients": 1,
                        "details": 1,
                        "Contains": 1,
                        "images": 1,
                        "custom_fields": 1,
                        "allergen_link": 1,
                        "features": 1,
                        "url": 1,
                        "score": {"$meta": "vectorSearchScore"}
                    }
                }
            ]
            
            results = list(self.collection.aggregate(pipeline))
            logger.info(f"Hybrid search found {len(results)} results for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            # Fallback to semantic search or text search
            return self.semantic_search(query, limit)

    def find_similar_products(self, product_id: str, limit: int = 5) -> List[Dict]:
        """Find products similar to a given product using vector search."""
        if self.collection is None:
            logger.error("No database connection available")
            return []
            
        try:
            # Get the reference product
            reference_product = self.get_product_by_id(product_id)
            
            if not reference_product or not reference_product.get('embedding'):
                logger.warning(f"Product {product_id} not found or has no embedding")
                return []
            
            reference_embedding = reference_product['embedding']
            
            # Use vector search to find similar products
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": "vector_index",
                        "queryVector": reference_embedding,
                        "path": "embedding",
                        "numCandidates": limit * 5,
                        "limit": limit + 1  # +1 to exclude the reference product
                    }
                },
                {
                    "$match": {
                        "_id": {"$ne": reference_product["_id"]}  # Exclude the reference product
                    }
                },
                {
                    "$project": {
                        "_id": 1,
                        "name": 1,
                        "price": 1,
                        "description": 1,
                        "ingredients": 1,
                        "instructions": 1,
                        "features": 1,
                        "url": 1,
                        "score": {"$meta": "vectorSearchScore"}
                    }
                },
                {
                    "$limit": limit
                }
            ]
            
            results = list(self.collection.aggregate(pipeline))
            logger.info(f"Found {len(results)} similar products to {product_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error finding similar products: {e}")
            return []

    def get_product_recommendations(self, user_preferences: List[str], limit: int = 5) -> List[Dict]:
        """Get product recommendations based on user preferences."""
        try:
            # Combine preferences into a single query
            query = " ".join(user_preferences)
            
            # Use hybrid search for recommendations
            recommendations = self.hybrid_search(query, limit)
            
            logger.info(f"Generated {len(recommendations)} recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return []

    def categorize_products(self, categories: List[str]) -> Dict[str, List[Dict]]:
        """Categorize products based on embedding similarity to category descriptions."""
        try:
            categorized = {category: [] for category in categories}
            
            for category in categories:
                # Use semantic search to find products for each category
                category_products = self.semantic_search(category, limit=50, threshold=0.3)
                categorized[category] = category_products
            
            return categorized
            
        except Exception as e:
            logger.error(f"Error categorizing products: {e}")
            return {}

    def update_embeddings(self) -> int:
        """Update embeddings for all products that don't have them."""
        if self.collection is None:
            logger.error("No database connection available")
            return 0
            
        try:
            # Get products without embeddings
            products_without_embeddings = list(self.collection.find({"embedding": {"$exists": False}}))
            
            if not products_without_embeddings:
                logger.info("All products already have embeddings")
                return 0
            
            updated_count = 0
            for product in products_without_embeddings:
                # Generate searchable text
                searchable_text = self.generate_searchable_text(product)
                
                # Generate embedding
                embedding = self.generate_embedding(searchable_text)
                
                if embedding:
                    # Update the product with embedding
                    result = self.collection.update_one(
                        {"_id": product["_id"]},
                        {"$set": {"embedding": embedding}}
                    )
                    if result.modified_count > 0:
                        updated_count += 1
            
            logger.info(f"Updated embeddings for {updated_count} products")
            return updated_count
            
        except Exception as e:
            logger.error(f"Error updating embeddings: {e}")
            return 0

    def get_all_products(self, limit: int = 100) -> List[Dict]:
        """Get all products from the database."""
        if self.collection is None:
            logger.error("No database connection available")
            return []
            
        try:
            return list(self.collection.find().limit(limit))
        except Exception as e:
            logger.error(f"Error getting products: {e}")
            return []

    def get_product_by_id(self, product_id: str) -> Optional[Dict]:
        """Get a specific product by ID."""
        if self.collection is None:
            logger.error("No database connection available")
            return None
            
        try:
            from bson import ObjectId
            return self.collection.find_one({"_id": ObjectId(product_id)})
        except Exception as e:
            logger.error(f"Error getting product by ID: {e}")
            return None

    def update_product(self, product_id: str, updates: Dict) -> bool:
        """Update a specific product."""
        if self.collection is None:
            logger.error("No database connection available")
            return False
            
        try:
            from bson import ObjectId
            result = self.collection.update_one(
                {"_id": ObjectId(product_id)},
                {"$set": updates}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating product: {e}")
            return False

    def delete_product(self, product_id: str) -> bool:
        """Delete a specific product."""
        if self.collection is None:
            logger.error("No database connection available")
            return False
            
        try:
            from bson import ObjectId
            result = self.collection.delete_one({"_id": ObjectId(product_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting product: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics with thread safety."""
        if self.collection is None:
            logger.error("No database connection available")
            return {"total_products": 0, "error": "No database connection"}
            
        try:
            with self._lock:
                total_products = self.collection.count_documents({})
                
                return {
                    "total_products": total_products,
                    "connection_status": "connected",
                    "database_name": settings.mongodb_db_name,
                    "collection_name": settings.mongodb_collection_name
                }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"total_products": 0, "error": str(e)}

    def close(self):
        """Close the database connection."""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")

def main():
    """Main function to test the database manager."""
    db_manager = MongoDBManager()
    
    # Load data from JSON
    inserted_count = db_manager.load_from_json("result.json")
    print(f"Inserted {inserted_count} products")
    
    # Get database stats
    stats = db_manager.get_stats()
    print(f"Database stats: {stats}")
    
    # Test search
    results = db_manager.search_products("chocolate")
    print(f"Found {len(results)} products matching 'chocolate'")
    
    # Test semantic search
    try:
        semantic_results = db_manager.semantic_search("sweet baking mix")
        print(f"Found {len(semantic_results)} products with semantic search")
    except Exception as e:
        print(f"Semantic search error: {e}")
    
    # Test hybrid search
    try:
        hybrid_results = db_manager.hybrid_search("chocolate cake")
        print(f"Found {len(hybrid_results)} products with hybrid search")
    except Exception as e:
        print(f"Hybrid search error: {e}")

if __name__ == "__main__":
    main() 