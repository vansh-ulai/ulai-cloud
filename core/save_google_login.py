import os
import json
import asyncio
from playwright.async_api import async_playwright

# Paths
PROFILE_PATH = r"C:\Ulai\ulai_meet_ai\playwright_notion_profile"
STORAGE_FILE = r"C:\Ulai\ulai_meet_ai\storage_state.json"  # your saved Google login cookies


async def inject_google_login():
    """Inject saved Google cookies into the persistent Notion+Meet profile."""
    if not os.path.exists(STORAGE_FILE):
        print(f"❌ Storage file not found: {STORAGE_FILE}")
        return

    os.makedirs(PROFILE_PATH, exist_ok=True)

    # Load saved cookies
    with open(STORAGE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        cookies = data.get("cookies", [])
        print(f"🍪 Loaded {len(cookies)} Google cookies from storage_state.json")

    async with async_playwright() as p:
        print("🌐 Launching your persistent Notion + Meet profile...")
        context = await p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_PATH,
            headless=False,
            args=[
                "--start-maximized",
                "--disable-blink-features=AutomationControlled"
            ],
        )

        page = context.pages[0] if context.pages else await context.new_page()

        # Add all cookies from storage_state.json
        try:
            await context.add_cookies(cookies)
            print(f"✅ Injected {len(cookies)} cookies into profile.")
        except Exception as e:
            print(f"⚠️ Failed to inject cookies: {e}")

        # Visit Google to verify
        await page.goto("https://accounts.google.com", wait_until="domcontentloaded")
        print("🔍 Checking Google login status...")

        await asyncio.sleep(5)
        current_url = page.url
        if "myaccount.google.com" in current_url:
            print("✅ Successfully logged into Google!")
        else:
            print(f"⚠️ Login might not be detected (URL: {current_url})")

        print("\n🎯 You can now use this profile for Meet automations too!")
        input("👉 Press ENTER to close browser...")

        await context.close()
        print("🟢 Done — Google cookies are now inside your Notion profile.")


if __name__ == "__main__":
    asyncio.run(inject_google_login())
