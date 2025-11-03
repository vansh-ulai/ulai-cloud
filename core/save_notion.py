import asyncio
from playwright.async_api import async_playwright
import os

# ✅ New dedicated Playwright profile folder
PROFILE_PATH = r"C:\Ulai\ulai_meet_ai\playwright_notion_profile"
NOTION_URL = "https://www.notion.so"

async def main():
    os.makedirs(PROFILE_PATH, exist_ok=True)

    print("--- 🧠 Creating persistent Notion Playwright profile ---")
    print(f"Profile path: {PROFILE_PATH}")
    print("\n👉 A Chromium window will open. Log in to Notion (Google/email).")
    print("Once your workspace loads, close the browser manually.\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_PATH,
            headless=False,
            args=[
                "--start-maximized",
                "--disable-blink-features=AutomationControlled",
            ],
        )

        page = browser.pages[0] if browser.pages else await browser.new_page()
        await page.goto(NOTION_URL)
        print("🌐 Notion opened. Please log in manually...")

        # Wait for the user to log in
        try:
            await page.wait_for_selector("div[aria-label='Notion sidebar']", timeout=600000)
            print("✅ Detected Notion workspace! Login complete.")
        except:
            print("⚠️ Timeout waiting for workspace. Make sure you log in fully.")

        print("\nWhen done, close the Chromium window manually.")
        input("Then press Enter here to finalize and save your session... ")

        await browser.close()
        print("🟢 Done! Your Notion login is now saved permanently in:")
        print(PROFILE_PATH)

if __name__ == "__main__":
    asyncio.run(main())
