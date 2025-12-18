import pandas as pd
import os
import io
import sys
import streamlit as st # Added for secret handling
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
# Break these into separate imports to help the cloud find them
from langchain.agents import AgentExecutor
from langchain.agents import create_tool_calling_agent

# --- CONFIGURATION ---
# PASTE YOUR GROQ KEY HERE INSIDE THE QUOTES
# This key MUST be set here for the agent to initialize.
os.environ["GROQ_API_KEY"]= st.secrets["GROQ_API_KEY"] 

# --- INITIAL MOCK DATA ---
# This dictionary is the starting point for the editor.
INITIAL_DATA_MOCK = {
    "product_name": ["Pro Yoga Mat", "Whey Protein (Chocolate)", "Resistance Bands Set"],
    "current_stock": [15, 500, 45], # Low stock item
    "daily_burn_rate": [3, 10, 2],    
    "lead_time_days": [7, 14, 5],     
    "current_price": [15.00, 49.99, 25.00] 
}

# --- GLOBAL VARIABLES FOR AGENT RUNTIME ---
# We will store the CURRENT DataFrame from the editor here
GLOBAL_DF = pd.DataFrame(INITIAL_DATA_MOCK) 
# We need to capture the agent's log output
AGENT_LOG = io.StringIO()

# --- AGENT TOOLS (MUST use the GLOBAL_DF updated by the editor) ---

@tool
def analyze_inventory_risk(threshold_days: int = 10) -> str:
    """
    Analyzes current inventory. Returns a list of products that will run out 
    of stock within the specified threshold days, using the current dashboard data.
    """
    st.info(f"[SYSTEM] Invoking: analyze_inventory_risk (Threshold: {threshold_days} days)")
    
    # Use the globally updated DataFrame
    df_current = GLOBAL_DF.copy() 
    
    df_current['days_remaining'] = df_current['current_stock'] / df_current['daily_burn_rate']
    urgent_items = df_current[df_current['days_remaining'] <= threshold_days]
    
    if urgent_items.empty:
        return "All stock levels are healthy."
    
    # Return JSON for the LLM
    return urgent_items[['product_name', 'current_stock', 'daily_burn_rate', 'days_remaining', 'current_price']].to_json(orient="records")

@tool
def check_competitor_pricing(product_name: str) -> str:
    """
    Mocks checking the market price for a product from a competitor API.
    """
    st.info(f"[SYSTEM] Invoking: check_competitor_pricing for {product_name}...")
    
    # Mock Logic - you can edit these values if you want to show a different scenario
    if "Yoga Mat" in product_name:
        competitor_price = 19.99
    elif "Whey Protein" in product_name:
        competitor_price = 45.00 
    else:
        competitor_price = 28.00

    return f"The average competitor price for {product_name} is ${competitor_price:.2f}."

@tool
def send_restock_alert(product_name: str, quantity: int, reason: str):
    """
    Sends an alert to the Operations team via the dashboard.
    """
    with st.container(border=True):
        st.error(f"🚨 URGENT ALERT: REORDER NEEDED")
        st.write(f"**Product:** `{product_name}`")
        st.write(f"**Recommended Quantity:** `{quantity} units`")
        st.write(f"**AI Justification:** {reason}")
    return "Alert displayed successfully on dashboard."

# --- AGENT CORE FUNCTION ---
def run_agent(user_query, tools):
    """Initializes and runs the Groq Agent."""
    
    try:
    # We pull the key from st.secrets and pass it as 'groq_api_key'
    	llm = ChatGroq(
        	groq_api_key=st.secrets["GROQ_API_KEY"], 
        	model_name="llama-3.3-70b-versatile", 
        	temperature=0
   	 	)
    except Exception as e:
    	st.error(f"Failed to initialize Groq: {e}. Check your API key in Streamlit 	Secrets.")
    	st.stop() # Stops the app here so it doesn't crash later

    prompt = ChatPromptTemplate.from_messages([
        ("system", """
        You are the 'Sentinel Analyst', an advanced AI for Boldfit Supply Chain.
        Your primary goal is to optimize stock levels and profit margin.
        
        1. First, always check the inventory risk.
        2. IF THE INVENTORY IS HEALTHY (no risk is reported by the tool), IMMEDIATELY FINISH the task and provide a brief summary that all stock is good. DO NOT call any other tools.
        3. IF a product IS AT RISK (JSON data is returned), proceed to check the competitor's price for that product.
        4. Compare prices, calculate a 30-day reorder quantity, and send an alert, including a summary of the pricing analysis and your reorder recommendation.
        """),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    with st.spinner("🤖 Sentinel Analyst is analyzing data..."):
        # Temporarily capture the standard output (verbose=True)
        global AGENT_LOG
        AGENT_LOG = io.StringIO()
        
        # Capture the LLM's thought process (verbose output)
        sys.stdout = AGENT_LOG
        result = agent_executor.invoke({"input": user_query})
        sys.stdout = sys.__stdout__ # Restore console output
        
        # Display the final summary
        st.success("Analysis Complete!")
        st.write("---")
        st.markdown(f"**Final Agent Summary:** {result['output']}")


# --- STREAMLIT APP LAYOUT ---
st.set_page_config(page_title="Boldfit Sentinel Analyst", layout="wide")

st.title("🛒 Boldfit Sentinel Analyst (Interactive Demo)")
st.caption("Edit the inventory data below and run the agent to see real-time supply chain intelligence.")

# 1. INTERACTIVE DATA EDITOR
st.subheader("1. 📊 Editable Inventory Snapshot")

# Use st.data_editor to allow live editing
edited_df = st.data_editor(
    pd.DataFrame(INITIAL_DATA_MOCK),
    num_rows="dynamic",
    use_container_width=True,
    key="inventory_editor",
)

# Crucial step: Update the global variable with the edited data
GLOBAL_DF = edited_df

st.write("---")

# 2. USER INTERACTION
st.subheader("2. 🤖 Run Agent Analysis")

user_input = st.text_input(
    "Ask the Agent to take action:",
    value="Check our warehouse status and make strategic recommendations for low-stock items."
)

if st.button("▶️ Run Agent Analysis", type="primary"):
    if os.environ.get("GROQ_API_KEY") == "gsk_...":
        st.error("❌ ERROR: Please replace 'gsk_...' with your actual Groq API Key in the Python script.")
    else:
        # Run the agent with the current edited data
        run_agent(user_input, tools=[analyze_inventory_risk, check_competitor_pricing, send_restock_alert])

st.write("---")

# 3. VERBOSE LOG DISPLAY
st.subheader("3. 🧠 Agent's Thought Process (Verbose Log)")
st.code(AGENT_LOG.getvalue(), language='bash')