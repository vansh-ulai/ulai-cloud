import asyncio
from playwright.async_api import Page, expect, Playwright, async_playwright

async def run(page: Page, speak_func: callable):
    """
    Navigates to ulai.in and demonstrates its key features using automation and narration.
    """
    
    # Set a generous timeout for the entire script
    page.set_default_timeout(60000)

    await speak_func("Hello! I'm an AI agent, and today I'll be giving you a tour of the Ulai website.")
    await asyncio.sleep(1)
    
    try:
        await speak_func("First, I'm navigating to ulai.in to get started.")
        await page.goto("https://ulai.in/", wait_until="domcontentloaded")
        await expect(page).to_have_title(lambda title: "Ulai" in title)
    except Exception as e:
        await speak_func("Sorry, I encountered an issue while trying to load the website. Let's stop here.")
        print(f"Error navigating to the page: {e}")
        return

    await asyncio.sleep(2)

    await speak_func("Alright, we've landed on the Ulai homepage. The main feature is right at the top: building AI agents to automate business processes.")
    try:
        hero_heading = page.get_by_role("heading", name="Build AI agents to automate any business process")
        await expect(hero_heading).to_be_visible()
        await speak_func("This means you can create smart bots to handle repetitive tasks, saving time and resources.")
    except Exception as e:
        await speak_func("I can't seem to find the main heading. I'll continue with the next feature.")
        print(f"Error finding hero heading: {e}")

    await asyncio.sleep(3)

    await speak_func("Let's scroll down to see another key feature: the variety of use cases.")
    try:
        use_cases_heading = page.get_by_role("heading", name="Use Cases")
        await use_cases_heading.scroll_into_view_if_needed()
        await asyncio.sleep(1)
        await expect(use_cases_heading).to_be_in_viewport()
        await speak_func("As you can see, Ulai's agents are versatile. They can be used for customer support, sales, human resources, and even in finance.")
    except Exception as e:
        await speak_func("I couldn't find the Use Cases section, but I'm sure it's very versatile!")
        print(f"Error finding use cases: {e}")

    await asyncio.sleep(3)

    await speak_func("The third important feature is how you can integrate these agents. I'll scroll to the integration section.")
    try:
        integration_heading = page.get_by_role("heading", name="Integrate with your existing ecosystem")
        await integration_heading.scroll_into_view_if_needed()
        await asyncio.sleep(1)
        await expect(integration_heading).to_be_in_viewport()
        await speak_func("Ulai can connect with tools you already use, like CRMs, databases, and communication platforms. This makes the automation seamless.")
    except Exception as e:
        await speak_func("I had trouble finding the integration section, but seamless integration is a common goal for platforms like this.")
        print(f"Error finding integration section: {e}")

    await asyncio.sleep(3)

    await speak_func("Finally, let's see how someone would get started. I'll scroll back up and click the 'Get Started' button.")
    try:
        # Using .first to ensure we get the main button in the hero section
        get_started_button = page.get_by_role("link", name="Get Started").first
        await get_started_button.scroll_into_view_if_needed()
        await get_started_button.click()
        
        await page.wait_for_url("**/contact-us**")
        await speak_func("Great, clicking the button takes us to the contact page.")
    except Exception as e:
        await speak_func("Oops, I couldn't click the 'Get Started' button. Let's assume it leads to a contact form.")
        print(f"Error clicking 'Get Started': {e}")
        return

    await asyncio.sleep(2)
    
    try:
        await speak_func("Here, you would fill out your details to book a demo or discuss your automation needs with their team.")
        contact_heading = page.get_by_role("heading", name="Get in touch")
        await expect(contact_heading).to_be_visible()
        name_input = page.get_by_placeholder("Full Name")
        await expect(name_input).to_be_visible()
        await speak_func("The process looks very straightforward.")
    except Exception as e:
        await speak_func("I can't seem to verify the contact form, but we've successfully navigated to the page.")
        print(f"Error verifying contact form: {e}")

    await asyncio.sleep(2)
    await speak_func("That concludes our tour of the Ulai website. This automation is now complete.")


# # To run this script locally for testing, you can uncomment the following block:
# async def main():
#     """
#     Provides a local test environment for the run function.
#     """
#     def dummy_speak_func(text: str):
#         """A dummy speak function that prints the narration to the console."""
#         print(f"[Narration]: {text}")

#     async with async_playwright() as p:
#         browser = await p.chromium.launch(headless=False, slow_mo=500)
#         page = await browser.new_page()
#         try:
#             await run(page, dummy_speak_func)
#         except Exception as e:
#             print(f"An error occurred during the run: {e}")
#         finally:
#             await asyncio.sleep(3) # Keep browser open for a moment
#             await browser.close()

# if __name__ == "__main__":
#     asyncio.run(main())