import asyncio
import random
from playwright.async_api import async_playwright

async def human_like_click(page, selector):
    """Clicks a selector with a small random offset to simulate human-like interaction."""
    try:
        bounding_box = await page.locator(selector).bounding_box()
        if bounding_box:
            x = bounding_box["x"] + random.uniform(5, bounding_box["width"] - 5)
            y = bounding_box["y"] + random.uniform(5, bounding_box["height"] - 5)
            await page.mouse.click(x, y)
        else:
            print(f"Bounding box not found for selector: {selector}")
            await page.locator(selector).click()  # Fallback
    except Exception as e:
        print(f"Error during human-like click on {selector}: {e}")
        await page.locator(selector).click()  # Last resort


async def scroll_to_bottom(page):
    """Scrolls the page to the bottom."""
    try:
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(1)  # Give it a moment to load any lazy-loaded content
    except Exception as e:
        print(f"Error scrolling to bottom: {e}")


async def speak_func(narration):
    """Simulates narration with a print statement.  Replace with actual TTS if desired."""
    print(f"NARRATION: {narration}")


async def run(playwright):
    try:
        browser = await playwright.chromium.launch(headless=False, slow_mo=50)  # Launch in headful mode for demonstration
        context = await browser.new_context()
        page = await context.new_page()

        # 1. Home Page Demonstration
        await speak_func("Navigating to the Ulai homepage to showcase the AI Voice Agent Platform.")
        await page.goto("https://ulai.in/")
        await page.wait_for_load_state()
        await speak_func("Let's take a quick look at the main heading, describing the platform's capability to launch an AI agent in under 15 minutes without coding.")
        heading_text = await page.locator("h1").inner_text()
        print(f"Main Heading: {heading_text}")
        await asyncio.sleep(2)

        await scroll_to_bottom(page)
        await speak_func("Scrolling down to explore the key sections like 'How it Works' and 'Enterprise' offerings.")
        await asyncio.sleep(3)

        # Demonstrate button clicks on the homepage
        await speak_func("Now, let's interact with a button. We'll click on the 'Introduction' button to see where it leads us.")
        await human_like_click(page, "text=Introduction") # Click the "Introduction" button
        await page.wait_for_load_state()
        await asyncio.sleep(3) # Give the page time to load

        await page.go_back() # return to the homepage
        await page.wait_for_load_state()
        await asyncio.sleep(2)

        # Demonstrate button clicks on the homepage
        await speak_func("Let's try to click the 'Book a Demo' button to show potential lead generation flow.")
        await human_like_click(page, "text=BOOK A DEMO") # Click the "Book a Demo" button
        await page.wait_for_load_state()
        await asyncio.sleep(5) # Give the page time to load
        await page.go_back() # return to the homepage
        await page.wait_for_load_state()
        await asyncio.sleep(2)


        # 2. Navigate to the Login Page
        await speak_func("Next, let's navigate to the Login page to demonstrate user authentication.")
        await human_like_click(page, "text=LOGIN")  # Click the "LOGIN" button
        await page.wait_for_load_state()
        await speak_func("Here we have the login form.  We'll inspect the elements, but not attempt a login as we don't have credentials.")
        print("Login Page URL:", page.url)
        await asyncio.sleep(3)

        # 3. Attempt to sign up (navigate and show signup form)
        await speak_func("Now, let's see the signup process. We will try clicking on the 'Sign Up' button.")
        await human_like_click(page, "text=Sign Up")  # Click the "Sign Up" button
        await page.wait_for_load_state()
        print("Signup Page URL:", page.url)
        await speak_func("Here is the signup form, including fields for name, email, password, and confirmation.  We will highlight the fields and the 'Create Account' button.")
        await asyncio.sleep(5)


        # 4. Fill in the Sign Up form (partially, for demonstration)
        await speak_func("We'll begin to fill in the sign-up form to demonstrate the interaction. We will enter a name and email.")
        await page.fill("input[name='fullName']", "Demo User")
        await page.fill("input[name='email']", "demo.user@example.com")
        await asyncio.sleep(2)  # Pause to show filled fields

        # Highlight the "Create Account" button before (not) clicking
        await speak_func("Finally we will hover over the 'Create Account' button, but not click it to prevent an actual account creation during the demo.")
        create_account_button = page.locator("text=Create Account")
        await create_account_button.hover()
        await asyncio.sleep(2)

        # 5. Go back to the Home Page
        await speak_func("Returning to the homepage to conclude the demonstration.")
        await page.goto("https://ulai.in/")
        await page.wait_for_load_state()
        await asyncio.sleep(3)


        await context.close()
        await browser.close()

        return True  # Indicate success

    except Exception as e:
        print(f"An error occurred: {e}")
        return False

async def main():
    async with async_playwright() as playwright:
        success = await run(playwright)
        if success:
            print("Demo script executed successfully!")
        else:
            print("Demo script failed.")

if __name__ == "__main__":
    asyncio.run(main())