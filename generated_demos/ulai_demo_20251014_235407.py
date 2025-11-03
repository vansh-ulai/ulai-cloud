import asyncio
import random
from playwright.async_api import Page

async def human_like_click(page: Page, selector: str):
    """Clicks a button or link with a bit of human-like variation."""
    try:
        element = await page.locator(selector).first
        if element:
            await element.hover()  # Hover before clicking, like a human
            await asyncio.sleep(random.uniform(0.1, 0.3))  # Slight delay
            await element.click()
            await asyncio.sleep(random.uniform(0.2, 0.5))  # Pause after click
            return True
        else:
            return False
    except Exception as e:
        print(f"Error clicking {selector}: {e}")
        return False


async def scroll_and_reveal(page: Page, speak_func):
    """Scrolls through the page, revealing content and narrating."""
    await speak_func("Scrolling down the page to reveal all the content.")
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await asyncio.sleep(2)  # Give time for content to load

    await speak_func("Scrolling back to the top.")
    await page.evaluate("window.scrollTo(0, 0)")
    await asyncio.sleep(1)


async def handle_new_pages(page: Page, speak_func):
    """Handles any new pages that might open during the demo."""
    new_pages = page.context.pages
    if len(new_pages) > 1:
        await speak_func("A new page has opened. I will examine it and then close it to return to the main demo page.")
        for new_page in new_pages:
            if new_page != page:
                await new_page.bring_to_front()
                await asyncio.sleep(1)
                await speak_func(f"New page title: {await new_page.title()}")
                await asyncio.sleep(1)
                await new_page.close()
                await page.bring_to_front()
        await speak_func("New page closed. Returning to the main demo.")


async def run(page: Page, speak_func) -> bool:
    """
    This function contains the main logic for the Playwright demo.
    It navigates to the Ulai website, interacts with elements, and narrates the process.
    """
    try:
        await speak_func("Hello, welcome to the Ulai AI demo.")
        await speak_func("Navigating to the Ulai website: ulai.in")
        await page.goto("https://ulai.in/")
        await asyncio.sleep(2)

        await speak_func(f"The title of the page is: {await page.title()}")
        await speak_func("We are now on the homepage. Let's explore the hero section.")

        # Hero Section narration
        await speak_func("The main heading is: Go live with your AI agent in under 15 minutes—no coding, no delays.")
        await speak_func("Ulai helps deploy hyper personalized AI agents for answering, selling, and support across phone, WhatsApp, and web.")

        # Buttons in Hero Section
        await speak_func("Now I will click on the 'Book A Demo' button")
        if await human_like_click(page, "text=Book A Demo"):
             await handle_new_pages(page, speak_func)  # Handle potential new page
        else:
            await speak_func("The 'Book A Demo' button was not found.")

        await speak_func("Scrolling down to explore the features.")
        await scroll_and_reveal(page, speak_func)

        # Features Section narration
        await speak_func("Ulai is a full-stack platform to build and deploy intelligent voice and text agents with real-time control and analytics.")
        await speak_func("It helps create intelligent voice agents that hold natural conversations and automate support and sales.")

        # Navigation Menu
        await speak_func("Let's check out the 'Platform' link.")
        await human_like_click(page, "text=Platform")
        await asyncio.sleep(2)
        await page.go_back() #return to home page
        await asyncio.sleep(2)

        # Footer Links
        await speak_func("Now, I will click on the 'Industries' link.")
        await human_like_click(page, "text=Industries")
        await asyncio.sleep(2)
        await page.go_back() #return to home page
        await asyncio.sleep(2)

        # Try for Free button
        await speak_func("Now I will click on the 'Try for free' button.")
        if await human_like_click(page, "text=Try for free"):
             await handle_new_pages(page, speak_func)  # Handle potential new page
        else:
            await speak_func("The 'Try for free' button was not found.")

        # Open Login Page
        await speak_func("Let's take a look at the login page.")
        await human_like_click(page, "text=LOGIN")
        await asyncio.sleep(2)

        await speak_func(f"The title of the page is: {await page.title()}")

        await speak_func("Now I will go back to the homepage.")
        await page.go_back()
        await asyncio.sleep(2)

        await speak_func("This concludes the Ulai website demo.")
        return True

    except Exception as e:
        print(f"An error occurred during the demo: {e}")
        return False