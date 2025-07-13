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

        # query_embedding = self.generate_embedding("Ingredients: Flour, Sugar, Baking Powder, Baking Soda, Salt, Vanilla Extract, Egg, Milk, Butter, Chocolate Chips")
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
            # self.collection.create_index([
            #     ("name", "text"),
            #     ("description", "text"),
            #     ("instructions", "text"),
            #     ("ingredients", "text")
            # ])
            
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
            return []

    def semantic_search(self, query: str, limit: int = 5) -> List[Dict]:
        """Perform semantic search using embeddings."""
        try:
            # Generate embedding for the query
            query_embedding = self.generate_embedding(query)
            
            if not query_embedding:
                logger.warning("Could not generate embedding for query")
                return self.search_products(query, limit)
            
            # For now, we'll use a simple approach - calculate similarity in application
            # In a production environment, you'd use MongoDB's vector search capabilities
            all_products = list(self.collection.find({"embedding": {"$exists": True}}))
            
            # Calculate cosine similarity
            from numpy import dot
            from numpy.linalg import norm
            
            def cosine_similarity(a, b):
                if not a or not b:
                    return 0
                return dot(a, b) / (norm(a) * norm(b))
            
            # Calculate similarities
            similarities = []
            for product in all_products:
                if product.get('embedding'):
                    similarity = cosine_similarity(query_embedding, product['embedding'])
                    similarities.append((similarity, product))
            
            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x[0], reverse=True)
            return [product for _, product in similarities[:limit]]
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return self.search_products(query, limit)

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
    """Main function to test database operations."""
    db_manager = MongoDBManager()
    
    # Load data from JSON
    # inserted_count = db_manager.load_from_json()
    # print(f"Inserted {inserted_count} products")
    
    # Get stats
    stats = db_manager.get_stats()
    print(f"Database stats: {stats}")
    
    # Test search
    results = db_manager.search_products("chocolate")
    print(f"Found {len(results)} products matching 'chocolate'")
    
    # Test semantic search
    results = db_manager.semantic_search("sweet baking mix")
    print(f"Found {len(results)} products with semantic search")

if __name__ == "__main__":
    main() 