# 🧠 Natural Language to DB Query

A tool that converts natural language questions about Ethereum blockchain data into SQL queries, executes them against a PostgreSQL database, and provides the results via a RESTful API.

---

## 🚀 Overview

This project allows you to:

- Convert natural language questions to optimized PostgreSQL queries using **Google's Gemini AI**
- Query a database containing **Ethereum blockchain data** (blocks, transactions, withdrawals, etc.)
- Get results via a **RESTful API**
- Import and process blockchain data from **JSON files**

---

## ⚙️ Project Setup

### ✅ Prerequisites

- Python 3.8+
- PostgreSQL or CockroachDB (PostgreSQL compatible)
- Google Gemini API Key

### 📦 Installation

Clone this repository:

```bash
git clone <repository-url>
cd natural_language_to_db_query
```

Create and activate a virtual environment:

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Set up environment variables:

```bash
# Copy the sample environment file
cp .env.sample .env

# Edit .env with your DB credentials and Gemini API key
```

Set up the database:

```bash
# Connect to your PostgreSQL server and run the schema
psql -U yourusername -d yourdbname -f schema.sql
```

---

## 📁 File Structure

### 🔹 Core Files

- `main.py` – FastAPI application entry point  
- `schema.sql` – SQL schema for creating blockchain tables and indexes  
- `insert_data.py` – Script to load Ethereum data from JSON to DB  
- `sample_data.json` – Sample Ethereum blockchain data  

### 🔹 App Directory

- `config.py` – Loads settings from environment variables  
- `llm.py` – Handles natural language processing with Gemini  
- `query.py` – Manages DB connection and query execution  
- `query_routers.py` – API endpoints for query execution  

### 🔹 Configuration

- `.env.sample` – Template for environment variables  
- `.gitignore` – Specifies ignored files  

---

## ▶️ Usage

Run the application:

```bash
uvicorn main:app --reload
```

This will start the FastAPI server at [http://localhost:8000](http://localhost:8000), which provides the following endpoints:

- `/query/create_query?natural_language=your_query&page_index=1&rows_per_page=100`  
  Convert natural language to SQL, execute it, and return results

You can also use the automatic API documentation:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)  
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 📥 Importing Data

To load Ethereum blockchain data into your database:

1. Ensure your JSON file matches the format in `sample_data.json`  
2. Update the `JSON_FILE_PATH` in your `.env` file  
3. Run the import script:

```bash
python insert_data.py
```

---

## 🗃️ Database Schema

### `blocks`

- **Primary Key**: `number`  
- **Fields**: `hash`, `parent_hash`, `timestamp`, `gas_limit`, `gas_used`, etc.

### `transactions`

- **Primary Key**: `hash`  
- **Foreign Key**: `block_number → blocks(number)`  
- **Fields**: `from_address`, `to_address`, `value`, `gas_price`, etc.

### `withdrawals`

- **Primary Keys**: `block_number`, `index`  
- **Fields**: `validator_index`, `address`, `amount`

### `access_list`

- **Primary Keys**: `transaction_hash`, `address`  
- **Fields**: `storage_keys`

---

## 🔐 Environment Variables

Your `.env` file should include:

```env
JSON_FILE_PATH="/path/to/your/blockchain/data.json"

POSTGRESDB_HOST="your-database-host"
POSTGRESDB_PORT=your-database-port
POSTGRESDB_USER="your-username"
POSTGRESDB_PASSWORD="your-password"
POSTGRESDB_NAME="your-database-name"

GEMINI_API_KEY="your-gemini-api-key"
```

---

## 🔌 API Endpoints

### Query Creation Endpoint

**GET** `/query/create_query`

**Parameters:**

- `natural_language` (string, required): The natural language query to convert to SQL  
- `page_index` (integer, optional, default=1): Page number for pagination  
- `rows_per_page` (integer, optional, default=100): Number of rows per page

**Response:**

```json
{
  "query": "Generated SQL query",
  "count_query": "SQL query to count total rows",
  "explanation": "Explanation of the query",
  "columns": ["column1", "column2", ...],
  "data": [
    {"column1": "value1", "column2": "value2", ...},
    ...
  ],
  "total_rows": 1000,
  "has_next_page": true
}
```

---

## 💬 Example Queries

Here are some example queries you can make to the API:

- `/query/create_query?natural_language=Show the last 5 transactions with value over 1 ETH`  
- `/query/create_query?natural_language=What was the average gas price in the last 100 blocks?`  
- `/query/create_query?natural_language=Find the top 10 miners by number of blocks mined`  
- `/query/create_query?natural_language=Show all withdrawals to address 0xb9d7934878b5fb9610b3fe8a5e441e8fad7e293f`

---

## 📄 License

MIT License. See `LICENSE` file for more details.

---

## 🙌 Acknowledgements

- **Google Gemini** for powerful LLM integration  
- **FastAPI** for high-performance API development  
- **Ethereum** for open blockchain data
