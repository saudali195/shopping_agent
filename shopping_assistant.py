import os
import re
import requests
import chainlit as cl
from dotenv import load_dotenv
from agents import Agent, Runner, OpenAIChatCompletionsModel, AsyncOpenAI

# Load API key from .env
load_dotenv()
gemini_key = os.getenv("GEMINI_API_KEY")
if not gemini_key:
    raise ValueError("GEMINI_API_KEY missing in .env")

# Initialize Gemini model with OpenAI-compatible client
external = AsyncOpenAI(
    api_key=gemini_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai",
)
model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=external
)

def search_product_api(query: str) -> str:
    try:
        response = requests.get(
            "https://hackathon-apis.vercel.app/api/products",
            params={"q": query}
        )
        response.raise_for_status()
        products = response.json()

        # Extract relevant keywords from the query
        words = re.findall(r"\w+", query.lower())
        stopwords = {"the", "and", "is", "a", "in", "of", "for", "on", "with", "under", "above", "below", "best"}
        keywords = [word for word in words if word not in stopwords]

        matches = []
        for product in products:
            title = product.get("title", "").lower()
            price = product.get("price")
            if title and price and any(kw in title for kw in keywords):
                matches.append(f"- {product['title']} | Rs {price}")

        return "\n".join(matches) if matches else "⚠️ No matching products found."

    except Exception as error:
        return f"❌ API Error: {error}"

@cl.on_message
async def main(message: cl.Message):
    user_input = message.content.strip()

    # Create shopping assistant agent
    agent = Agent(
        name="Shopping Agent",
        instructions=(
            "You are a smart and friendly shopping assistant."
            " Respond clearly and help the user find suitable products."
        ),
        model=model
    )

    # Get AI response
    result = Runner.run_sync(agent, user_input)
    ai_response = result.final_output.strip()

    # Get product search results
    product_results = search_product_api(user_input)

    # Smooth, styled message output
    await cl.Message(
        content=f"""
✨ **AI Insight**
{ai_response}
""",
        author="🤖 Assistant",
    ).send()

    await cl.Message(
        content=f"""
🛒 **Search Results**
{product_results}
""",
        author="📦 Products",
    ).send()
