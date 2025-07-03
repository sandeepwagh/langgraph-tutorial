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
def buy_stocks_new(
    symbol1: str, quantity1: int,
    symbol2: str, quantity2: int,
    symbol3: str, quantity3: int,
    total_price: float
) -> str:
    '''Buy 3 different stocks given their symbols, quantities, and total price'''
    
    decision = interrupt(
        f"Approve buying:\n"
        f"- {quantity1} shares of {symbol1}\n"
        f"- {quantity2} shares of {symbol2}\n"
        f"- {quantity3} shares of {symbol3}\n"
        f"Total cost: ${total_price:.2f}?\n\n"
    )

    if decision == "yes":
        return (
            f"You bought:\n"
            f"- {quantity1} shares of {symbol1}\n"
            f"- {quantity2} shares of {symbol2}\n"
            f"- {quantity3} shares of {symbol3}\n"
            f"For a total price of ${total_price:.2f}\n\n"
        )
    elif decision == "no":
        return "\nBuying declined."
    else:
        return "Invalid response. Buying not executed."


tools = [get_live_stock_price, buy_stocks_new]

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
msg = "I want to buy 20 DNUT stocks using current price. Then 15 SNOW. What will be the total cost?"

state = graph.invoke({"messages": [{"role": "user", "content": msg}]}, config=config1)
print(state["messages"][-1].content)


# Step 2: user asks more prices and refers previous output

msg = "Using the current price tell me the total price of 10 YUM stocks and add it to previous total cost"

state = graph.invoke({"messages": [{"role": "user", "content": msg}]}, config=config1)
print(state["messages"][-1].content)

# Step 3: user asks to buy..  we cannot actually but but simulate it though using tool.
state = graph.invoke({"messages":[{"role":"user","content":"Buy all above stock quantities of stocks at current price"}]}, config=config1)
print(state.get("__interrupt__"))

decision = input("Approve (yes/no): ")
state = graph.invoke(Command(resume=decision), config=config1)
print(state["messages"][-1].content)



