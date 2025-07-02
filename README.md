# langgraph-tutorial
exploring langgraph, langsmith and langchain

🚀 Setup Instructions

1. Install required packages via pip: 

pip install python-dotenv
pip install -U langchain-google-genai
pip install langchain
pip install langgraph
pip install langsmith
pip install yfinance


langchain-google-genai requires Python 3.9–<4.0 and enables integration with Google Gemini models


2. Configure API keys

✅ Gemini API key (for Google Generative AI)
Go to Google AI Studio API key page and create a Gemini API key.

Add it to your .env file:

      GOOGLE_API_KEY=your‑gemini‑api‑key


✅ LangSmith API key (for observability and evaluation)

Sign in to LangSmith, go to Settings → API Keys, and create a Personal Access Token or Service Key.

Add to your .env file:
      LANGSMITH_API_KEY=your‑langsmith‑api‑key



