# Description: This script automates interactions with the Ulai AI Agent website (https://ulai.in/).
# It demonstrates navigation, form filling, and button clicking using Selenium.

# Import necessary libraries
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Configure Chrome options for headless browsing (optional)
chrome_options = Options()
# chrome_options.add_argument("--headless")  # Run in headless mode (no browser window)
chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration (recommended for headless)
chrome_options.add_argument("--window-size=1920x1080")  # Set window size
chrome_options.add_argument("--disable-extensions") # Disable extensions

# Set up Chrome driver (replace with your webdriver path)
webdriver_path = "/usr/local/bin/chromedriver"  # Example path, adjust as needed
service = Service(executable_path=webdriver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# Website URL
url = "https://ulai.in/"

try:
    # 1. Navigate to the Ulai website
    driver.get(url)
    print(f"Navigated to: {url}")

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

        # Wait for the new page to load (Tidycal page)
        WebDriverWait(driver, 10).until(EC.url_contains("tidycal.com"))
        print("Successfully navigated to the Tidycal booking page.")

        # Go back to the main page
        driver.back()
        WebDriverWait(driver, 10).until(EC.url_to_be(url)) # Wait for the main page to load back
        print("Navigated back to the main page.")

    except Exception as e:
        print(f"Error clicking 'BOOK A DEMO' link: {e}")

    # 4. Locate and click the "Try for free" button (using text)
    try:
        try_for_free_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Try for free')]"))
        )
        try_for_free_button.click()
        print("Clicked 'Try for free' button.")

        # Wait for the new page to load (assuming it's the signup page)
        WebDriverWait(driver, 10).until(EC.url_contains("app.ulai.in"))
        print("Successfully navigated to the signup page.")

        # Go back to the main page
        driver.back()
        WebDriverWait(driver, 10).until(EC.url_to_be(url)) # Wait for the main page to load back
        print("Navigated back to the main page.")

    except Exception as e:
        print(f"Error clicking 'Try for free' button: {e}")

    # 5. Locate and interact with the "Get a call" section (filling the form)
    try:
        # Locate the input fields (assuming they have specific IDs or names)
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

        print("Filled in the 'Get a call' form.")

        # Locate and click the "GET A CALL" button
        get_a_call_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'GET A CALL')]"))
        )
        get_a_call_button.click()
        print("Clicked 'GET A CALL' button.")

        # Add a wait to see the result (you might need to adjust this based on the actual behavior)
        time.sleep(5)  # Wait for 5 seconds (adjust as needed)

    except Exception as e:
        print(f"Error interacting with the 'Get a call' section: {e}")

    # 6. Click on the LOGIN button
    try:
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "LOGIN"))
        )
        login_button.click()
        print("Clicked 'LOGIN' button.")

        WebDriverWait(driver, 10).until(EC.url_contains("app.ulai.in"))
        print("Successfully navigated to the login page.")

        driver.back()
        WebDriverWait(driver, 10).until(EC.url_to_be(url)) # Wait for the main page to load back
        print("Navigated back to the main page.")

    except Exception as e:
        print(f"Error clicking 'LOGIN' button: {e}")

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    # 7. Close the browser
    driver.quit()
    print("Browser closed.")