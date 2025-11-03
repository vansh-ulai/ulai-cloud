import asyncio
import random
from playwright.async_api import Page

async def human_like_click(page, selector):
    """Clicks a selector with a small delay to simulate human interaction."""
    await asyncio.sleep(random.uniform(0.2, 0.5))
    await page.click(selector)

async def scroll_and_reveal(page, speak_func):
    """Scrolls through the entire page, revealing content and narrating."""
    await speak_func("Scrolling through the page to reveal all content.")
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await asyncio.sleep(1)  # Give time for content to load after scrolling
    await page.evaluate("window.scrollTo(0, 0)")
    await asyncio.sleep(1)

async def handle_new_pages(page, browser_context, speak_func):
    """Handles any new pages that open during the demo."""
    while len(browser_context.pages) > 1:
        new_page = None
        for p in browser_context.pages:
            if p != page:
                new_page = p
                break

        if new_page:
            await speak_func("A new page has opened. Closing it and returning to the main page.")
            await new_page.close()
            await page.bring_to_front()
        else:
            await asyncio.sleep(0.5) # Check again soon

async def run(page: Page, speak_func):
    """
    This function contains the main demo script for the Ulai website.
    """
    await speak_func("Starting the Ulai website demo.")

    # 1. Visit the homepage
    await speak_func("Navigating to the Ulai homepage: ulai.in")
    await page.goto("https://ulai.in/")

    # 2. Analyze the Hero Section
    await speak_func("Analyzing the hero section of the homepage.")
    main_heading = await page.locator("h1").first().inner_text()
    await speak_func(f"The main heading is: {main_heading}")

    # 3. Scroll and Reveal
    await scroll_and_reveal(page, speak_func)

    # 4. Interact with Navigation
    await speak_func("Exploring the navigation bar.")
    await speak_func("Clicking the 'Platform' link.")
    await human_like_click(page, "text=Platform")

    await speak_func("Navigating back to the home page.")
    await page.go_back()
    await asyncio.sleep(1)

    # 5. Interact with a Call-to-Action
    await speak_func("Clicking the 'Book A Demo' button.")
    await human_like_click(page, "text=Book A Demo")
    await asyncio.sleep(2) # Give the page time to react
    # 6. Handle new page if opened
    browser_context = page.context
    await handle_new_pages(page, browser_context, speak_func)

    # 7. Interact with another Call-to-Action
    await speak_func("Clicking the 'Try for free' button.")
    await human_like_click(page, "text=Try for free")
    await asyncio.sleep(2) # Give the page time to react
    # 8. Handle new page if opened
    browser_context = page.context
    await handle_new_pages(page, browser_context, speak_func)

    #9 Navigate to Login Page
    await speak_func("Navigating to the login page.")
    await human_like_click(page, "text=LOGIN")
    await speak_func("Now on the login page.")
    await asyncio.sleep(1)
    await page.go_back()
    await asyncio.sleep(1)

    # 10. Visit the "How It Works" section (if it's a separate page - otherwise, scroll to it)
    try:
        await speak_func("Navigating to the 'How It Works' section.")
        await human_like_click(page, "text=How It Works")
        await scroll_and_reveal(page, speak_func)
        browser_context = page.context
        await handle_new_pages(page, browser_context, speak_func)

    except Exception as e:
        await speak_func("'How it Works' not found as a link.  Scrolling to it if it exists on this page.")
        await scroll_and_reveal(page, speak_func)


    await speak_func("Demo completed. Thank you for watching!")
    return True