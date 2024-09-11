import re
import csv
import pandas as pd
from urllib.parse import urlparse, parse_qs
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Function to extract product_id from a URL (specifically the href of the signup button)
def extract_product_id(url):
    # Parse the URL and extract query parameters
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    
    # Check if 'product_id' is present in the query parameters
    if 'product_id' in query_params:
        return query_params['product_id'][0]  # Return the first value of 'product_id'
    return "Product ID not found"

# Function to process each URL and return the extracted data
def process_url(merchant_name, url, driver):
    results = []
    driver.get(url)

    # Use WebDriverWait to wait until the 'pricings' div is present
    wait = WebDriverWait(driver, 10)  # Wait for up to 10 seconds
    try:
        pricings_div = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "pricings")))

        # Find the 'pricings-container' div within the 'pricings' div
        pricings_container_div = pricings_div.find_element(By.CLASS_NAME, "pricings-container")

        # Find all 'pricing' divs within the 'pricings-container' div
        pricing_divs = pricings_container_div.find_elements(By.CLASS_NAME, "pricing")

        # Process each 'pricing' div
        for pricing_div in pricing_divs:
            plan_data = {"Merchant": merchant_name, "URL": url}
            
            # Extract the plan name
            try:
                name_element = pricing_div.find_element(By.CLASS_NAME, "type-wrap")
                plan_data["Plan Name"] = name_element.get_attribute("innerHTML").strip()
            except:
                plan_data["Plan Name"] = "Name not found"
            
            # Extract the price
            try:
                pricing_wrap_div = pricing_div.find_element(By.CLASS_NAME, "pricing-wrap")
                price_elements = pricing_wrap_div.find_elements(By.CLASS_NAME, "price")
                if price_elements:
                    raw_price = price_elements[0].get_attribute("innerHTML").strip()
                    plan_data["Price"] = ' '.join(raw_price.split())
                else:
                    plan_data["Price"] = "Price not found"
            except:
                plan_data["Price"] = "Price not found"

            # Extract the benefits
            try:
                benefits_elements = pricing_div.find_elements(By.CSS_SELECTOR, ".benefits .streamline")
                plan_data["Benefits"] = [benefit.get_attribute("innerHTML").strip() for benefit in benefits_elements]
            except:
                plan_data["Benefits"] = []

            # Check if "Sign up" button exists and extract product_id from the button href
            try:
                signup_button = pricing_div.find_element(By.CLASS_NAME, "pricing-btn")
                signup_button_href = signup_button.get_attribute("href")
                if signup_button_href and signup_button_href.startswith("http"):
                    plan_data["Sign Up Button Href"] = signup_button_href
                    
                    # Extract product_id from the href of the sign-up button
                    product_id = extract_product_id(signup_button_href)
                    plan_data["Product ID"] = product_id

                    # Print product_id for each plan
                    print(f"Merchant: {merchant_name}")
                    print(f"Product ID: {product_id}")
                else:
                    plan_data["Sign Up Button Href"] = "Invalid or missing"
                    plan_data["Product ID"] = "Product ID not found"
            except:
                plan_data["Sign Up Button Href"] = "Not found"
                plan_data["Product ID"] = "Product ID not found"

            # Print the extracted data to the console
            print(f"URL: {plan_data['URL']}")
            print(f"Plan Name: {plan_data['Plan Name']}")
            print(f"Price: {plan_data['Price']}")
            print("Benefits:")
            for benefit in plan_data["Benefits"]:
                print(f" - {benefit}")
            print(f"Sign Up Button Href: {plan_data['Sign Up Button Href']}")
            
            print("")  # Empty line for readability
            
            results.append(plan_data)

    except Exception as e:
        print(f"Error processing URL {url}: {e}")
        results.append({"Merchant": merchant_name, "URL": url, "Error": str(e)})

    return results

# Function to load URLs from a CSV file
def load_urls_from_csv(csv_filename):
    urls = []
    with open(csv_filename, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if len(row) == 2:
                merchant_name, url = row
                urls.append((merchant_name, url))
    return urls

# Function to save the results to Excel
def save_results_to_excel(results, output_filename):
    df = pd.DataFrame(results)
    df.to_excel(output_filename, index=False)

# Main function
def main():
    # Read the list of URLs from a CSV file
    csv_filename = "pricing_plan.csv"  # Replace with your actual CSV file
    urls = load_urls_from_csv(csv_filename)

    # Configure Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run headless if you do not need a GUI
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Setup Chrome WebDriver using webdriver_manager to automatically get the correct driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    all_results = []

    try:
        # Process each URL
        for merchant_name, url in urls:
            results = process_url(merchant_name, url, driver)
            all_results.extend(results)

    finally:
        # Close the browser
        driver.quit()

    # Save all results to an Excel file
    output_filename = "pricing_results.xlsx"  # Replace with desired output filename
    save_results_to_excel(all_results, output_filename)
    print(f"Results saved to {output_filename}")

if __name__ == "__main__":
    main()
