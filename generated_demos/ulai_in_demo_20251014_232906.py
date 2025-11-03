``python
import asyncio
from playwright.async_api import async_playwright


async def human_like_click(page, selector):
    """
    Performs a human-like click on the specified element.
    """
    await page.hover(selector)
    await asyncio.sleep(0.2)  # Simulate user hesitation
    await page.click(selector)
    await asyncio.sleep(0.1)  # Small delay after click


async def run(page, speak_func):
    """
    Navigates the Ulai website and interacts with elements.
    """
    await speak_func("Navigating to Ulai website.")
    await page.goto("https://ulai.in/")
    await asyncio.sleep(2)

    await speak_func("Clicking on Book a Demo button.")
    await human_like_click(page, "text=BOOK A DEMO")
    await asyncio.sleep(3)
    await page.go_back()
    await asyncio.sleep(2)

    await speak_func("Clicking on How It Works button.")
    await human_like_click(page, "text=How it Works")
    await asyncio.sleep(3)

    await speak_func("Going back to the homepage.")
    await page.go_back()
    await asyncio.sleep(2)

    await speak_func("Clicking on Login button.")
    await human_like_click(page, "text=LOGIN")
    await asyncio.sleep(3)
    await page.go_back()
    await asyncio.sleep(2)



async def main():
    """
    Main function to run the Playwright script.
    """

    async def speak(text):
        """
        Placeholder for text-to-speech functionality.  Replace with your preferred method.
        """
        print(f"Speaking: {text}")

    async with aasync_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Set headless to False to see the browser
        page = await browser.new_page()
        await run(page, speak)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
`