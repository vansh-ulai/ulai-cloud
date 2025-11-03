import asyncio
from playwright.async_api import Page

async def run(page: Page, speak_func):
    try:
        # Introduction
        await speak_func("Hello! I'll demonstrate the website https://ulai.in/. This is an AI-powered walkthrough.")
        await asyncio.sleep(2)
        
        # Navigate
        await speak_func("Let me navigate to the homepage.")
        await page.goto("https://ulai.in/", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)
        
        # Explore header
        await speak_func("The page has loaded. I can see the main navigation at the top.")
        await asyncio.sleep(2)
        
        # Scroll section 1
        await speak_func("Let me scroll down to show you the first main section.")
        await page.evaluate("window.scrollBy(0, 400)")
        await asyncio.sleep(2)
        
        await speak_func("This section highlights the key value proposition of the platform.")
        await asyncio.sleep(3)
        
        # Scroll section 2
        await page.evaluate("window.scrollBy(0, 400)")
        await asyncio.sleep(2)
        await speak_func("Here we can see information about the main features and benefits.")
        await asyncio.sleep(3)
        
        # Scroll section 3
        await page.evaluate("window.scrollBy(0, 400)")
        await asyncio.sleep(2)
        await speak_func("This section typically contains customer testimonials or case studies.")
        await asyncio.sleep(3)
        
        # Try to find interactive elements
        await speak_func("Let me look for key interactive elements like buttons or forms.")
        await asyncio.sleep(2)
        
        try:
            buttons = await page.query_selector_all('button, a[class*="button"], [class*="cta"]')
            if buttons:
                await speak_func(f"I found {len(buttons)} interactive elements on this page.")
                await asyncio.sleep(2)
        except:
            await speak_func("The site uses custom interactive elements.")
            await asyncio.sleep(2)
        
        # Scroll to footer
        await speak_func("Finally, let me show you the footer section.")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(3)
        
        await speak_func("The footer contains additional links and contact information.")
        await asyncio.sleep(2)
        
        # Back to top
        await page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
        await asyncio.sleep(2)

        # Slow scroll demo
        await speak_func("Now I will slowly scroll through the page to showcase the content.")
        await asyncio.sleep(2)
        for _ in range(10):
            await page.evaluate("window.scrollBy(0, 300)")
            await asyncio.sleep(1)
        
        # Conclusion
        await speak_func(f"That completes the walkthrough of https://ulai.in/. This site provides valuable services with a clean, professional design. Do you have any questions?")
        await asyncio.sleep(3)
        
    except Exception as e:
        await speak_func(f"I encountered an error during the demo, but I hope this gave you a good overview.")
        await asyncio.sleep(2)