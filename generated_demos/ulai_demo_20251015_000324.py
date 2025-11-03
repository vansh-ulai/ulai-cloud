import asyncio
import random
from playwright.async_api import Page

async def human_like_click(page: Page, x: int, y: int, desc: str):
    """Performs a human-like click with mouse movement and slight delays."""
    await page.mouse.move(x, y, steps=10)
    await asyncio.sleep(random.uniform(0.1, 0.3))
    await page.mouse.click(x, y)
    await asyncio.sleep(random.uniform(0.3, 0.7))
    print(f"Clicked: {desc} at ({x}, {y})")  # Debugging


async def scroll_and_reveal(page: Page, y_offset: int):
    """Scrolls the page to reveal content."""
    print(f"Scrolling to y_offset: {y_offset}")  # Debugging
    await page.evaluate(f"window.scrollTo(0, {y_offset})")
    await asyncio.sleep(1)

async def handle_new_pages(page: Page):
  """Closes any new tabs that open during the demo."""
  await asyncio.sleep(2)  #Allow time for potential new pages to open

  new_pages = page.context.pages
  if len(new_pages) > 1:
      for p in new_pages:
          if p != page:
              await p.close()
              print("Closed a new tab.") #Debugging

async def run(page: Page, speak_func):
    """Automated demo script for ulai.in."""

    await speak_func("Starting the Ulai demo. We'll explore key features and sections of the website.")

    # 1. Navigate to the "Book A Demo" button in the header and click.
    book_demo_x = 1160
    book_demo_y = 76
    await speak_func("Navigating to the 'Book a Demo' button in the header.")
    await human_like_click(page, book_demo_x, book_demo_y, "Book a Demo (Header)")
    await speak_func("Clicked 'Book a Demo'. This should bring us to the contact form.")

    # 2. Scroll to the form at Y:1874 and fill out the name input box
    await scroll_and_reveal(page, 1874)
    await speak_func("Scrolling to the contact form to demonstrate lead capture.")
    await page.locator('input[name="name"]').fill("Demo User")
    await speak_func("Entering 'Demo User' into the name field.")

    # 3. Fill out the email field
    await page.locator('input[name="email"]').fill("demo@example.com")
    await speak_func("Entering 'demo@example.com' into the email field.")

    # 4. Fill out the phone number field.
    await page.locator('input[name="phoneNumber"]').fill("555-123-4567")
    await speak_func("Entering '555-123-4567' into the phone number field.")

    # 5. Scroll to the "Try for free" button
    try_free_x = 712
    try_free_y = 579
    await speak_func("Scrolling to the 'Try for free' button in the hero section.")
    await scroll_and_reveal(page, 400)
    await asyncio.sleep(1) # give the page a second to scroll
    await human_like_click(page, try_free_x, try_free_y, "Try for free")
    await speak_func("Clicking 'Try for free'.")

    await handle_new_pages(page)

    # 6. Scroll to the FAQ section and select one of the questions.

    await scroll_and_reveal(page, 9301)
    await speak_func("Scrolling to the Frequently Asked Questions section.")
    faq_x = 969
    faq_y = 9301
    await human_like_click(page, faq_x, faq_y, "Is it suitable for small businesses? +")
    await speak_func("Clicking the question: 'Is it suitable for small businesses?'.")
    await asyncio.sleep(1)

    #7 Navigate back to the top, log in
    await scroll_and_reveal(page, 0)
    login_x = 1046
    login_y = 76
    await speak_func("Navigate back to top, log in")
    await human_like_click(page, login_x, login_y, "LOGIN")
    await speak_func("Clicking Login.")

    await handle_new_pages(page)

    await speak_func("The demo is complete. We showcased lead capture, free trial access, and FAQ interaction.")
    return True