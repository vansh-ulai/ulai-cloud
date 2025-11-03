import asyncio
from playwright.async_api import Page

async def run(page: Page, speak_func):
    try:
        # Introduction
        await speak_func("Hello! I'm here to demonstrate the website ulai.in using Playwright automation. I will provide a narrated walkthrough of the site's key features and sections.")
        await asyncio.sleep(2)

        # Navigate
        await speak_func("Now, let's navigate to the homepage of ulai.in.")
        await page.goto("https://ulai.in/", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)

        # Explore header
        await speak_func("The page has loaded successfully. At the top, we can see the main navigation elements including the logo and menu items.")
        await asyncio.sleep(2)

        # Scroll section 1
        await speak_func("Let's scroll down to the first main section of the website.")
        await page.evaluate("window.scrollBy(0, 400)")
        await asyncio.sleep(2)

        await speak_func("This section appears to highlight the core value proposition of Ulai AI Agent, focusing on its key benefits and features.")
        await asyncio.sleep(3)

        # Scroll section 2
        await page.evaluate("window.scrollBy(0, 400)")
        await asyncio.sleep(2)
        await speak_func("Moving further down, we can see a section dedicated to showcasing specific features or use cases of the AI agent.")
        await asyncio.sleep(3)

        # Scroll section 3
        await page.evaluate("window.scrollBy(0, 400)")
        await asyncio.sleep(2)
        await speak_func("This section might contain customer testimonials, case studies, or social proof to build trust and credibility.")
        await asyncio.sleep(3)

        # Scroll section 4
        await page.evaluate("window.scrollBy(0, 400)")
        await asyncio.sleep(2)
        await speak_func("Here's another section, potentially highlighting different aspects of the Ulai AI Agent or providing additional information.")
        await asyncio.sleep(3)

        # Try to find interactive elements
        await speak_func("Let's check for interactive elements like buttons or forms on the page.")
        await asyncio.sleep(2)

        try:
            buttons = await page.query_selector_all('button, a[class*="button"], [class*="cta"]')
            if buttons:
                await speak_func(f"I found {len(buttons)} interactive elements on this page, such as buttons and call-to-action links.")
                await asyncio.sleep(2)
                try:
                    await buttons[0].hover()
                    await asyncio.sleep(2)
                except:
                    await speak_func("Could not hover on the first button")
                    await asyncio.sleep(2)
        except:
            await speak_func("I was unable to identify specific interactive elements using standard selectors.")
            await asyncio.sleep(2)

        # Scroll to footer
        await speak_func("Finally, let's scroll down to the footer section of the website.")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(3)

        await speak_func("The footer typically contains links to important pages like contact information, terms of service, and privacy policy.")
        await asyncio.sleep(2)

        # Slow scrolling
        await speak_func("Now, I will slowly scroll up the page to demonstrate the content.")
        await asyncio.sleep(2)
        for _ in range(5):
            await page.evaluate("window.scrollBy(0, -300)")
            await asyncio.sleep(1)

        # Back to top
        await page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
        await asyncio.sleep(2)

        # Conclusion
        await speak_func(f"That concludes the automated walkthrough of ulai.in. I hope this demonstration provided a clear overview of the website's content and structure. Do you have any questions or would you like me to perform any other actions on the page?")
        await asyncio.sleep(3)

    except Exception as e:
        await speak_func(f"I encountered an error during the demo: {e}. I apologize for the interruption, but I hope this still provided a useful overview.")
        await asyncio.sleep(2)