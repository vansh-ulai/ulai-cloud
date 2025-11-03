import asyncio
from playwright.async_api import async_playwright
import time
import os

# Go up one level (from 'core' to 'app') to find the profile directory
PROFILE_DIR = "../meet_profile"
TEST_URL = "https://accounts.google.com/"
# Save the screenshot in the main app folder so you can find it
SCREENSHOT_FILE = "../profile_test.png"

async def check_profile():
    print("="*50)
    print(f"🚀 Starting profile check...")
    
    # Get the absolute path *inside the container*
    # This will resolve to /app/meet_profile
    profile_abs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), PROFILE_DIR))
    screenshot_abs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), SCREENSHOT_FILE))

    print(f"Script location (inside container): {os.path.dirname(__file__)}")
    print(f"Target Profile directory (relative): {PROFILE_DIR}")
    print(f"Target Profile directory (absolute): {profile_abs_path}")
    
    if not os.path.exists(profile_abs_path):
        print(f"❌ CRITICAL: Profile directory '{profile_abs_path}' does not exist.")
        print("   Make sure your -v mount is correct and 'meet_profile' is in the root.")
        print("="*50)
        return
    else:
        print(f"✅ Found profile directory: '{profile_abs_path}'")

    print(f"🌐 Launching browser with persistent context...")
    
    async with async_playwright() as p:
        try:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=profile_abs_path, # Use the absolute path
                headless=True, # Run headless for this test
                args=["--no-sandbox"] # Add no-sandbox for Docker
            )
            page = await context.new_page()
            
            print(f"Navigating to: {TEST_URL}")
            await page.goto(TEST_URL, wait_until="domcontentloaded", timeout=15000)
            
            title = await page.title()
            print(f"Page title is: '{title}'")
            
            print(f"📸 Taking screenshot: {screenshot_abs_path}")
            await page.screenshot(path=screenshot_abs_path, full_page=True)
            
            await context.close()
            
            print("="*50)
            if "Sign in" in title or "Sign-in" in title:
                print("❌ TEST FAILED: The profile is NOT authenticated.")
                print(f"   Check '{screenshot_abs_path}' - it will show the login page.")
            else:
                print(f"✅ TEST PASSED: The profile IS authenticated!")
                print(f"   Check '{screenshot_abs_path}' - it should show your Google account page.")
            print("="*50)

        except Exception as e:
            print(f"❌ TEST FAILED with error: {e}")
            print("="*50)

if __name__ == "__main__":
    asyncio.run(check_profile())

