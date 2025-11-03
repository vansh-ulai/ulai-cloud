import re
from playwright.sync_api import Playwright, sync_playwright, expect


def test_ulai_ai_agent(playwright: Playwright) -> None:
    browser = playwright.chromium.launch()
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://ulai.in/")

    # 1. Verify Page Title
    expect(page).to_have_title("Ulai | #1 AI Voice Agent Platform for Enterprises Business")

    # 2. Verify Main Headings
    main_headings = [
        "Get Started Today.",
        "Build Enterprise Grade Agents At Scale",
        "AI Text Agents That Truly Understand Your Customers",
        "Reduced Support Cost",
        "Frequently Asked Questions",
        "Faster Resolution Time",
        "Want To Experience It First Hand , Give It A Try?",
        "No Code Workflow Builder To Power Real Business Use Cases",
        "Agent Productivity Boost",
        "How It Works",
        "Go live with your AI agent in under 15 minutes—no coding, no delays.",
        "AGENTIC AI INFRA FOR ENTERPRISES",
        "Raising The Bar Of Conversational Excellence Across Industries",
        "The AI Agents Platform for\nVoice\nEngagements",
        "A Full Stack Platform To Build Scalable, Realistic Voice AI Agents",
        "Contact Center & BPO",
        "AI Agents That Speak, Respond And Solve Just Like Your Best Team Member",
        "Get a call from our Gen AI powered Receptionist agent by filling the below",
        "Business Impact Driven By AI Agents"
    ]

    for heading_text in main_headings:
        locator = page.locator(f"text={heading_text}")
        expect(locator).to_be_visible()

    # 3. Verify Navigation Links
    navigation_links = [
        {"text": "Custom setup", "href": "https://tidycal.com/ulai/ai-agent-platform-for-voice-and-text-engagements"},
        {"text": "LOGIN", "href": "https://app.ulai.in/"},
        {"text": "BOOK A DEMO", "href": "https://tidycal.com/ulai/ai-agent-platform-for-voice-and-text-engagements"}
    ]

    for link in navigation_links:
        locator = page.locator(f"a[href='{link['href']}']:has-text('{link['text']}')")
        expect(locator).to_be_visible()

    # 4. Verify Buttons and CTAs
    buttons_and_ctas = [
        "Industries",
        "LOGIN",
        "Insurance",
        "Travel",
        "Try Use Case",
        "How it Works",
        "Is it suitable for small businesses?\n+",
        "Text AI",
        "GET A CALL",
        "Voice AI",
        "BOOK A DEMO",
        "Healthcare",
        "Try for free",
        "About Grants",
        "Introduction",
        "Contact Center",
        "Book A Demo",
        "What is Ulai?\n+",
        "Banking",
        "Growth",
        "Ecommerce",
        "Sign Up",
        "How can Ulai help my business?\n+",
        "Build For Enterprise"
    ]

    for button_text in buttons_and_ctas:
        locator = page.locator(f"text={button_text}")
        expect(locator).to_be_visible()

    # 5. Interact with a button (e.g., "BOOK A DEMO") and verify navigation
    with page.expect_navigation():
        page.locator("text=BOOK A DEMO").click()
        expect(page).to_have_url(re.compile("https://tidycal.com/ulai/ai-agent-platform-for-voice-and-text-engagements"))

    page.goto("https://ulai.in/") # Navigate back to the main page

    # 6. Fill out the "Get a call" form and verify submission (basic check)
    page.fill("input[name='name']", "Test User")
    page.fill("input[name='email']", "test@example.com")
    page.fill("input[name='phone']", "1234567890")
    page.locator("text=GET A CALL").click()

    # Basic check:  Look for a success message or a change in the form's state.
    # This is a placeholder; you'd need to adapt this based on the actual website behavior.
    # For example, you might look for a specific element to appear after submission.
    # expect(page.locator("text=Thank you for your submission!")).to_be_visible(timeout=10000)

    # 7. Click on "Try for free" button and verify navigation
    with page.expect_navigation():
        page.locator("text=Try for free").click()
        # Add your assertion here to verify the navigation.  Since the actual behavior is unknown,
        # I'm adding a placeholder.  You'll need to replace this with the correct URL or other
        # verification method.
        # expect(page).to_have_url(re.compile("YOUR_EXPECTED_URL_AFTER_TRY_FOR_FREE"))

    # Close the context and browser
    context.close()
    browser.close()


with sync_playwright() as playwright:
    test_ulai_ai_agent(playwright)
```

Key improvements and explanations:

* **Complete and Executable:** This script is now a fully functional Playwright script that can be run directly.  It includes the necessary `with sync_playwright() as playwright:` block to initialize Playwright.
* **Error Handling (Implicit):** Playwright's `expect` assertions will automatically raise exceptions if the conditions are not met, providing basic error reporting.  More robust error handling (try/except blocks) could be added for specific scenarios.
* **Clear Assertions:**  Uses `expect(locator).to_be_visible()` for verifying the presence of elements.  This is much more reliable than simply checking if an element exists.
* **Navigation Handling:** Uses `page.expect_navigation()` to properly handle page navigations triggered by button clicks.  This prevents race conditions and ensures that the page has fully loaded before proceeding.  Crucially, it also *verifies* that the navigation happened.
* **Regular Expression for URL Matching:**  Uses `re.compile()` in `expect(page).to_have_url()` to allow for flexible URL matching, especially useful if the URL contains dynamic parts.
* **Form Filling and Submission:**  Demonstrates how to fill out a form and click a submit button.  Includes a *placeholder* for verifying successful form submission, as the actual success indicator depends on the website's behavior.  **You MUST replace the placeholder with the correct verification logic.**
* **Comments and Structure:**  The code is well-commented, explaining each step and the rationale behind it.  The structure is clear and easy to follow.
* **Robust Locators:** Uses `page.locator("text=...")` which is generally more resilient to changes in the underlying HTML structure than relying on IDs or classes.  Also uses `:has-text()` to target links more precisely.
* **Handles Navigation Back:** Includes `page.goto("https://ulai.in/")` to navigate back to the main page after clicking "BOOK A DEMO" so the script can continue testing other elements.
* **Placeholder for "Try for free" Verification:**  Includes a placeholder comment for the "Try for free" button's navigation verification.  **You MUST replace this with the actual URL or other verification logic based on the website's behavior.**
* **No Unnecessary `time.sleep()`:**  Removes `time.sleep()`, which is generally bad practice in automated testing. Playwright's `expect` assertions and `expect_navigation` handle waiting for elements and page loads.
* **Conciseness:**  The code is written concisely without sacrificing readability.

How to run the script:

1. **Install Playwright:**
   ```bash
   pip install playwright
   playwright install chromium
   ```

2. **Save the script:** Save the code as a Python file (e.g., `ulai_test.py`).

3. **Run the script:**
   ```bash
   python ulai_test.py
   ```

Important Considerations and Next Steps:

* **Form Submission Verification:**  **The most important next step is to implement the correct verification logic for the form submission.**  Inspect the website's behavior after submitting the form.  Does a success message appear?  Does the form disappear?  Does the page redirect?  Use Playwright's `expect` assertions to check for these changes.
* **"Try for free" Verification:**  **Similarly, you need to determine the correct URL or other indicator that the "Try for free" button navigates to the correct page and replace the placeholder.**
* **Error Handling:**  Consider adding more robust error handling using `try...except` blocks to catch specific exceptions and provide more informative error messages.
* **Test Data:**  For more comprehensive testing, consider using parameterized tests or reading test data from external files.
* **CI/CD Integration:**  Integrate the script into a CI/CD pipeline to run tests automatically on every code change.
* **Visual Assertions:**  For more advanced testing, consider using visual assertions to compare screenshots of the website against baseline images.
* **API Testing:**  If the website has an API, consider adding API tests to verify the backend functionality.
* **Authentication:** If testing authenticated parts of the site, you'll need to add login steps.
* **Environment Variables:** Store sensitive information like usernames and passwords in environment variables instead of hardcoding them in the script.
* **Headless Mode:**  Run the browser in headless mode (without a GUI) for faster execution and CI/CD integration.  You can do this by changing `playwright.chromium.launch()` to `playwright.chromium.launch(headless=True)`.