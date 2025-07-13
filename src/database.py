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

from .config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoDBManager:
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self.collection: Optional[Collection] = None
        self.connect()

        query_embedding = self.generate_embedding("Ingredients: Flour, Sugar, Baking Powder, Baking Soda, Salt, Vanilla Extract, Egg, Milk, Butter, Chocolate Chips")
        # pipeline = [
        #     {
        #             "$vectorSearch": {
        #                 "index": "vector_index",
        #                 "queryVector": query_embedding,
        #                 "path": "embedding",
        #                 "exact": True,
        #                 "limit": 5
        #             }
        #     }, {
        #             "$project": {
        #             "_id": 0,
        #             "name": 1,
        #             "price": 1,
        #             "ingredients": 1,
        #         }
        #     }
        # ]
        # pipeline = [
        #     {
        #             "$search": {
        #                 "index": "text_index",
        #                 "text": {
        #                     "query": "Ingredients: Flour, Sugar, Baking Powder, Baking Soda, Salt, Vanilla Extract, Egg, Milk, Butter, Chocolate Chips",
        #                     "path": "searchable_text"
        #                 },
        #             },
        #     }, {
        #         "$limit": 20
        #     }, {
        #             "$project": {
        #             "_id": 0,
        #             "name": 1,
        #             "price": 1,
        #             "ingredients": 1,
        #         }
        #     }
        # ]
        # pipeline = [
        #     {
        #         "$rankFusion": {
        #             "input": {
        #                 "pipelines": {
        #                     "vectorPipeline": [
        #                         {
        #                             "$vectorSearch": {
        #                                 "index": "vector_index",
        #                                 "path": "embedding",
        #                                 "queryVector": query_embedding,
        #                                 "numCandidates": 100,
        #                                 "limit": 20
        #                             }
        #                         }
        #                     ],
        #                     "fullTextPipeline": [
        #                         {
        #                             "$search": {
        #                                 "index": "text-index",
        #                                 "phrase": {
        #                                     "query": "Ingredients: Flour, Sugar, Baking Powder, Baking Soda, Salt, Vanilla Extract, Egg, Milk, Butter, Chocolate Chips",
        #                                     "path": "searchable_text"
        #                                 },
        #                                 "limit": 20
        #                             }
        #                         }
        #                     ]
        #                 }
        #             },
        #             "combination": {
        #                 "weights": {
        #                     "vectorPipeline": 0.7,
        #                     "fullTextPipeline": 0.3
        #                 }
        #             },
        #             "scoreDetails": True
        #         }
        #     },
        #     {
        #         "$project": {
        #             "_id": 1,
        #             "name": 1,
        #             "price": 1,
        #             "ingredients": 1,
        #         }
        #     },
        #     {
        #         "$limit": 20
        #     }
        # ]
        # results = self.collection.aggregate(pipeline)
        # array_of_results = []
        # for doc in results:
        #     array_of_results.append(doc)
        # print(array_of_results)

    def connect(self):
        """Connect to MongoDB Atlas."""
        try:
            self.client = MongoClient(settings.mongodb_uri)
            self.db = self.client[settings.mongodb_db_name]
            self.collection = self.db[settings.mongodb_collection_name]
            
            # Test connection
            self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB Atlas")
            
            # Create indexes
            # self.create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def create_indexes(self):
        """Create necessary indexes for the collection."""
        try:
            # Create unique index on URL to prevent duplicates
            # self.collection.create_index("url", unique=True)
            search_idx = SearchIndexModel(
                definition ={
                    "mappings": {
                        "dynamic": True
                    }
                },
                name="text_index",
            )
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
            self.collection.create_search_indexes(models=indexes)

            logger.info("Indexes created successfully")
            
            # Create text index for search
            # try:
            #     existing_indexes = list(self.collection.list_indexes())
            #     index_names = [idx['name'] for idx in existing_indexes]
                
            #     if "text_search_index" not in index_names:
            #         self.collection.create_index([
            #             ("name", "text"),
            #             ("description", "text"),
            #             ("instructions", "text"),
            #             ("ingredients", "text")
            #         ], name="text_search_index")
            #         logger.info("Created text search index")
            #     else:
            #         logger.info("Text search index already exists")
            # except Exception as text_idx_error:
            #     logger.warning(f"Could not create text index: {text_idx_error}")
            
            # Create index for embeddings if vector search is supported
            # Note: This might need to be configured in MongoDB Atlas UI for vector search
            
        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI."""
        try:
            client = openai.OpenAI(api_key=settings.openai_api_key)
            response = client.embeddings.create(
                model=settings.embedding_model,
                input=text
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

        searchable_text = f"This is a mix named {name}. {description}. The ingredients are {ingredients}. Here is the details: {details}. This mix contains {contains}. The custom fields are {custom_fields}. If you want to know more about the allergens, please visit {allergens}."
        return searchable_text

    def prepare_document(self, product: Dict) -> Dict:
        """Prepare document for MongoDB insertion with embeddings."""
        try:
            # Create searchable text by combining key fields
            searchable_text = self.generate_searchable_text(product)
            
            # Generate embedding
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
        """Insert a single product into the database."""
        try:
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
        """Insert multiple products into the database."""
        inserted_count = 0
        
        for product in products:
            if self.insert_product(product):
                inserted_count += 1
        
        logger.info(f"Inserted {inserted_count} products out of {len(products)}")
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
        """Search products using text search."""
        try:
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

    def semantic_search(self, query: str, limit: int = 5, threshold: float = 0.3) -> List[Dict]:
        """Perform semantic search using MongoDB vector search."""
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
                        "price": 1,
                        "description": 1,
                        "ingredients": 1,
                        "instructions": 1,
                        "features": 1,
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

    def hybrid_search(self, query: str, limit: int = 5) -> List[Dict]:
        """Combine semantic search with text search for better results using MongoDB $rankFusion."""
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
                        "description": 1,
                        "ingredients": 1,
                        "instructions": 1,
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
        try:
            return list(self.collection.find().limit(limit))
        except Exception as e:
            logger.error(f"Error getting products: {e}")
            return []

    def get_product_by_id(self, product_id: str) -> Optional[Dict]:
        """Get a specific product by ID."""
        try:
            from bson import ObjectId
            return self.collection.find_one({"_id": ObjectId(product_id)})
        except Exception as e:
            logger.error(f"Error getting product by ID: {e}")
            return None

    def update_product(self, product_id: str, updates: Dict) -> bool:
        """Update a product in the database."""
        try:
            from bson import ObjectId
            updates['updated_at'] = datetime.utcnow()
            result = self.collection.update_one(
                {"_id": ObjectId(product_id)},
                {"$set": updates}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating product: {e}")
            return False

    def delete_product(self, product_id: str) -> bool:
        """Delete a product from the database."""
        try:
            from bson import ObjectId
            result = self.collection.delete_one({"_id": ObjectId(product_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting product: {e}")
            return False

    def get_stats(self) -> Dict:
        """Get database statistics."""
        try:
            total_products = self.collection.count_documents({})
            products_with_embeddings = self.collection.count_documents({"embedding": {"$exists": True}})
            
            return {
                "total_products": total_products,
                "products_with_embeddings": products_with_embeddings,
                "collection_name": settings.mongodb_collection_name,
                "database_name": settings.mongodb_db_name
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}

    def close(self):
        """Close the database connection."""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")

def main():
    """Main function to test the database manager."""
    db_manager = MongoDBManager()
    
    # Load data from JSON
    inserted_count = db_manager.load_from_json()
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