from core.local_llm import get_local_llm_response_async
import asyncio

async def main():
    prompt = "What is 2 + 2?"
    print("🧠 Testing local LLM...")
    result = await get_local_llm_response_async(prompt)
    print("✅ LLM output:", result)

asyncio.run(main())
