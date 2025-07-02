from dotenv import load_dotenv
load_dotenv()

from langchain.chat_models import init_chat_model
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
import yfinance as yf



class State(TypedDict):
    messages: Annotated[list, add_messages]

@tool
def get_live_stock_price(symbol: str) -> float:
    """
    Return the current price of a stock given the stock symbol.
    Uses yfinance and falls back on recent history if needed.
    """
    ticker = yf.Ticker(symbol)
    info = ticker.info or {}
    # Prefer currentPrice if available, else regularMarketPrice, else fetch from history
    price = info.get("currentPrice") or info.get("regularMarketPrice")
    if price is not None:
        return float(price)
    # Fallback to latest closing price from today’s data
    hist = ticker.history(period="1d", interval="1m")
    if not hist.empty:
        return float(hist["Close"].iloc[-1])
    return 0.0   


@tool
def buy_stocks(symbol: str, quantity: int, total_price: float) -> str:
    '''Buy stocks given the stock symbol and quantity'''
    decision = interrupt(f"Approve buying {quantity} {symbol} stocks for ${total_price:.2f}?")

    if decision == "yes":
        return f"You bought {quantity} shares of {symbol} for a total price of {total_price}"
    else:
        return "Buying declined."

#tools = [get_stock_price, buy_stocks]
tools = [get_live_stock_price]

llm = init_chat_model("google_genai:gemini-2.0-flash")
llm_with_tools = llm.bind_tools(tools)

def chatbot_node(state: State):
    msg = llm_with_tools.invoke(state["messages"])
    return {"messages": [msg]}

memory = MemorySaver()
builder = StateGraph(State)
builder.add_node("chatbot", chatbot_node)
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "chatbot")
builder.add_conditional_edges("chatbot", tools_condition)
builder.add_edge("tools", "chatbot")

graph = builder.compile(checkpointer=memory)



config1 = { 'configurable': { 'thread_id': '1'} }

# Step 1: user asks price
config1 = { 'configurable': { 'thread_id': '1'} }

msg = "I want to buy 20 DNUT stocks using current price. Then 15 SNOW. What will be the total cost?"

state = graph.invoke({"messages": [{"role": "user", "content": msg}]}, config=config1)
print(state["messages"][-1].content)

# Step 2: user asks to check another stock
config2 = { 'configurable': { 'thread_id': '2'} }

msg = "Tell me the current price of 5 LUV stocks."

state = graph.invoke({"messages": [{"role": "user", "content": msg}]}, config=config2)
print(state["messages"][-1].content)


# Step 3: user asks to buy 

msg = "Using the current price tell me the total price of 10 YUM stocks and add it to previous total cost"

state = graph.invoke({"messages": [{"role": "user", "content": msg}]}, config=config1)
print(state["messages"][-1].content)


# Step 4: user asks to buy
msg = "Tell me the current price of 5 SNOW stocks and add it to previous total"

state = graph.invoke({"messages": [{"role": "user", "content": msg}]}, config=config2)
print(state["messages"][-1].content)


#decision = input("Approve (yes/no): ")
#state = graph.invoke(Command(resume=decision), config=config)
#print(state["messages"][-1].content)



