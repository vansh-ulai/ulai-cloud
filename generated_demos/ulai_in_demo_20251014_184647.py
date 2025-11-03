import asyncio
from playwright.async_api import Page

async def run(page: Page, speak_func):
    try:
        # Introduction
        await speak_func("Hello! I'm going to demonstrate the Ulai AI Agent website, ulai.in. This is an automated walkthrough.")
        await asyncio.sleep(2)

        # Navigate
        await speak_func("Let me navigate to the homepage now.")
        await page.goto("https://ulai.in/", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)

        # Explore header
        await speak_func("The page has loaded. I can see the main navigation at the top, including the Ulai logo and navigation links.")
        await asyncio.sleep(2)

        # Scroll section 1
        await speak_func("Let me scroll down to show you the first main section, which highlights the core value proposition of Ulai.")
        await page.evaluate("window.scrollBy(0, 400)")
        await asyncio.sleep(2)

        await speak_func("This section appears to focus on the benefits of using Ulai, such as increased efficiency and productivity.")
        await asyncio.sleep(3)

        # Scroll section 2
        await speak_func("Now, let's move on to the next section, which likely details specific features or use cases.")
        await page.evaluate("window.scrollBy(0, 400)")
        await asyncio.sleep(2)
        await speak_func("Here, we can see more information about how Ulai can be applied to different tasks and workflows.")
        await asyncio.sleep(3)

        # Scroll section 3
        await speak_func("Let's scroll down further to see if there are any testimonials or case studies.")
        await page.evaluate("window.scrollBy(0, 400)")
        await asyncio.sleep(2)
        await speak_func("This section showcases real-world examples of how Ulai has helped other users or organizations.")
        await asyncio.sleep(3)

        # Scroll section 4
        await speak_func("And now the next section, which might focus on pricing or getting started.")
        await page.evaluate("window.scrollBy(0, 400)")
        await asyncio.sleep(2)
        await speak_func("Here we can see information about the different plans and how to get started.")
        await asyncio.sleep(3)

        # Scroll through page
        await speak_func("Now, I'll slowly scroll through the rest of the page to give you a better sense of the overall layout and content.")
        await asyncio.sleep(2)
        for _ in range(5):
            await page.evaluate("window.scrollBy(0, 300)")
            await asyncio.sleep(2)

        # Scroll to footer
        await speak_func("Finally, let me show you the footer section.")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(3)

        await speak_func("The footer contains important links like terms of service, privacy policy, and contact information.")
        await asyncio.sleep(2)

        # Back to top
        await speak_func("I'll scroll back to the top of the page now.")
        await page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
        await asyncio.sleep(2)

        # Conclusion
        await speak_func("That completes the walkthrough of ulai.in. This website showcases the Ulai AI Agent and its capabilities. Do you have any questions or would you like me to explore a specific section in more detail?")
        await asyncio.sleep(3)

    except Exception as e:
        await speak_func(f"I encountered an error during the demo: {e}. However, I hope this gave you a good overview of the website.")
        await asyncio.sleep(2)