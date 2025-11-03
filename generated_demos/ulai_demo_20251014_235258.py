import asyncio
import random
from playwright.sync_api import Page

async def human_like_click(page: Page, selector: str, speak_func):
    """
    Clicks an element with a bit of human-like delay.
    """
    try:
        speak_func(f"Clicking on {selector}")
        await asyncio.sleep(random.uniform(0.2, 0.5))  # Simulate human delay
        await page.locator(selector).first.click()
    except Exception as e:
        speak_func(f"Could not click on {selector}: {e}")

async def scroll_and_reveal(page: Page, speak_func):
    """
    Scrolls through the entire page, revealing content as it goes.
    """
    speak_func("Scrolling through the page to reveal all content.")
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await asyncio.sleep(1)  # Give it time to load
    await page.evaluate("window.scrollTo(0, 0)")
    await asyncio.sleep(1)

async def handle_new_pages(page: Page, speak_func):
    """
    Handles new pages that open in a new tab. Closes the new tab and returns to the original page.
    """
    speak_func("Checking for new pages opening in new tabs.")
    pages = page.context.pages
    if len(pages) > 1:
        new_page = pages[-1]
        speak_func(f"New page detected: {new_page.url}")
        await new_page.close()
        speak_func("New page closed. Returning to the main page.")

async def run(page: Page, speak_func):
    """
    This function contains the main demo script for the Ulai website.
    """

    speak_func("Starting the Ulai AI Voice Agent Platform demo.")
    speak_func("Navigating to https://ulai.in/")
    await page.goto("https://ulai.in/")

    speak_func("Waiting for the page to load completely.")
    await page.wait_for_load_state("networkidle")

    speak_func("The page title is: Ulai | #1 AI Voice Agent Platform for Enterprises Business")
    speak_func("The page description is: Automate lead generation, appointment bookings, reminders, and customer support with natural sounding AI voice agents. Multilingual, human like, and always on, Ulai helps you engage every customer, at every touchpoint.")

    # Hero Section Narration
    speak_func("Now exploring the hero section of the page.")
    speak_func("The main heading is: Go live with your AI agent in under 15 minutes—no coding, no delays.")
    speak_func("We can see text highlighting that Ulai deploys hyper personalized AI agents that answer, sell, and support across phone, WhatsApp, and web. It's purpose built to reduce support load and increase revenue.")
    speak_func("Also, Ulai is described as a full-stack platform to build and deploy intelligent voice and text agents with real-time control, analytics, and enterprise-grade performance.")

    # Buttons in Hero section
    speak_func("Let's explore some of the buttons in the hero section.")
    await human_like_click(page, "text=Book A Demo", speak_func)
    await handle_new_pages(page, speak_func)
    await page.go_back()

    speak_func("Scrolling down to view more features.")
    await scroll_and_reveal(page, speak_func)

    speak_func("Now exploring the 'How It Works' section.")
    speak_func("This section likely explains how the platform functions and helps users.")

    speak_func("Let's examine the navigation bar.")
    speak_func("We can see 'Custom Setup', 'LOGIN', 'BOOK A DEMO', and 'Try for free' options.")

    #Interacting with "Industries"
    speak_func("Clicking on 'Industries' to explore different use cases.")
    await human_like_click(page, "text=Industries", speak_func)
    await handle_new_pages(page, speak_func)

    # Going back to the main page
    await page.go_back()
    speak_func("Returning to the main page.")
    await page.wait_for_load_state("networkidle")

    #Visiting the Login page
    speak_func("Now, let's navigate to the Login page to see the login form.")
    await human_like_click(page, "text=LOGIN", speak_func)
    await page.wait_for_load_state("networkidle")

    speak_func("We are now on the Login page.")
    speak_func("This page has fields for entering login credentials and buttons to 'Login' or 'Sign Up'.")
    speak_func("There are also links to 'Privacy policy' and 'Terms of use'.")

    speak_func("Going back to the Ulai main page")
    await page.go_back()
    await page.wait_for_load_state("networkidle")

    speak_func("Visiting the Sign Up page")
    speak_func("Let's try to sign up by clicking the 'Try for free' button.")
    await human_like_click(page, "text=Try for free", speak_func)
    await page.wait_for_load_state("networkidle")

    speak_func("We are now on the Sign Up page.")
    speak_func("Here, you can create an account to get started with the Voice Dashboard.")
    speak_func("It also has a link to 'Sign in' if you already have an account.")

    # Filling in the form and submitting (example, but won't actually submit)
    speak_func("Filling in example details for signing up.  I am not actually submitting.")
    try:
        await page.locator('input[name="firstName"]').first.fill("Demo")
        await page.locator('input[name="lastName"]').first.fill("User")
        await page.locator('input[name="email"]').first.fill("demo@example.com")
        await page.locator('input[name="password"]').first.fill("P@sswOrd123")
        speak_func("Example details filled, but form is not actually being submitted.")
    except Exception as e:
        speak_func(f"Could not interact with signup form: {e}")

    # Final step
    speak_func("This concludes the basic Ulai platform demo.")
    speak_func("The demo covered the main landing page, navigation, exploring the 'Industries', 'Login' and 'Sign Up' pages.")

    return True