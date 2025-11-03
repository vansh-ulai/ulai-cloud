import asyncio
import random
from playwright.async_api import Page

async def smooth_mouse_move(page, start_x, start_y, end_x, end_y):
    '''Move mouse smoothly in small steps for human-like movement'''
    steps = max(abs(end_x - start_x), abs(end_y - start_y)) // 10
    steps = max(steps, 5)
    
    for i in range(steps):
        x = start_x + (end_x - start_x) * (i / steps)
        y = start_y + (end_y - start_y) * (i / steps)
        await page.mouse.move(x, y)
        await asyncio.sleep(random.uniform(0.01, 0.05))
    
    await page.mouse.move(end_x, end_y)
    await asyncio.sleep(random.uniform(0.1, 0.3))

async def close_extra_tabs(page):
    '''Close any new tabs and return to main page'''
    context = page.context
    pages = context.pages
    if len(pages) > 1:
        for p in pages[1:]:
            await p.close()
        return pages[0]
    return page

async def scroll_to_section(page, section_name):
    '''Scroll down to see more content'''
    await page.evaluate("window.scrollBy(0, window.innerHeight * 0.6)")
    await asyncio.sleep(0.8)

async def run(page, speak_func):
    '''Main demo - show website features with smooth interaction'''
    try:
        # Fullscreen
        await page.evaluate("document.documentElement.requestFullscreen().catch(()=>{})")

        await asyncio.sleep(0.5)
        
        # START YOUR DEMO HERE
        # 1. Introduce the website
        # 2. Show sections by scrolling
        # 3. Click 3-5 key buttons with smooth mouse movement
        # 4. Close any new tabs that open
        # 5. Narrate features, not just text
        # 6. Return to main page at end
        
        await speak_func("Starting demo of Ulai, the AI voice agent platform for enterprises. Ulai helps automate lead generation, appointment bookings, customer support, and more, using natural-sounding AI.")

        await asyncio.sleep(1)
        
        await speak_func("Let's take a look at some of the features.  First, we'll scroll down to the 'How It Works' section to see how easy it is to get started.")
        await scroll_to_section(page, "How It Works")

        await asyncio.sleep(1.5)
        await speak_func("Ulai empowers you to build, test, deploy, and monitor intelligent voice agents with ease and precision. It highlights the intuitive voice API.")

        await asyncio.sleep(1.5)

        await speak_func("Now, let's scroll down to see the 'Enterprise' section, showcasing enterprise-grade agents built to scale.")
        await scroll_to_section(page, "Enterprise")
        await asyncio.sleep(1)

        await speak_func("Here we see enterprise-level features like end-to-end encryption, AICPA SOC II compliance, GDPR compliance, zero retention for TTS API, dedicated support, and more, making it a secure and reliable platform for businesses.")
        await asyncio.sleep(2)
        
        await speak_func("Let's click on the 'BOOK A DEMO' button to see how easy it is to schedule a personalized demo.")
        await smooth_mouse_move(page, 1160, 76, 1160, 76)
        await page.mouse.click(1160, 76)
        await asyncio.sleep(1)

        page = await close_extra_tabs(page)
        await speak_func("The 'BOOK A DEMO' button navigates directly within the page. Let me click it again")
        await smooth_mouse_move(page, 1160, 76, 1160, 76)
        await page.mouse.click(1160, 76)
        await asyncio.sleep(1)
        

        await speak_func("I'll now scroll down to the footer and click on the 'GET A CALL' button.")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)") #scroll to bottom
        await asyncio.sleep(1)

        await smooth_mouse_move(page, 400, 2293, 400, 2293)
        await speak_func("Clicking the 'GET A CALL' button.")
        await page.mouse.click(400, 2293)
        await asyncio.sleep(2)
        page = await close_extra_tabs(page)

        await speak_func("That completes the demo of Ulai.  We've seen how easy it is to automate voice interactions and provide enterprise-grade security and support.")
        
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False