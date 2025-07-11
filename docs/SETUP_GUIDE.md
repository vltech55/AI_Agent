# 🚀 Setup Guide for King Arthur Baking AI Assistant

## ✅ Fixed Pydantic Import Issue

The Pydantic import issue has been resolved! The `BaseSettings` import has been updated to use `pydantic-settings` package.

## 🔧 Environment Setup

### 1. Create Environment File

Create a `.env` file in the project root with your API keys:

```bash
# OpenAI API Configuration
# Get your API key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=your_openai_api_key_here

# MongoDB Atlas Configuration
# Get your connection string from: https://cloud.mongodb.com/
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_DB_NAME=king_arthur_baking_db
MONGODB_COLLECTION_NAME=mixes

# Optional Configuration
SCRAPING_DELAY=1
MAX_RETRIES=3
TEMPERATURE=0.1
MAX_TOKENS=1000
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

### 2. Install Dependencies

Make sure you have the latest dependencies:

```bash
pip install pydantic-settings
```

All dependencies are listed in `requirements.txt`.

### 3. Quick Start

#### Test the Setup

```bash
python demo.py
```

#### Run Full Setup (with API keys)

```bash
python main.py --setup
```

#### Launch Streamlit App

```bash
streamlit run app.py
```

## 🛠️ Without API Keys (Demo Mode)

You can run the demo without API keys:

```bash
python demo.py
```

This will show you how the AI assistant works with sample data.

## 🔍 Troubleshooting

### Common Issues

1. **Import Error**: Make sure `pydantic-settings` is installed
2. **API Key Missing**: The app will run but won't connect to OpenAI/MongoDB
3. **Environment Variables**: Create a `.env` file with your credentials

### Test Your Setup

```bash
# Test if imports work
python -c "from config import settings; print('✅ Config OK')"

# Test all components
python test_setup.py
```

## 🎯 Next Steps

1. **Get API Keys**:
   - OpenAI: <https://platform.openai.com/api-keys>
   - MongoDB Atlas: <https://cloud.mongodb.com/>

2. **Set Up Environment**: Create `.env` file with your keys

3. **Run Full Setup**: `python main.py --setup`

4. **Launch App**: `streamlit run app.py`

## 🚀 Deployment

For Hugging Face Spaces:

1. Upload all files to your Space
2. Set environment variables in Space settings
3. The app will automatically deploy!

**The app is now ready to run! 🍰**
