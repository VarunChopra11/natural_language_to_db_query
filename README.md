# Crypto Monitoring & Analytics Platform

A comprehensive financial monitoring platform that provides crypto portfolio analytics, transaction tracking, and natural language query capabilities for blockchain data. Built with FastAPI and powered by Claude AI for intelligent data querying.

## 🚀 Features

### Core Functionality
- **Portfolio Tracking**: Real-time crypto portfolio monitoring with USD valuations
- **Transaction History**: Complete blockchain transaction analysis and categorization
- **NFT Asset Management**: Track and value NFT collections across networks
- **DeFi Position Monitoring**: Monitor lending, borrowing, and staking positions
- **Natural Language Queries**: Ask questions about your data in plain English using Claude AI

### API Management
- **Multi-tenant Architecture**: Support for multiple client organizations
- **API Key Management**: Secure API key generation and management (up to 5 keys per client)
- **End User Management**: Manage wallet addresses and associated data per client
- **Analytics Dashboard**: Comprehensive analytics for client portfolios

### Security & Authentication
- **Email Verification**: Secure signup with email verification
- **JWT Authentication**: Secure session management
- **API Key Authentication**: Programmatic access with Bearer token support
- **Multi-level Authorization**: Client and end-user level access controls

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL with AsyncPG
- **AI/ML**: Anthropic Claude (via Vertex AI)
- **Blockchain Data**: Zapper API integration
- **Authentication**: JWT with email verification
- **Email**: SMTP with Gmail integration
- **Deployment**: Cloud-ready with GCP support

## 📋 Prerequisites

- Python 3.8+
- PostgreSQL database
- GCP Account (for Claude AI integration)
- Gmail account (for email verification)
- Zapper API key

## 🔧 Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd crypto-monitoring-platform
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp .env.sample .env
```

Fill in your `.env` file with the required credentials:

```env
# Authentication
JWT_SECRET_KEY=your_jwt_secret_key
GMAIL_ADDRESS=your_gmail@gmail.com
GMAIL_APP_PASSWORD=your_gmail_app_password
FRONTEND_URL=https://your-frontend-domain.com

# Database
GCP_DATABASE_URL=postgresql+asyncpg://user:password@host/database

# Claude AI (GCP Vertex AI)
GCP_PROJECT_ID=your-gcp-project-id
GCP_LOCATION=us-east5
CLAUDE_MODEL_NAME=claude-3-5-haiku@20241022
SA_INFO=base64_encoded_service_account_json

# Analytics
ZAPPER_API_KEY=your_zapper_api_key
```

4. **Run the application**
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## 🏗️ Database Schema

The platform uses a multi-tenant PostgreSQL schema with the following key tables:

- **client_users**: Organization accounts and verification status
- **api_keys**: API key management and authentication
- **end_users**: Wallet addresses managed by each client
- **financial_portfolios**: Portfolio summaries and total balances
- **token_balances**: Individual token holdings and valuations
- **app_balances**: DeFi positions (lending, borrowing, staking)
- **nft_assets**: NFT collections and estimated values
- **transaction_history**: Complete transaction records with AI-powered descriptions

## 🔑 API Endpoints

### Authentication
- `POST /auth/signup` - Register new client organization
- `POST /auth/login` - Request login verification email
- `GET /auth/verify-email` - Verify email and complete authentication
- `GET /auth/get-current-client` - Get current authenticated client
- `POST /auth/logout` - Logout and clear session

### API Key Management
- `POST /apikey/create_apikey` - Generate new API key
- `GET /apikey/fetch_apikeys` - List all API keys (masked)
- `DELETE /apikey/delete_apikey` - Delete specific API key

### End User Management
- `POST /enduser/apikey/create_enduser` - Add new wallet address
- `GET /enduser/apikey/list_endusers` - List managed wallets
- `GET /enduser/apikey/get_enduser/{wallet_address}` - Get specific wallet
- `DELETE /enduser/apikey/delete_enduser/{wallet_address}` - Remove wallet

### Analytics
- `GET /analytics/portfolio-summary` - Portfolio overview across all users
- `GET /analytics/token-distribution` - Token holdings breakdown
- `GET /analytics/app-summary` - DeFi positions summary
- `GET /analytics/nft-summary` - NFT collections overview
- `GET /analytics/transaction-activity` - Transaction volume metrics

### Natural Language Queries
- `GET /query/create_query` - Convert natural language to SQL and execute

## 🤖 AI-Powered Querying

The platform integrates Claude AI to convert natural language questions into SQL queries:

```bash
# Example queries you can ask:
"Show me all transactions over $1000 in the last week"
"Which tokens have the highest balance across all users?"
"How many NFTs does each user own?"
"What's the total portfolio value by network?"
```

## 🔐 Authentication Methods

### 1. Cookie-based (Web Interface)
```javascript
// Automatic cookie handling for web applications
fetch('/analytics/portfolio-summary', {
  credentials: 'include'
})
```

### 2. API Key (Programmatic Access)
```bash
# Using Authorization header
curl -H "Authorization: Bearer hq_your_api_key_here" \
     https://api.example.com/enduser/apikey/list_endusers

# Using X-API-Key header
curl -H "X-API-Key: hq_your_api_key_here" \
     https://api.example.com/enduser/apikey/list_endusers
```

## 📊 Data Sources

- **Zapper API**: Portfolio data, token balances, DeFi positions, NFTs, and transaction history
- **Real-time Pricing**: Token prices and USD valuations
- **Multi-chain Support**: Ethereum, Base, and other EVM networks

## 🚀 Deployment

The application is designed for cloud deployment with:

- **Database**: PostgreSQL (supports GCP Cloud SQL)
- **AI Service**: GCP Vertex AI for Claude integration
- **Email**: Gmail SMTP for verification emails
- **CORS**: Configured for web application integration

## 🔧 Development

### Project Structure
```
app/
├── routers/          # API route handlers
├── services/         # Business logic and external integrations
├── schemas/          # Pydantic models for request/response
├── db/              # Database connection and table creation
└── config.py        # Configuration management
```

### Key Services
- **ZapperService**: Blockchain data integration
- **FinancialProfileService**: Portfolio data processing
- **ApiKeyService**: Secure API key management
- **GenerateQuery**: AI-powered SQL generation


## 🤝 Contributing

1. **Request access** to the repository if you’re not already a collaborator.
2. Fork the repository **(if permitted)** or create a feature branch directly:  
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. Commit your changes:  
   ```bash
   git commit -m 'Add amazing feature'
   ```
4. Push to the branch:  
   ```bash
   git push origin feature/amazing-feature
   ```
5. Open a Pull Request for review.

> ✅ **Note:** Please follow the contribution guidelines and respect any code review or security policies defined for this private project.

---

## 📝 License

This project is licensed under the **MIT License** — see the `LICENSE` file for details.

---

## 🆘 Support

For support and questions:

- Open an **Issue** in this private repository.
- Contact a repository **maintainer** directly if the issue contains sensitive information.
- Check the API documentation at `/docs` (FastAPI auto-generated).
- Review the database schema in `app/db/db.py`.

---
