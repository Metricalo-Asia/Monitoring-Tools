import requests
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup


class AgentUIPricePlan:
    url = None
    merchant_name = None
    response = None

    def __init__(self, merchant_name, url, response=None):
        self.url = url
        self.merchant_name = merchant_name
        self.response = response

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
        results = []
        # Send an HTTP request to get the page content
        if self.response is None:
            self.response = requests.get(self.url)

            # Check if the request was successful
            if self.response.status_code != 200:
                print(f"Error fetching the page: {self.url}")
                return [{"Merchant": self.merchant_name, "URL": self.url, "Error": f"HTTP {self.response.status_code}"}]

        # Parse the page content with BeautifulSoup
        soup = BeautifulSoup(self.response.content, 'html.parser')
        try:
            # Find the 'pricings' div
            pricings_div = soup.find(class_="pricings")
            if not pricings_div:
                raise ValueError("'pricings' div not found")

            # Find the 'pricings-container' div within the 'pricings' div
            pricings_container_div = pricings_div.find(class_="pricings-container")
            if not pricings_container_div:
                raise ValueError("'pricings-container' div not found")

            # Find all 'pricing' divs within the 'pricings-container' div
            pricing_divs = pricings_container_div.find_all(class_="pricing")

            # Process each 'pricing' div
            for pricing_div in pricing_divs:
                plan_data = {"Merchant": self.merchant_name, "URL": self.url}

                # Extract the plan name
                name_element = pricing_div.find(class_="type-wrap")
                plan_data["Plan Name"] = name_element.get_text(strip=True) if name_element else "Name not found"

                # Extract the price
                pricing_wrap_div = pricing_div.find(class_="pricing-wrap")
                if pricing_wrap_div:
                    price_element = pricing_wrap_div.find(class_="price")
                    plan_data["Price"] = price_element.get_text(strip=True) if price_element else "Price not found"
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


                # Print the extracted data to the console
                print(f"Merchant: {self.merchant_name}")
                print(f"Product ID: {plan_data['Product ID']}")
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
            print(f"Error processing URL {self.url}: {e}")
            results.append({"Merchant": self.merchant_name, "URL": self.url, "Error": str(e)})

        return results
