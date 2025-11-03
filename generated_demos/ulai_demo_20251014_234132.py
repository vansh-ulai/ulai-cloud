import asyncio
from playwright.async_api import Page
import random

async def human_like_click(page, selector, description=""):
    """Clicks on an element with a slight delay to simulate human interaction."""
    try:
        await page.wait_for_selector(selector, state="visible")
        await asyncio.sleep(random.uniform(0.1, 0.5))  # Small delay before click
        print(f"Clicking: {description} ({selector})")  # Log the click
        await page.click(selector)
        await asyncio.sleep(random.uniform(0.3, 0.8))  # Small delay after click
    except Exception as e:
        print(f"Error clicking {description} ({selector}): {e}")
        return False
    return True

async def scroll_and_reveal(page):
    """Scrolls the page in increments to reveal all content."""
    try:
        await page.evaluate("window.scrollTo(0, 0)") #Scroll to top
        await asyncio.sleep(1)

        total_height = await page.evaluate("document.body.scrollHeight")
        viewport_height = await page.evaluate("window.innerHeight")
        scroll_increment = viewport_height * 0.75  # Scroll in smaller increments

        current_position = 0
        while current_position < total_height:
            await page.evaluate(f"window.scrollTo(0, {current_position})")
            current_position += scroll_increment
            await asyncio.sleep(0.5)
            await page.wait_for_timeout(500) # give time to load content

    except Exception as e:
        print(f"Error scrolling: {e}")
        return False
    return True

async def run(page: Page, speak_func):
    """
    Demonstrates the Ulai website features.
    """
    try:
        # 1. Initial setup and navigation
        await speak_func("Navigating to the Ulai homepage to showcase the AI voice agent platform.")
        await page.goto("https://ulai.in/")

        # 2. Scroll to reveal content
        await speak_func("Scrolling through the homepage to reveal key sections and features.")
        if not await scroll_and_reveal(page):
            await speak_func("Scrolling failed, but proceeding with the demo.")  # Don't stop the demo

        # 3. Displaying Headings
        await speak_func("Displaying the main headings to understand the platform's core value proposition.")
        headings = await page.locator("h1, h2, h3, h4, h5, h6").all_text_contents()
        for heading in headings:
            print(f"Heading: {heading}")

        # 4. Interacting with CTAs: Book a Demo
        await speak_func("Attempting to click the 'Book a Demo' button to show the lead generation process.")
        if not await human_like_click(page, "text=BOOK A DEMO", "Book a Demo button"):
            await speak_func("Could not click 'Book a Demo', it might not be visible. Proceeding...")

        await asyncio.sleep(2) # Give time to load the next page if button worked

        # 5. Interacting with CTAs: Introduction
        await speak_func("Returning to the homepage and now clicking the 'Introduction' button.")
        await page.goto("https://ulai.in/")  # Go back to home
        if not await human_like_click(page, "text=Introduction", "Introduction Button"):
            await speak_func("Could not click 'Introduction', it might not be visible. Proceeding...")

        await asyncio.sleep(2) # Give time to load the next page if button worked

        #6. Try Use Case Link. Go back to Homepage first
        await speak_func("Returning to the homepage and clicking the 'Try Use Case' button.")
        await page.goto("https://ulai.in/")  # Go back to home
        if not await human_like_click(page, "text=Try Use Case", "Try Use Case Button"):
            await speak_func("Could not click 'Try Use Case', it might not be visible. Proceeding...")

        await asyncio.sleep(2) # Give time to load the next page if button worked

        #7. Click on Login and go to Login Page
        await speak_func("Returning to the homepage and navigating to the Login Page.")
        await page.goto("https://ulai.in/")  # Go back to home
        if not await human_like_click(page, "text=LOGIN", "Login Button"):
            await speak_func("Could not click 'Login', it might not be visible. Proceeding...")

        await asyncio.sleep(2)

        #8. Navigate to the Signup page
        await speak_func("Navigating to the Signup page.")
        await page.goto("https://infra.ulai.in/signup")

        #Fill out the signup form
        await speak_func("Filling out the signup form with example data.")
        await page.fill("input[name='fullName']", "Test User")
        await page.fill("input[name='email']", "test@example.com")
        await page.fill("input[name='password']", "Password123!")
        await page.fill("input[name='confirmPassword']", "Password123!")

        await speak_func("Attempting to click the 'Create Account' button.")
        if not await human_like_click(page, "text=Create Account", "Create Account Button"):
             await speak_func("Could not click Create Account button")
        await asyncio.sleep(2)

        # 9. Final Message
        await speak_func("Demonstration complete. This showcased basic navigation, interaction, and form submission on the Ulai platform.")

        return True

    except Exception as e:
        print(f"An error occurred during the demo: {e}")
        await speak_func(f"An error occurred during the demo: {e}")
        return False