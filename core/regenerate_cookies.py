import asyncio
from playwright.async_api import async_playwright
import os
import json

# Get the script's directory (e.g., /mnt/d/Ulai/ulai_meet_ai/core)
SCRIPT_DIR = os.path.dirname(__file__)

# We will save the new cookies to the root folder
STORAGE_FILE = os.path.abspath(os.path.join(SCRIPT_DIR, "../storage_state.json"))
LOGIN_URL = "https://accounts.google.com/"

async def regenerate_cookie_file():
    print("="*50)
    print(f"🚀 Starting Fresh Cookie Generation...")
    print(f"   This will save new cookies to: {STORAGE_FILE}")
    print("="*50)
    print("----- INSTRUCTIONS -----")
    print(f"1. A new Chromium browser will open at: {LOGIN_URL}")
    print(f"2. Log in to your Google account.")
    print(f"3. After you are 100% logged in, COME BACK to this terminal.")
    print("="*50)
    
    # Use input() to start, as it's blocking anyway
    input("Press ENTER to begin...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        print(f"Navigating to {LOGIN_URL}...")
        await page.goto(LOGIN_URL)
        
        print("\n✅ Browser is open. Please log in now.")
        print("   ****************************************************")
        print("   IMPORTANT: After you are logged in,")
        print("   COME BACK TO THIS TERMINAL and press ENTER.")
        print("   Do NOT close the browser yourself.")
        print("   ****************************************************")
        
        # Wait for user to press Enter in the terminal
        # Use asyncio.to_thread to run the blocking input() call
        await asyncio.to_thread(input, "Press ENTER here after you have successfully logged in...")
        
        print("✅ User has logged in. Saving cookie state...")
        
        # Save the storage state (cookies, local storage)
        try:
            storage_state = await context.storage_state()
            with open(STORAGE_FILE, 'w', encoding='utf-8') as f:
                json.dump(storage_state, f, indent=4)
            
            print(f"✅✅✅ Fresh 'storage_state.json' has been saved!")
            print(f"   Cookies found: {len(storage_state.get('cookies', []))}")
            print("="*50)
        except Exception as e:
            print(f"❌ FAILED to save storage state: {e}")
            print("="*50)

        print("Closing browser...")
        await context.close()

if __name__ == "__main__":
    asyncio.run(regenerate_cookie_file())

