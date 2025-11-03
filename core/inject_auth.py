import asyncio
from playwright.async_api import async_playwright
import os
import json
import argparse
import sys # Import sys
from datetime import datetime # Import datetime

# ===== CONTAINER-RELATIVE PATHS =====
# Get the script's directory (e.g., /app/core)
SCRIPT_DIR = os.path.dirname(__file__)

# Paths are now relative to the /app directory inside the container
STORAGE_FILE = os.path.abspath(os.path.join(SCRIPT_DIR, "../storage_state.json"))
PROFILE_PATH = os.path.abspath(os.path.join(SCRIPT_DIR, "../meet_profile"))
# ===== END PATHS =====

async def inject_google_login(headless=True):
    print("="*50)
    print(f"🚀 Starting Cookie Injection (Headless: {headless})...")
    print(f"   Target Profile: {PROFILE_PATH}")
    print(f"   Source Cookies: {STORAGE_FILE}")
    print("="*50)

    # --- Ensure screenshot dir exists ---
    debug_screenshot_dir = os.path.abspath(os.path.join(SCRIPT_DIR, "../debug_screenshots"))
    os.makedirs(debug_screenshot_dir, exist_ok=True)
    print(f"   Debug Screenshots: {debug_screenshot_dir}")
    # --- END ---

    if not os.path.exists(STORAGE_FILE):
        print(f"❌ Storage file not found: {STORAGE_FILE}")
        print("   Make sure 'storage_state.json' is in the /app folder.")
        print("   Run 'python -m playwright codegen --save-storage=storage_state.json https://accounts.google.com' locally first.")
        return False # Return failure

    # Ensure profile path exists, but rely on user deleting old one before 'docker run' for a clean slate.
    os.makedirs(PROFILE_PATH, exist_ok=True)

    try:
        with open(STORAGE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            cookies = data.get("cookies", [])
            print(f"🍪 Loaded {len(cookies)} Google cookies from {STORAGE_FILE}")
            if not cookies:
                print("❌ No cookies found in storage_state.json. Regenerate the file.")
                return False
    except Exception as e:
        print(f"❌ FAILED to read storage_state.json: {e}")
        return False # Return failure

    async with async_playwright() as p:
        print(f"🌐 Launching browser with persistent profile (Headless: {headless})...")
        context = None # Define before try block
        try:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=PROFILE_PATH,
                headless=headless,
                args=[
                    "--start-maximized",
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox", # Important for Docker
                    "--disable-dev-shm-usage", # Important for Docker
                    # --- Force PulseAudio for injection browser too ---
                    "--alsa-output-device=pulse",
                    "--alsa-input-device=pulse",
                ],
                # Increase launch timeout slightly
                timeout=45000
            )
            print("✅ Browser context launched.")
        except Exception as e:
            print(f"❌ FAILED to launch browser context: {e}")
            return False # Return failure

        print("💉 Injecting cookies into the profile...")
        try:
            await context.add_cookies(cookies)
            print(f"✅ Injected {len(cookies)} cookies.")
            await asyncio.sleep(1.0) # Short pause after injection
        except Exception as e:
            print(f"⚠️ Failed to inject cookies: {e}")
            # Continue to verification, maybe some cookies worked

        print(f"🔍 Navigating to https://accounts.google.com/ to verify login status...")
        page = None
        screenshot_path = os.path.join(debug_screenshot_dir, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_inject_verify.png")
        is_success = False
        try:
            page = context.pages[0] if context.pages else await context.new_page()
            
            # Increased timeout for reliability
            await page.goto("https://accounts.google.com", wait_until="domcontentloaded", timeout=30000)
            print("   Page loaded. Waiting a bit for redirects/scripts...")
            await asyncio.sleep(4) # Increased wait time
            
            current_url = page.url
            page_title = await page.title()
            print(f"   Current URL: {current_url}")
            print(f"   Page Title: {page_title}")

            # --- Take verification screenshot ---
            await page.screenshot(path=screenshot_path)
            print(f"📸 Saved verification screenshot: {screenshot_path}")
            # --- END ---

            # --- Stricter Login Check ---
            # Look for a common element indicating a logged-in state.
            # Google often uses an img with alt="Google Account" or aria-label containing "Google Account"
            logged_in_selector = 'img[alt*="Google Account"], [aria-label*="Google Account"]'
            logged_in_indicator = page.locator(logged_in_selector).first
            
            is_indicator_visible = False
            try:
                # Wait briefly for the indicator to appear
                await logged_in_indicator.wait_for(state="visible", timeout=5000)
                is_indicator_visible = True
            except Exception:
                print("   Login indicator element not found or not visible quickly.")

            # Final decision based on indicator or URL/Title fallbacks
            if is_indicator_visible or "myaccount.google.com" in current_url or "Google Account" in page_title:
                print("="*50)
                print("✅ VERIFICATION SUCCESS: Looks like you are logged in!")
                print("="*50)
                is_success = True
            else:
                print("="*50)
                print("❌ VERIFICATION FAILED: Could not confirm login.")
                print(f"   Check the screenshot: {screenshot_path}")
                print(f"   Ensure the new storage_state.json was generated correctly and the old meet_profile was deleted.")
                print("="*50)
                
        except Exception as e:
            print(f"❌ Error during verification navigation or check: {e}")
            try: # Attempt error screenshot
                if page and not page.is_closed():
                    error_screenshot_path = screenshot_path.replace("_inject_verify.png", "_inject_verify_ERROR.png")
                    await page.screenshot(path=error_screenshot_path)
                    print(f"📸 Saved ERROR screenshot: {error_screenshot_path}")
            except Exception as ss_e:
                print(f"   Could not save error screenshot: {ss_e}")

        finally:
            print("Closing injection browser...")
            if context:
                await context.close()
            print("✅ Profile injection attempt complete.")
            return is_success

# (main execution block remains the same)
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--headless', dest='headless', action='store_true', help="Run headlessly (default)")
    parser.add_argument('--headful', dest='headless', action='store_false', help="Run with browser visible")
    parser.set_defaults(headless=True)
    args = parser.parse_args()
    
    # Run the injection and verification
    success = asyncio.run(inject_google_login(headless=args.headless))
    
    if not success:
        print("\n❌ Authentication injection failed verification. The bot will likely fail to join Meet.")
        print("   Please regenerate storage_state.json and delete the meet_profile directory before running again.")
        sys.exit(1) # Exit with error code to stop start_bot.sh
    else:
         print("\n✅ Authentication injection finished successfully.")