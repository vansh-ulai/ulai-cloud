# Description: This script automates interactions with the Ulai AI Agent website (https://ulai.in/).
# It demonstrates navigation, form filling, and interaction with key elements.

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
chrome_options.add_argument("--window-size=1920x1080")

# Initialize the Chrome driver
driver = webdriver.Chrome(options=chrome_options)

# 1. Navigate to the Ulai website
driver.get("https://ulai.in/")
print(f"Navigated to: {driver.current_url}")
print(f"Page title: {driver.title}")

# 2. Click the "BOOK A DEMO" button (using multiple methods for robustness)
try:
    # Method 1: By text content
    book_a_demo_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//a[text()='BOOK A DEMO']"))
    )
    book_a_demo_button.click()
    print("Clicked 'BOOK A DEMO' button (Method 1)")
except Exception as e:
    print(f"Error clicking 'BOOK A DEMO' button (Method 1): {e}")
    try:
        # Method 2: By link href
        book_a_demo_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@href='https://tidycal.com/ulai/ai-agent-platform-for-voice-and-text-engagements']"))
        )
        book_a_demo_button.click()
        print("Clicked 'BOOK A DEMO' button (Method 2)")
    except Exception as e:
        print(f"Error clicking 'BOOK A DEMO' button (Method 2): {e}")
        try:
            # Method 3: By partial text and tag
            book_a_demo_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'BOOK A DEMO')]"))
            )
            book_a_demo_button.click()
            print("Clicked 'BOOK A DEMO' button (Method 3)")

        except Exception as e:
            print(f"Error clicking 'BOOK A DEMO' button (Method 3): {e}")
            print("Failed to click 'BOOK A DEMO' button using any method.")

# Handle the new tab/window (if it opens)
original_window = driver.current_window_handle
for window_handle in driver.window_handles:
    if window_handle != original_window:
        driver.switch_to.window(window_handle)
        break

# Verify that we are on the TidyCal page
try:
    WebDriverWait(driver, 10).until(EC.url_contains("tidycal.com"))
    print(f"Successfully navigated to: {driver.current_url}")
except:
    print("Failed to navigate to the TidyCal booking page.")

# Close the TidyCal tab and switch back to the original Ulai tab
driver.close()
driver.switch_to.window(original_window)

# 3. Locate and interact with the "Get a call" form.
print("Returning to Ulai Website")

try:
    # Find the name field
    name_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "name"))
    )
    name_field.send_keys("John Doe")
    print("Filled name field.")

    # Find the email field
    email_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "email"))
    )
    email_field.send_keys("john.doe@example.com")
    print("Filled email field.")

    # Find the phone number field
    phone_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "phone"))
    )
    phone_field.send_keys("123-456-7890")
    print("Filled phone field.")

    # Find the "GET A CALL" button and click it
    get_a_call_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[text()='GET A CALL']"))
    )
    get_a_call_button.click()
    print("Clicked 'GET A CALL' button.")

    # Add a short wait to allow for potential feedback/submission
    time.sleep(2)

except Exception as e:
    print(f"Error interacting with the 'Get a call' form: {e}")

# 4. Scroll to the "Frequently Asked Questions" section and expand the first question.
try:
    # Scroll to the FAQ section (using JavaScriptExecutor for better compatibility)
    faq_heading = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//h2[text()='Frequently Asked Questions']"))
    )
    driver.execute_script("arguments[0].scrollIntoView();", faq_heading)
    print("Scrolled to 'Frequently Asked Questions' section.")

    # Find the "What is Ulai?" question and click it
    ulai_question_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'What is Ulai?')]"))
    )
    ulai_question_button.click()
    print("Clicked 'What is Ulai?' question.")
    time.sleep(1)  # Wait for the answer to expand

except Exception as e:
    print(f"Error interacting with the 'Frequently Asked Questions' section: {e}")

# 5. Navigate to the Login page
try:
    login_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//a[text()='LOGIN']"))
    )
    login_button.click()
    print("Clicked 'LOGIN' button.")
    WebDriverWait(driver, 10).until(EC.url_contains("app.ulai.in"))
    print(f"Successfully navigated to: {driver.current_url}")

except Exception as e:
    print(f"Error navigating to the Login page: {e}")

# 6. Return to the main page
driver.get("https://ulai.in/")
print("Returning to Ulai Website")

# 7. Close the browser
driver.quit()
print("Browser closed.")