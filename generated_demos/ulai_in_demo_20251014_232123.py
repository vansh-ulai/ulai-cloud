import re
from playwright.sync_api import Playwright, sync_playwright, expect


def test_ulai_ai_agent_website(playwright: Playwright) -> None:
    browser = playwright.chromium.launch()
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://ulai.in/")

    # 1. Verify Page Title
    expect(page).to_have_title("Ulai | #1 AI Voice Agent Platform for Enterprises Business")

    # 2. Verify Main Headings
    main_headings = [
        "No Code Workflow Builder To Power Real Business Use Cases",
        "Reduced Support Cost",
        "The AI Agents Platform for\nVoice\nEngagements",
        "Raising The Bar Of Conversational Excellence Across Industries",
        "AI Text Agents That Truly Understand Your Customers",
        "A Full Stack Platform To Build Scalable, Realistic Voice AI Agents",
        "Get Started Today.",
        "Get a call from our Gen AI powered Receptionist agent by filling the below",
        "AI Agents That Speak, Respond And Solve Just Like Your Best Team Member",
        "Business Impact Driven By AI Agents",
        "Contact Center & BPO",
        "Build Enterprise Grade Agents At Scale",
        "Go live with your AI agent in under 15 minutes—no coding, no delays.",
        "How It Works",
        "Agent Productivity Boost",
        "Faster Resolution Time",
        "Frequently Asked Questions",
        "AGENTIC AI INFRA FOR ENTERPRISES",
        "Want To Experience It First Hand , Give It A Try?"
    ]

    for heading_text in main_headings:
        locator = page.locator("h1, h2, h3, h4, h5, h6", has_text=heading_text)
        expect(locator).to_be_visible()

    # 3. Verify Navigation Links
    navigation_links = [
        {"text": "Custom setup", "href": "https://tidycal.com/ulai/ai-agent-platform-for-voice-and-text-engagements"},
        {"text": "LOGIN", "href": "https://app.ulai.in/"},
        {"text": "BOOK A DEMO", "href": "https://tidycal.com/ulai/ai-agent-platform-for-voice-and-text-engagements"}
    ]

    for link in navigation_links:
        locator = page.locator(f"a[href='{link['href']}']", has_text=link['text'])
        expect(locator).to_be_visible()

    # 4. Verify Buttons and CTAs
    buttons_and_ctas = [
        "GET A CALL",
        "Is it suitable for small businesses?\n+",
        "Growth",
        "Try for free",
        "What is Ulai?\n+",
        "BOOK A DEMO",
        "Introduction",
        "Build For Enterprise",
        "Text AI",
        "Insurance",
        "LOGIN",
        "Book A Demo",
        "Sign Up",
        "How it Works",
        "Contact Center",
        "Try Use Case",
        "Travel",
        "Ecommerce",
        "Voice AI",
        "About Grants",
        "Banking",
        "Healthcare",
        "How can Ulai help my business?\n+",
        "Industries"
    ]

    for button_text in buttons_and_ctas:
        locator = page.locator("button, a", has_text=re.compile(button_text, re.IGNORECASE))
        expect(locator).to_be_visible()

    # 5. Interact with a form (Get a call)
    page.fill("input[name='name']", "Test User")
    page.fill("input[name='email']", "test@example.com")
    page.fill("input[name='phone']", "1234567890")
    page.click("text=GET A CALL")

    # 6. Verify a successful form submission (check for a success message or redirect)
    #   Since we don't know the exact success behavior, we'll check for a generic change.
    #   This is a placeholder and needs to be adapted based on the actual website behavior.
    #   For example, check for a specific success message element.
    #   expect(page.locator("text=Thank you for your submission!")).to_be_visible() # Example

    # 7. Click on the "How it Works" link and verify the URL
    page.locator("text=How it Works").click()
    expect(page).to_have_url("https://ulai.in/#how-it-works")

    # 8. Click on the "Book a Demo" button and verify the URL
    page.locator("text=Book A Demo").first.click()
    expect(page).to_have_url("https://tidycal.com/ulai/ai-agent-platform-for-voice-and-text-engagements")

    # Close the browser context
    context.close()
    browser.close()


with sync_playwright() as playwright:
    test_ulai_ai_agent_website(playwright)