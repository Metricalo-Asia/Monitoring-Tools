import json
import re

import requests
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup


class AgentUIPricePlan:
    url = None
    merchant_name = None
    response = None
    has_error = False

    def __init__(self, merchant_name, url, response=None):
        self.url = url
        self.merchant_name = merchant_name
        # Initialize the PricingPlanStart event
        self.start_event = PricingPlanStart(self.url, self.merchant_name)
        self.url_check = PricingPlanUrlCheck(self.url, self.merchant_name)

    def extract_product_id(self, url):
        # Parse the URL and extract query parameters
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)

        # Check if 'product_id' is present in the query parameters
        if 'product_id' in query_params:
            return query_params['product_id'][0]  # Return the first value of 'product_id'
        return "Product ID not found"

    # Function to process each URL and return the extracted data
    def process(self):
        """Process the pricing plan with validation checks."""
        # First validate URL and merchant name
        self.start_event.validate()
        if self.start_event.state == 'failure':
            return  # Stop the process if URL and merchant name validation fails

        # Then check the HTTP status code
        self.url_check.validate()
        if self.url_check.state == 'failure':
            return  # Stop the process if HTTP status code check fails

        print(f"Continuing with the pricing plan process for merchant '{self.merchant_name}' with URL: {self.url}...")

        # Parse the page content with BeautifulSoup
        soup = BeautifulSoup(self.response.content, 'html.parser')

        try:
            # Initialize a dictionary to hold all plan information
            merchant_data = {
                "URL": self.url,
                "Plans": []  # List to hold all pricing plans
            }

            # Find the 'pricings' div
            pricings_div = soup.find(class_="pricings")
            if not pricings_div:
                self.has_error = True
                raise ValueError("'pricings' div not found")

            # Find the 'pricings-container' div within the 'pricings' div
            pricings_container_div = pricings_div.find(class_="pricings-container")
            if not pricings_container_div:
                self.has_error = True
                raise ValueError("'pricings-container' div not found")

            # Find all 'pricing' divs within the 'pricings-container' div
            pricing_divs = pricings_container_div.find_all(class_="pricing")

            # Process each 'pricing' div
            for pricing_div in pricing_divs:
                plan_data = {}

                # Extract the plan name
                name_element = pricing_div.find(class_="type-wrap")
                plan_data["Plan Name"] = name_element.get_text(strip=True) if name_element else "Name not found"

                # Extract the price
                pricing_wrap_div = pricing_div.find(class_="pricing-wrap")
                if pricing_wrap_div:
                    price_element = pricing_wrap_div.find(class_="price")
                    if price_element:
                        raw_price = price_element.get_text(strip=True)
                        plan_data["Price"] = re.sub(r'\s+', ' ', raw_price).strip()
                    else:
                        plan_data["Price"] = "Price not found"
                else:
                    plan_data["Price"] = "Price not found"


                # Extract the benefits
                benefits_elements = pricing_div.select(".benefits .streamline")
                plan_data["Benefits"] = [benefit.get_text(strip=True) for benefit in benefits_elements]

                # Check if "Sign up" button exists and extract product_id from the button href
                signup_button = pricing_div.find(class_="pricing-btn")
                if signup_button and signup_button.get("href"):
                    signup_button_href = signup_button['href']
                    plan_data["Sign Up Button Href"] = signup_button_href

                    # Extract product_id from the href of the sign-up button
                    product_id = self.extract_product_id(signup_button_href)
                    plan_data["Product ID"] = product_id
                else:
                    plan_data["Sign Up Button Href"] = "Not found"
                    plan_data["Product ID"] = "Product ID not found"

                # Append each plan data to the 'Plans' list within the single merchant data
                merchant_data["Plans"].append(plan_data)

            # Add the merchant data (with all plans) to the results list
            results.append(merchant_data)

        except Exception as e:
            self.has_error = True
            results.append({"URL": self.url})

        self.has_error = (len(results) == 0)
        return results

