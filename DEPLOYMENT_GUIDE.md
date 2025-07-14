# 🚀 Deployment Guide - Hugging Face Spaces

## SSL/TLS Connection Issues with MongoDB Atlas

If you encounter SSL handshake errors like `tlsv1 alert internal error`, try these solutions:

### 🔧 Solution 1: Update MongoDB URI with SSL Parameters

Add these parameters to your MongoDB URI in Hugging Face Spaces environment variables:

```
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/database?retryWrites=true&w=majority&ssl=true&authSource=admin&tlsAllowInvalidCertificates=true&tlsAllowInvalidHostnames=true
```

### 🔧 Solution 2: Alternative URI Format

If the above doesn't work, try this format:

```
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/database?ssl=true&ssl_cert_reqs=CERT_NONE&ssl_match_hostname=false
```

### 🔧 Solution 3: Environment Variables for SSL

Set these additional environment variables in Hugging Face Spaces:

```
SSL_CERT_REQS=CERT_NONE
SSL_MATCH_HOSTNAME=false
PYTHONHTTPSVERIFY=0
```

### 🔧 Solution 4: MongoDB Atlas Network Access

1. Go to MongoDB Atlas Dashboard
2. Navigate to "Network Access"
3. Add `0.0.0.0/0` to allow access from anywhere (for testing)
4. Or add Hugging Face Spaces IP ranges if available

### 🔧 Solution 5: Update Dependencies

Make sure you have the latest dependencies with SSL support:

```bash
pip install --upgrade pymongo[srv]==4.10.1 dnspython>=2.4.0 certifi>=2023.7.22
```

### 📋 Required Environment Variables for Hugging Face Spaces

Set these in your Hugging Face Space settings:

```
OPENAI_API_KEY=your_openai_api_key_here
MONGODB_URI=your_mongodb_connection_string_with_ssl_params
MONGODB_DB_NAME=king_arthur_baking_db
MONGODB_COLLECTION_NAME=mixes
```

### 🔍 Debugging Steps

1. **Check MongoDB Atlas Status**: Ensure your cluster is running
2. **Verify Credentials**: Test connection string locally first
3. **Network Access**: Ensure Hugging Face IPs are whitelisted
4. **SSL Certificates**: Try with SSL verification disabled (for testing only)
5. **Connection Timeout**: Increase timeout values if needed

### ⚠️ Security Note

Disabling SSL verification (`tlsAllowInvalidCertificates=true`) should only be used as a temporary workaround. For production, ensure proper SSL configuration.

### 🆘 If All Else Fails

Consider using MongoDB Atlas Data API instead of direct connection:

- More compatible with serverless environments
- No SSL handshake issues
- REST API based access

Would you like help setting up the Data API approach?
