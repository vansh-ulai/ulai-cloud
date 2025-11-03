import asyncio
from playwright.async_api import async_playwright

async def run(page, speak_func):
    """
    Asynchronous function to automate interactions with the Ulai website using Playwright.

    Args:
        page: The Playwright page object.
        speak_func: An asynchronous function to simulate text-to-speech (TTS) output.
    """

    await page.goto("https://ulai.in/")
    await speak_func("Navigating to Ulai website.")

    # Simulate realistic mouse movement to the "Book a Demo" button in the nav bar
    book_demo_link = page.locator('a', has_text='BOOK A DEMO').first
    await book_demo_link.hover()
    await speak_func("Hovering over the Book a Demo link.")
    await asyncio.sleep(1)  # Simulate user hesitation

    # Click the "Book a Demo" button
    await book_demo_link.click()
    await speak_func("Clicking the Book a Demo link.")
    await asyncio.sleep(3) # Give time to load the new page

    # Go back to the main page
    await page.go_back()
    await speak_func("Going back to the main page.")
    await asyncio.sleep(2)

    # Scroll down to the "How It Works" section
    how_it_works_heading = page.locator('h2', has_text='How It Works')
    await how_it_works_heading.scroll_into_view_if_needed()
    await speak_func("Scrolling to the How It Works section.")
    await asyncio.sleep(2)

    # Scroll down to the "Want To Experience It First Hand , Give It A Try?" section
    experience_heading = page.locator('h2', has_text='Want To Experience It First Hand , Give It A Try?')
    await experience_heading.scroll_into_view_if_needed()
    await speak_func("Scrolling to the 'Want To Experience It First Hand' section.")
    await asyncio.sleep(2)

    # Simulate clicking the "Industries" button
    industries_button = page.locator('button', has_text='Industries')
    await industries_button.click()
    await speak_func("Clicking the Industries button.")
    await asyncio.sleep(1)

    # Simulate clicking the "Healthcare" button
    healthcare_button = page.locator('button', has_text='Healthcare')
    await healthcare_button.click()
    await speak_func("Clicking the Healthcare button.")
    await asyncio.sleep(2)

    # Scroll back to the top of the page
    await page.evaluate("window.scrollTo(0, 0)")
    await speak_func("Scrolling back to the top of the page.")
    await asyncio.sleep(1)

    # Simulate hovering over the "LOGIN" button in the nav bar
    login_link = page.locator('a', has_text='LOGIN').first
    await login_link.hover()
    await speak_func("Hovering over the LOGIN link.")
    await asyncio.sleep(1)

    print("Ulai website demo completed.")
    await speak_func("Ulai website demo completed.")

async def speak(text):
    """
    Asynchronous function to simulate text-to-speech output.

    Args:
        text: The text to be "spoken".
    """
    print(f"TTS: {text}")
    await asyncio.sleep(0.5)  # Simulate TTS delay

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=250) # set headless=False to view the browser
        page = await browser.new_page()
        await run(page, speak)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())