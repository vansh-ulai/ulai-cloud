import pytest
from playwright.sync_api import Page, expect

URL = "https://ulai.in/"


@pytest.fixture(scope="function", autouse=True)
def setup(page: Page):
    page.goto(URL)
    yield


def test_ulai_website_title(page: Page):
    """
    Test case to verify the title of the Ulai website.
    """
    expect(page).to_have_title("Ulai | #1 AI Voice Agent Platform for Enterprises Business")


def test_ulai_navigation_links(page: Page):
    """
    Test case to verify the presence and functionality of navigation links.
    """
    # Verify "Custom setup" link
    custom_setup_link = page.locator("text=Custom setup")
    expect(custom_setup_link).to_have_attribute("href", "https://tidycal.com/ulai/ai-agent-platform-for-voice-and-text-engagements")

    # Verify "LOGIN" link
    login_link = page.locator("text=LOGIN")
    expect(login_link).to_have_attribute("href", "https://app.ulai.in/")

    # Verify "BOOK A DEMO" link
    book_a_demo_link = page.locator("text=BOOK A DEMO")
    expect(book_a_demo_link).to_have_attribute("href", "https://tidycal.com/ulai/ai-agent-platform-for-voice-and-text-engagements")


def test_ulai_main_headings(page: Page):
    """
    Test case to verify the presence of main headings on the page.
    """
    main_headings = [
        "AGENTIC AI INFRA FOR ENTERPRISES",
        "AI Text Agents That Truly Understand Your Customers",
        "Contact Center & BPO",
        "Get a call from our Gen AI powered Receptionist agent by filling the below",
        "Business Impact Driven By AI Agents",
        "How It Works",
        "Reduced Support Cost",
        "Build Enterprise Grade Agents At Scale",
        "Faster Resolution Time",
        "Get Started Today.",
        "AI Agents That Speak, Respond And Solve Just Like Your Best Team Member",
        "Want To Experience It First Hand , Give It A Try?",
        "Go live with your AI agent in under 15 minutes—no coding, no delays.",
        "A Full Stack Platform To Build Scalable, Realistic Voice AI Agents",
        "Frequently Asked Questions",
        "The AI Agents Platform for\nVoice\nEngagements",
        "No Code Workflow Builder To Power Real Business Use Cases",
        "Agent Productivity Boost",
        "Raising The Bar Of Conversational Excellence Across Industries"
    ]

    for heading_text in main_headings:
        heading_locator = page.locator(f"text={heading_text}")
        expect(heading_locator).to_be_visible()


def test_ulai_buttons_and_ctas(page: Page):
    """
    Test case to verify the presence and clickability of buttons and CTAs.
    """
    buttons_and_ctas = [
        "What is Ulai?\n+",
        "Voice AI",
        "Text AI",
        "Try Use Case",
        "Ecommerce",
        "Banking",
        "Contact Center",
        "Sign Up",
        "How can Ulai help my business?\n+",
        "Travel",
        "Industries",
        "Book A Demo",
        "About Grants",
        "GET A CALL",
        "BOOK A DEMO",
        "Healthcare",
        "Try for free",
        "How it Works",
        "Introduction",
        "Insurance",
        "Growth",
        "LOGIN",
        "Build For Enterprise",
        "Is it suitable for small businesses?\n+"
    ]

    for button_text in buttons_and_ctas:
        button_locator = page.locator(f"text={button_text}")
        expect(button_locator).to_be_visible()
        # Optional: Uncomment the line below to test clickability (may cause navigation)
        # button_locator.click()


def test_ulai_get_a_call_form(page: Page):
    """
    Test case to fill and submit the "Get a call" form.
    """
    page.fill("input[name='your-name']", "Test User")
    page.fill("input[name='your-email']", "test@example.com")
    page.fill("input[name='your-phone']", "1234567890")
    page.click("text=GET A CALL")

    # Add an assertion to check for a success message or form submission confirmation.
    # This will depend on how the website handles form submissions.
    # Example:
    # expect(page.locator("text=Thank you for your submission!")).to_be_visible()
    # or
    # expect(page).to_have_url("https://ulai.in/thank-you") # Replace with the actual URL after submission


def test_ulai_book_a_demo_button_navigation(page: Page):
    """
    Test case to verify the navigation when clicking the "Book A Demo" button.
    """
    with page.expect_navigation() as navigation_info:
        page.click("text=BOOK A DEMO")

    # Verify that the navigation went to the expected URL.
    expect(page).to_have_url("https://tidycal.com/ulai/ai-agent-platform-for-voice-and-text-engagements")