# Description: This script automates interactions with the Ulai AI Agent website (https://ulai.in/).
# It demonstrates key functionalities such as navigating the site, filling out a form,
# and exploring different sections.

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Configure Chrome options for headless browsing (optional)
chrome_options = Options()
# chrome_options.add_argument("--headless")  # Uncomment for headless mode
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")

# Initialize the Chrome driver
driver = webdriver.Chrome(options=chrome_options)

# 1. Navigate to the Ulai website
url = "https://ulai.in/"
driver.get(url)
print(f"Navigated to: {url}")
print(f"Page title: {driver.title}")

# 2. Verify the page title
assert "Ulai | #1 AI Voice Agent Platform for Enterprises Business" in driver.title, "Title verification failed!"

# 3. Click the "Book A Demo" button (using multiple methods for demonstration)
try:
    # Method 1: By text content (more robust)
    book_demo_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//a[text()='BOOK A DEMO']"))
    )
    book_demo_button.click()
    print("Clicked 'BOOK A DEMO' button (Method 1)")
    driver.back() # Go back to the main page
    time.sleep(2)

except Exception as e:
    print(f"Error clicking 'BOOK A DEMO' button (Method 1): {e}")

# 4. Find and click the "Industries" button, then navigate back
try:
    industries_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[text()='Industries']"))
    )
    industries_button.click()
    print("Clicked 'Industries' button.")
    driver.back()
    time.sleep(2)

except Exception as e:
    print(f"Error clicking 'Industries' button: {e}")

# 5. Locate and interact with the "Get a call from our Gen AI powered Receptionist agent by filling the below" form.
try:
    # Locate the form elements
    name_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "name"))
    )
    email_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "email"))
    )
    phone_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "phone"))
    )

    # Fill out the form
    name_field.send_keys("Test User")
    email_field.send_keys("test@example.com")
    phone_field.send_keys("1234567890")

    # Locate and click the "GET A CALL" button
    get_a_call_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[text()='GET A CALL']"))
    )
    get_a_call_button.click()
    print("Filled out the form and clicked 'GET A CALL' button.")

    # Wait for a potential success message or page change (adjust time as needed)
    time.sleep(5)  # Wait for 5 seconds

except Exception as e:
    print(f"Error interacting with the form: {e}")

# 6. Explore the "Frequently Asked Questions" section (click the first question)
try:
    faq_question = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'What is Ulai?')]"))
    )
    faq_question.click()
    print("Clicked the first FAQ question.")
    time.sleep(2)

    # Click it again to close it
    faq_question.click()
    print("Clicked the first FAQ question again to close it.")
    time.sleep(2)

except Exception as e:
    print(f"Error interacting with FAQ section: {e}")

# 7. Navigate to the Login page
try:
    login_link = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//a[text()='LOGIN']"))
    )
    login_link.click()
    print("Clicked the LOGIN link.")
    time.sleep(3) # Wait for the login page to load
    driver.back() # Go back to the main page
    time.sleep(2)

except Exception as e:
    print(f"Error navigating to the Login page: {e}")

# 8. Scroll to the bottom of the page
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
print("Scrolled to the bottom of the page.")
time.sleep(2)

# 9. Scroll back to the top of the page
driver.execute_script("window.scrollTo(0, 0);")
print("Scrolled back to the top of the page.")
time.sleep(2)

# 10. Close the browser
driver.quit()
print("Browser closed.")