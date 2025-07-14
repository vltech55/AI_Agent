---
title: King Arthur Baking AI Assistant
emoji: 🍰
colorFrom: blue
colorTo: red
sdk: streamlit
sdk_version: "1.28.0"
app_file: app.py
pinned: false
---

# 🍰 King Arthur Baking AI Assistant

A sophisticated AI-powered assistant for King Arthur Baking mixes using RAG (Retrieval-Augmented Generation) with LangGraph, OpenAI, and MongoDB Atlas.

## 🚀 Features

- **Intelligent Web Scraping**: Automatically scrapes the King Arthur Baking mixes category
- **RAG System**: Combines semantic search with OpenAI embeddings for accurate product recommendations
- **LangGraph Agent**: Advanced AI agent with multi-step reasoning and tool use
- **MongoDB Atlas Integration**: Vector search and document storage
- **Streamlit Frontend**: Beautiful, interactive web interface
- **Real-time Analytics**: Product insights and data visualization

## 🛠️ Technology Stack

- **Frontend**: Streamlit with custom CSS styling
- **AI Framework**: LangGraph + LangChain
- **LLM**: OpenAI GPT-4o
- **Embeddings**: OpenAI text-embedding-3-small
- **Database**: MongoDB Atlas
- **Web Scraping**: BeautifulSoup4 + Requests
- **Visualization**: Plotly
- **Deployment**: Hugging Face Spaces

## 📦 Installation

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd king-arthur-baking-ai
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   Create a `.env` file in the root directory:

   ```
   OPENAI_API_KEY=your_openai_api_key_here
   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
   MONGODB_DB_NAME=king_arthur_baking_db
   MONGODB_COLLECTION_NAME=mixes
   ```

## 🔧 Configuration

The application uses several configuration parameters that can be adjusted in `config.py`:

- **API Keys**: OpenAI API key for LLM and embeddings
- **Database**: MongoDB Atlas connection string and collection names
- **Scraping**: Delay between requests and retry limits
- **Agent**: Temperature, max tokens, and model parameters

## 🕷️ Data Scraping

The scraper automatically extracts comprehensive product information:

- Product names and descriptions
- Pricing information
- Ingredients and nutritional details
- Instructions and features
- Product images and URLs
- Availability status

### Running the Scraper

```bash
python scraper.py
```

This will:

1. Scrape all mixes from the King Arthur Baking website
2. Save data to `mixes_data.json` (avoiding duplicates)
3. Display scraping statistics

## 🗄️ Database Setup

### MongoDB Atlas Configuration

1. Create a MongoDB Atlas account
2. Create a new cluster
3. Get your connection string
4. Update the `MONGODB_URI` in your `.env` file

### Loading Data

```bash
python database.py
```

This will:

1. Connect to MongoDB Atlas
2. Load data from the JSON file
3. Generate embeddings for all products
4. Create necessary indexes

## 🤖 AI Agent

The LangGraph agent features:

- **Query Analysis**: Understands user intent and extracts key information
- **Multi-Modal Search**: Combines semantic and text search
- **Product Recommendations**: Personalized suggestions based on preferences
- **Product Comparison**: Side-by-side analysis of different mixes
- **Reasoning**: Advanced analysis and insights about products

### Agent Workflow

1. **Analyze Query**: Determine intent and extract keywords
2. **Route Decision**: Choose appropriate search strategy
3. **Search/Recommend/Compare**: Execute the chosen action
4. **Reasoning**: Analyze results and provide insights
5. **Response Generation**: Create helpful, detailed responses

## 🎨 Frontend Features

The Streamlit interface includes:

- **Chat Interface**: Natural language interaction with the AI
- **Agent Graph**: Visual representation of the AI workflow
- **Product Cards**: Rich product information display
- **Analytics Dashboard**: Data insights and visualizations
- **Control Panel**: Scraping and embedding management

## 📊 Analytics

The application provides:

- **Price Distribution**: Analysis of product pricing
- **Feature Analysis**: Most common product features
- **Database Statistics**: Product counts and embedding status
- **Search Performance**: Query analysis and results

## 🚀 Deployment

### Hugging Face Spaces

1. Create a new Space on Hugging Face
2. Choose "Streamlit" as the SDK
3. Upload your code files
4. Set environment variables in the Space settings
5. The app will automatically deploy

### Local Development

```bash
streamlit run app.py
```

## 📋 Usage Examples

### Basic Product Search

```
"I'm looking for a chocolate cake mix"
```

### Recommendations

```
"Can you recommend some easy baking mixes for beginners?"
```

### Product Comparison

```
"Compare different pancake mixes"
```

### Ingredient Information

```
"What ingredients are in your bread mixes?"
```

## 🔍 API Reference

### Main Classes

#### `KingArthurScraper`

- `scrape_all_mixes()`: Scrape all products from the website
- `save_to_json()`: Save data to JSON file avoiding duplicates

#### `MongoDBManager`

- `insert_products()`: Insert products into database
- `search_products()`: Text-based search
- `semantic_search()`: Embedding-based search

#### `EmbeddingService`

- `generate_embedding()`: Create embeddings for text
- `semantic_search()`: Find similar products
- `hybrid_search()`: Combine semantic and text search

#### `KingArthurBakingAgent`

- `chat()`: Main chat interface
- `get_graph_visualization()`: Get agent workflow graph

## 🛡️ Error Handling

The application includes comprehensive error handling:

- **Connection Errors**: Automatic retry with exponential backoff
- **API Rate Limits**: Proper delays and batch processing
- **Data Validation**: Input sanitization and type checking
- **Graceful Degradation**: Fallback options when services are unavailable

## 📈 Performance Optimization

- **Batch Processing**: Embeddings generated in batches
- **Caching**: Frequent queries cached for faster response
- **Indexing**: MongoDB indexes for efficient search
- **Rate Limiting**: Respectful scraping with delays

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- King Arthur Baking for their excellent products and website
- OpenAI for the powerful GPT-4o and embedding models
- MongoDB Atlas for the vector database capabilities
- Streamlit for the beautiful web interface framework
- LangGraph for the advanced agent workflow capabilities

## 🐛 Troubleshooting

### Common Issues

1. **Connection Errors**: Check your internet connection and API keys
2. **Rate Limiting**: Reduce scraping frequency or batch sizes
3. **Memory Issues**: Limit the number of products processed at once
4. **Authentication**: Verify your MongoDB Atlas and OpenAI credentials

### Support

For issues and questions:

1. Check the logs for detailed error messages
2. Verify all environment variables are set correctly
3. Ensure all dependencies are installed
4. Check the MongoDB Atlas connection and permissions

## 📝 Changelog

### Version 1.0.0

- Initial release
- Web scraping functionality
- MongoDB Atlas integration
- OpenAI embeddings and chat
- LangGraph agent workflow
- Streamlit frontend
- Hugging Face Spaces deployment ready
