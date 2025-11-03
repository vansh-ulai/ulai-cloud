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

# 2. Verify the page title
expected_title = "Ulai | #1 AI Voice Agent Platform for Enterprises Business"
actual_title = driver.title
assert actual_title == expected_title, f"Title mismatch: Expected '{expected_title}', but got '{actual_title}'"
print("Page title verification successful.")

# 3. Click the "BOOK A DEMO" button (using link text)
try:
    book_demo_link = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.LINK_TEXT, "BOOK A DEMO"))
    )
    book_demo_link.click()
    print("Clicked 'BOOK A DEMO' link.")
    # Wait for the new page or element to load after clicking the link
    WebDriverWait(driver, 10).until(EC.url_contains("tidycal.com")) #Verify navigation
    print(f"Navigated to: {driver.current_url}")

    driver.back() #Go back to main page
    print(f"Navigated back to: {driver.current_url}")

except Exception as e:
    print(f"Error clicking 'BOOK A DEMO' link: {e}")

# 4. Locate and interact with the "Get a call from our Gen AI powered Receptionist agent by filling the below" section.
try:
    # Locate the form elements (replace with actual locators after inspecting the page)
    name_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "name"))
    )
    email_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "email"))
    )
    phone_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "phone"))
    )

    # Fill in the form
    name_field.send_keys("John Doe")
    email_field.send_keys("john.doe@example.com")
    phone_field.send_keys("123-456-7890")

    print("Filled the 'Get a call' form.")

    # Locate and click the "GET A CALL" button (using text)
    get_a_call_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[text()='GET A CALL']"))
    )
    get_a_call_button.click()
    print("Clicked 'GET A CALL' button.")

    # Wait for a success message or page change (adjust the wait time as needed)
    # Example:
    # WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "success-message")))
    time.sleep(2) #Wait 2 seconds for the form to submit

except Exception as e:
    print(f"Error interacting with the 'Get a call' form: {e}")

# 5. Scroll to the "Frequently Asked Questions" section and expand the first question.
try:
    # Scroll to the FAQ section (using a heading as an anchor)
    faq_heading = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//h2[text()='Frequently Asked Questions']"))
    )
    driver.execute_script("arguments[0].scrollIntoView();", faq_heading)
    print("Scrolled to 'Frequently Asked Questions' section.")

    # Find the first question and click it (assuming the questions are in a list)
    first_question = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//div[@class='faq-item']/button")) #Adjust XPATH as needed
    )
    first_question.click()
    print("Expanded the first FAQ question.")
    time.sleep(1)

except Exception as e:
    print(f"Error interacting with the FAQ section: {e}")

# 6. Click on the "LOGIN" button.
try:
    login_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.LINK_TEXT, "LOGIN"))
    )
    login_button.click()
    print("Clicked 'LOGIN' button.")
    WebDriverWait(driver, 10).until(EC.url_contains("app.ulai.in")) #Verify navigation
    print(f"Navigated to: {driver.current_url}")
    driver.back() #Go back to main page
    print(f"Navigated back to: {driver.current_url}")

except Exception as e:
    print(f"Error clicking 'LOGIN' button: {e}")

# 7. Close the browser
driver.quit()
print("Browser closed.")