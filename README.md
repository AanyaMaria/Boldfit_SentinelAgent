# BoldFit SentinelAgent

An AI-powered inventory monitoring agent that tracks product stock levels in the warehouse and predicts when restocking is needed.

## Features
- Real-time stock level monitoring across warehouse inventory
- Predictive alerts when stock is about to run out
- Automated restocking notifications to suppliers
- Historical consumption analysis for better demand forecasting

## How It Works
1. Monitors current stock levels in the godown
2. Analyzes consumption patterns using ML models
3. Predicts when a product will run out
4. Sends restocking alerts before stock hits zero

## Getting Started
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure warehouse settings in `config.yaml`
4. Run the agent: `python main.py`

## Tech Stack
- Python
- scikit-learn 
- FastAPI
- PostgreSQL
