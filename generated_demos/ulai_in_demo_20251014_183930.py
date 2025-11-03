import asyncio
from playwright.async_api import Page, TimeoutError, expect

async def run(page: Page, speak_func: callable):
    """
    Navigates to ulai.in and provides a narrated tour of its main features.
    """
    
    async def highlight_and_speak(selector: str, text: str, by_role=None, name=None):
        """Helper function to scroll to, highlight, and speak about an element."""
        try:
            if by_role and name:
                element = page.get_by_role(by_role, name=name).first
            else:
                element = page.locator(selector).first
            
            await element.scroll_into_view_if_needed()
            await asyncio.sleep(0.5)
            # Add a temporary border to highlight the element
            await element.evaluate("element => { element.style.border = '3px solid red'; element.style.transition = 'border 0.5s'; }")
            speak_func(text)
            await asyncio.sleep(2) # Keep highlight while speaking
            await element.evaluate("element => { element.style.border = ''; }")
            await asyncio.sleep(1)
        except TimeoutError:
            speak_func(f"Sorry, I couldn't find the section I was looking for: {text.split('.')[0]}")
        except Exception as e:
            speak_func(f"An unexpected error occurred while highlighting a feature. {e}")

    speak_func("Hello! Let's take a quick tour of the Ulai AI Agent platform.")
    await asyncio.sleep(1)

    try:
        speak_func("First, I'll navigate to their website at ulai.in.")
        await page.goto("https://ulai.in/", timeout=60000, wait_until="domcontentloaded")
        await expect(page.get_by_role("heading", name="Build your AI Agent")).to_be_visible(timeout=15000)
        speak_func("Great, the page has loaded successfully.")
    except TimeoutError:
        speak_func("I'm sorry, the Ulai website seems to be taking too long to load. Please try again later.")
        return
    except Exception as e:
        speak_func(f"An error occurred while trying to load the page: {e}")
        return

    await asyncio.sleep(2)

    # Feature 1: Build your AI Agent
    await highlight_and_speak(
        selector=None,
        by_role="heading",
        name="Build your AI Agent",
        text="Ulai's core feature is allowing you to build custom AI agents. These agents are designed to handle complex conversations and automate tasks, acting as a true digital team member."
    )

    # Feature 2: Train on your knowledge
    await highlight_and_speak(
        selector=None,
        by_role="heading",
        name="Train on your knowledge",
        text="You can train the agent on your own specific knowledge base. This means it can provide accurate, context-aware answers using your company's documents, websites, and internal data."
    )

    # Feature 3: Integrate with your tools
    await highlight_and_speak(
        selector=None,
        by_role="heading",
        name="Integrate with your tools",
        text="A key strength is its ability to seamlessly integrate with tools you already use, like Zendesk, Salesforce, and HubSpot. This allows the agent to perform actions and not just answer questions."
    )
    
    # Feature 4: Deploy Everywhere
    await highlight_and_speak(
        selector=None,
        by_role="heading",
        name="Deploy everywhere",
        text="Finally, you can deploy your finished agent across various channels to meet your customers where they are, whether that's on your website chat, Slack, or even WhatsApp."
    )

    try:
        speak_func("They make it easy to get started. I'll find the 'Book a Demo' button in the main navigation.")
        book_demo_button = page.get_by_role("link", name="Book a demo").first
        await book_demo_button.scroll_into_view_if_needed()
        await book_demo_button.hover()
        await asyncio.sleep(1)
        speak_func("Here it is. Clicking this would start the process of scheduling a demonstration.")
    except TimeoutError:
        speak_func("I couldn't find the 'Book a Demo' button, but it's usually at the top right.")
    except Exception as e:
        speak_func(f"Something went wrong when I tried to find the demo button. {e}")

    await asyncio.sleep(2)
    speak_func("That concludes our quick tour of the Ulai AI Agent platform. It seems like a very capable and flexible solution for business automation.")