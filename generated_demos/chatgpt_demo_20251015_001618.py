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
        
        await speak_func("Starting demo. I'm going to showcase ChatGPT, a powerful tool for getting answers, finding inspiration, and boosting your productivity.")

        # Initial view - Main Heading
        await speak_func("The main heading asks 'What can I help with?'. This highlights the core functionality of ChatGPT - it's a versatile assistant ready to assist with a variety of tasks.")

        # Scrolling to show more content
        await scroll_to_section(page, "Temporary Chat")
        await speak_func("Scrolling down to reveal further options.  We see the website utilizes cookies which are important for user preferences and general functionality. There's also temporary chat functionality.")

        # Click on 'Terms'
        await speak_func("Now, let's explore the website's legal information. I'm going to click on 'Terms'.")
        await smooth_mouse_move(page, 100, 100, 670, 752)
        await page.mouse.click(670, 752)

        page = await close_extra_tabs(page)
        await speak_func("We opened the Terms page in a new tab and now closed it. It's crucial to understand the terms of service before using any online platform.")

        # Click on 'Privacy Policy'
        await speak_func("Let's check the privacy policy to understand how user data is handled. Clicking on 'Privacy Policy'.")
        await smooth_mouse_move(page, 100, 100, 849, 752)
        await page.mouse.click(849, 752)
        page = await close_extra_tabs(page)
        await speak_func("We quickly reviewed and then closed the 'Privacy Policy'. Understanding privacy is critical.")

        # Click on 'Sign up for free'
        await speak_func("Finally, I'll click on 'Sign up for free' to demonstrate the account creation process. Note that clicking on this will take you to the signup flow.")
        await smooth_mouse_move(page, 100, 100, 1326, 26)
        await page.mouse.click(1326, 26)
        page = await close_extra_tabs(page)
        await speak_func("Demo complete. The key takeaway from this website is its easy to use interface for accessing a powerful AI assistant. The meta description also suggests that ChatGPT can help with writing, learning, and brainstorming.")
        
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False