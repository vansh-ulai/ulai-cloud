# run_notion_demo.py
import asyncio
import logging
import sys
from playwright.async_api import async_playwright
from core import notion_handler

# --- Basic Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# --- Mock Speaker Function ---
# This function will print what the AI would say, instead of using TTS.
# This makes debugging much faster.
async def log_speaker(text: str):
    """A simple speaker function that just logs the text to the console."""
    logging.info(f"🤖 AI SAYS: {text}")
    # We add a tiny delay to simulate the time it would take to speak.
    await asyncio.sleep(0.1)

# --- Main Execution Block ---
async def main():
    """
    Launches Notion using the saved profile and runs the full demo sequence.
    """
    logging.info("🚀 Starting Notion Standalone Demo...")
    
    async with async_playwright() as p:
        try:
            # Launch the browser with your saved Notion login session
            context, notion_page = await notion_handler.launch_notion_with_profile(p)
            
            # Run the entire demo sequence from start to finish
            await notion_handler.run_demo_sequence(notion_page, log_speaker)
            
        except Exception as e:
            logging.exception(f"An error occurred during the demo execution: {e}")
        finally:
            # Keep the browser open for a while so you can inspect the final page state
            logging.info("✅ Demo finished. Browser will close in 60 seconds.")
            await asyncio.sleep(60)
            logging.info("Closing browser.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("🛑 User interrupted. Shutting down.")