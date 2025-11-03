import asyncio
from playwright.async_api import async_playwright

async def human_like_click(page, selector, delay_min=0.05, delay_max=0.2):
    """
    Performs a click on a page element with a human-like delay.

    Args:
        page: The Playwright page object.
        selector: The CSS selector or XPath of the element to click.
        delay_min: Minimum delay in seconds before clicking.
        delay_max: Maximum delay in seconds before clicking.
    """
    delay = delay_min + (delay_max - delay_min) * asyncio.get_event_loop().time() % 1
    await asyncio.sleep(delay)
    await page.click(selector)

async def run(page, speak_func):
    """
    Navigates the Ulai website and interacts with elements.

    Args:
        page: The Playwright page object.
        speak_func: An optional function to simulate speech (not used in this example).
    """

    await page.goto("https://ulai.in/")
    print(f"Page title: {await page.title()}")

    # Click on "BOOK A DEMO" button in the nav bar.
    await human_like_click(page, "text=BOOK A DEMO")
    print("Clicked on BOOK A DEMO in nav")
    await asyncio.sleep(2) # Give time for the page to load
    await page.go_back()
    print("Going back to main page")
    await asyncio.sleep(2)

    # Scroll down and click on "Industries" button.
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await asyncio.sleep(1) #Give time to scroll
    await human_like_click(page, "text=Industries")
    print("Clicked on Industries button.")
    await asyncio.sleep(2)
    await page.go_back()
    print("Going back to main page")
    await asyncio.sleep(2)

    # Click on "What is Ulai?" expand button
    await human_like_click(page, "text=What is Ulai?\n+")
    print("Clicked on 'What is Ulai?' button")

    # Click on "How can Ulai help my business?" expand button
    await human_like_click(page, "text=How can Ulai help my business?\n+")
    print("Clicked on 'How can Ulai help my business?' button")

    await asyncio.sleep(2)

async def main():
    async with aasync_playwright() as p:
        browser = await p.chromium.launch(headless=False) #Set to False to see browser
        page = await browser.new_page()
        await run(page, None) #No speak_func in this example
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())