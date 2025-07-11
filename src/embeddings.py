import openai
import numpy as np
from typing import List, Dict, Optional, Tuple
import logging
from .database import MongoDBManager
from .config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.db_manager = MongoDBManager()
        
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a given text."""
        try:
            response = self.client.embeddings.create(
                model=settings.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return []
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        embeddings = []
        batch_size = 100  # OpenAI's recommended batch size
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            try:
                response = self.client.embeddings.create(
                    model=settings.embedding_model,
                    input=batch
                )
                batch_embeddings = [data.embedding for data in response.data]
                embeddings.extend(batch_embeddings)
                logger.info(f"Generated embeddings for batch {i//batch_size + 1}/{len(texts)//batch_size + 1}")
            except Exception as e:
                logger.error(f"Error generating embeddings for batch: {e}")
                # Add empty embeddings for failed batch
                embeddings.extend([[] for _ in batch])
        
        return embeddings
    
    def cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if not a or not b:
            return 0.0
        
        a_np = np.array(a)
        b_np = np.array(b)
        
        # Calculate cosine similarity
        dot_product = np.dot(a_np, b_np)
        norm_a = np.linalg.norm(a_np)
        norm_b = np.linalg.norm(b_np)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)
    
    def semantic_search(self, query: str, limit: int = 5, threshold: float = 0.3) -> List[Dict]:
        """Perform semantic search using embeddings."""
        try:
            # Generate embedding for the query
            query_embedding = self.generate_embedding(query)
            
            if not query_embedding:
                logger.warning("Could not generate embedding for query")
                return []
            
            # Get all products with embeddings
            products = self.db_manager.get_all_products()
            products_with_embeddings = [p for p in products if p.get('embedding')]
            
            if not products_with_embeddings:
                logger.warning("No products with embeddings found")
                return []
            
            # Calculate similarities
            similarities = []
            for product in products_with_embeddings:
                similarity = self.cosine_similarity(query_embedding, product['embedding'])
                if similarity >= threshold:
                    similarities.append((similarity, product))
            
            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x[0], reverse=True)
            results = [product for _, product in similarities[:limit]]
            
            logger.info(f"Semantic search found {len(results)} results for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def hybrid_search(self, query: str, limit: int = 5) -> List[Dict]:
        """Combine semantic search with text search for better results."""
        try:
            # Get semantic search results
            semantic_results = self.semantic_search(query, limit * 2)
            
            # Get text search results
            text_results = self.db_manager.search_products(query, limit * 2)
            
            # Combine and deduplicate results
            combined_results = {}
            
            # Add semantic search results with higher weight
            for i, product in enumerate(semantic_results):
                product_id = str(product.get('_id'))
                score = 1.0 - (i / len(semantic_results)) * 0.5  # Higher score for semantic
                combined_results[product_id] = {
                    'product': product,
                    'score': score
                }
            
            # Add text search results with lower weight
            for i, product in enumerate(text_results):
                product_id = str(product.get('_id'))
                score = 0.5 - (i / len(text_results)) * 0.3  # Lower score for text
                
                if product_id in combined_results:
                    # Combine scores if already present
                    combined_results[product_id]['score'] += score
                else:
                    combined_results[product_id] = {
                        'product': product,
                        'score': score
                    }
            
            # Sort by combined score and return top results
            sorted_results = sorted(
                combined_results.values(),
                key=lambda x: x['score'],
                reverse=True
            )
            
            return [result['product'] for result in sorted_results[:limit]]
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            return self.semantic_search(query, limit)
    
    def find_similar_products(self, product_id: str, limit: int = 5) -> List[Dict]:
        """Find products similar to a given product."""
        try:
            # Get the reference product
            reference_product = self.db_manager.get_product_by_id(product_id)
            
            if not reference_product or not reference_product.get('embedding'):
                logger.warning(f"Product {product_id} not found or has no embedding")
                return []
            
            reference_embedding = reference_product['embedding']
            
            # Get all other products
            all_products = self.db_manager.get_all_products()
            other_products = [p for p in all_products if str(p.get('_id')) != product_id and p.get('embedding')]
            
            # Calculate similarities
            similarities = []
            for product in other_products:
                similarity = self.cosine_similarity(reference_embedding, product['embedding'])
                similarities.append((similarity, product))
            
            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x[0], reverse=True)
            return [product for _, product in similarities[:limit]]
            
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
            # Generate embeddings for categories
            category_embeddings = {}
            for category in categories:
                embedding = self.generate_embedding(category)
                if embedding:
                    category_embeddings[category] = embedding
            
            # Get all products
            products = self.db_manager.get_all_products()
            products_with_embeddings = [p for p in products if p.get('embedding')]
            
            # Categorize products
            categorized = {category: [] for category in categories}
            
            for product in products_with_embeddings:
                best_category = None
                best_similarity = 0
                
                for category, category_embedding in category_embeddings.items():
                    similarity = self.cosine_similarity(product['embedding'], category_embedding)
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_category = category
                
                if best_category and best_similarity > 0.3:  # Threshold for categorization
                    categorized[best_category].append(product)
            
            return categorized
            
        except Exception as e:
            logger.error(f"Error categorizing products: {e}")
            return {}
    
    def update_embeddings(self) -> int:
        """Update embeddings for all products that don't have them."""
        try:
            # Get products without embeddings
            all_products = self.db_manager.get_all_products()
            products_without_embeddings = [p for p in all_products if not p.get('embedding')]
            
            if not products_without_embeddings:
                logger.info("All products already have embeddings")
                return 0
            
            # Generate embeddings
            texts = []
            for product in products_without_embeddings:
                searchable_text = f"{product.get('name', '')} {product.get('description', '')} {product.get('instructions', '')} {product.get('ingredients', '')}"
                texts.append(searchable_text)
            
            embeddings = self.generate_embeddings_batch(texts)
            
            # Update database
            updated_count = 0
            for product, embedding in zip(products_without_embeddings, embeddings):
                if embedding:
                    success = self.db_manager.update_product(
                        str(product['_id']),
                        {'embedding': embedding}
                    )
                    if success:
                        updated_count += 1
            
            logger.info(f"Updated embeddings for {updated_count} products")
            return updated_count
            
        except Exception as e:
            logger.error(f"Error updating embeddings: {e}")
            return 0

def main():
    """Main function to test embedding service."""
    embedding_service = EmbeddingService()
    
    # Update embeddings
    updated_count = embedding_service.update_embeddings()
    print(f"Updated embeddings for {updated_count} products")
    
    # Test semantic search
    results = embedding_service.semantic_search("chocolate cake mix")
    print(f"Semantic search results: {len(results)}")
    
    # Test hybrid search
    results = embedding_service.hybrid_search("sweet baking mix")
    print(f"Hybrid search results: {len(results)}")
    
    # Test recommendations
    preferences = ["chocolate", "sweet", "easy to make"]
    recommendations = embedding_service.get_product_recommendations(preferences)
    print(f"Recommendations: {len(recommendations)}")

if __name__ == "__main__":
    main() 