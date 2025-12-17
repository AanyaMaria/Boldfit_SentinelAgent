import pandas as pd
import os
import requests # New library for web requests
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate

# --- CONFIGURATION ---
# PASTE YOUR GROQ KEY HERE INSIDE THE QUOTES
os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"] 

# --- STEP 1: MOCK DATA ---
def load_mock_database():
    data = {
        "product_id": ["BF-YOGA-01", "BF-WHEY-CHOC", "BF-RES-BANDS"],
        "product_name": ["Pro Yoga Mat", "Whey Protein (Chocolate)", "Resistance Bands Set"],
        "current_stock": [15, 500, 45], 
        "daily_burn_rate": [3, 10, 2],    
        "lead_time_days": [7, 14, 5],     
        "supplier_email": ["supply@yogamats.com", "labs@whey.com", "rubber@bands.com"],
        "current_price": [15.00, 49.99, 25.00] # Added price data
    }
    return pd.DataFrame(data)

df = load_mock_database()

# --- STEP 2: DEFINE TOOLS (The Agent's "Hands") ---

@tool
def analyze_inventory_risk(threshold_days: int = 10) -> str:
    """
    Analyzes current inventory. Returns a list of products that will run out 
    of stock within the specified threshold days.
    """
    print(f"\n[SYSTEM] Analyzing inventory risk for next {threshold_days} days...")
    
    # Logic: Days Remaining = Current Stock / Daily Burn Rate
    df['days_remaining'] = df['current_stock'] / df['daily_burn_rate']
    
    urgent_items = df[df['days_remaining'] <= threshold_days]
    
    if urgent_items.empty:
        return "All stock levels are healthy."
    
    # Include current price in the JSON output for the next tool to use
    return urgent_items[['product_name', 'current_stock', 'daily_burn_rate', 'days_remaining', 'current_price']].to_json(orient="records")

@tool
def check_competitor_pricing(product_name: str) -> str:
    """
    Mocks checking the market price for a product from a competitor API.
    Used to inform reordering and pricing decisions.
    """
    print(f"\n[SYSTEM] Checking competitor price for {product_name}...")
    
    # --- MOCK LOGIC for DEMO ---
    if "Yoga Mat" in product_name:
        # Boldfit sells for $15. Competitor is higher.
        competitor_price = 19.99
    elif "Whey Protein" in product_name:
        # Boldfit sells for $49.99. Competitor is lower (a potential issue).
        competitor_price = 45.00 
    else:
        competitor_price = 28.00

    return f"The average competitor price for {product_name} is ${competitor_price:.2f}."

@tool
def send_restock_alert(product_name: str, quantity: int, reason: str):
    """
    Sends an alert to the Operations team via 'Slack' (Mocked).
    """
    print(f"\n🚨 [SLACK ALERT SENT]")
    print(f"To: #supply-chain-ops")
    print(f"Message: URGENT REORDER NEEDED for {product_name}.")
    print(f"Recommended Qty: {quantity}")
    print(f"AI Reasoning: {reason}")
    return "Alert sent successfully."

# --- STEP 3: THE BRAIN (Groq Setup) ---

llm = ChatGroq(
    model="llama-3.3-70b-versatile", 
    temperature=0
)

# New list of tools
tools = [analyze_inventory_risk, check_competitor_pricing, send_restock_alert]

prompt = ChatPromptTemplate.from_messages([
    ("system", """
    You are the 'Sentinel Analyst', an advanced AI for Boldfit Supply Chain.
    Your goal is to optimize both stock levels and profit margin.
    
    1. First, always check the inventory risk.
    2. If a product is at risk, IMMEDIATELY check the competitor's price for that product using the appropriate tool.
    3. Compare the current Boldfit price against the competitor price.
    4. Calculate a reasonable reorder quantity (30 days of stock).
    5. Send an alert using the alert tool, including a summary of the pricing analysis and your reorder recommendation.
    """),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# --- STEP 4: EXECUTION ---
if __name__ == "__main__":
    print("--- STARTING BOLDFIT SENTINEL ANALYST (Price-Aware) ---")
    query = "Check our warehouse status and make strategic recommendations for low-stock items."
    
    try:
        agent_executor.invoke({"input": query})
    except Exception as e:
        print(f"Error: {e}")