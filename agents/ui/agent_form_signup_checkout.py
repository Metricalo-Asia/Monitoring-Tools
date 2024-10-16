import json
import re

import requests
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
from faker import Faker

from agents.ui.agent_ui_down_checker import AgentUIDownChecker


class AgentFormChecker:
    url = None
    merchant_name = None
    response = None
    has_error = False

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

    def process_signup_form(self, signup_page_url):
        dom_status_signup = False
        dom_status_checkout = False
        form_session = requests.session()
        form_session.headers.update({
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-US,en;q=0.9,bn-US;q=0.8,bn;q=0.7",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "priority": "u=0, i",
            "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        })

        parsed_url = urlparse(signup_page_url)
        root_domain = f'{parsed_url.scheme}://{parsed_url.netloc}'
        checkout_page_url = f'{parsed_url.scheme}://{parsed_url.netloc}/en/order'

        signup_response = form_session.get(signup_page_url)

        if signup_response.status_code != 200:
            return {
                'signup': {
                    'url': signup_page_url,
                    'status': signup_response.status_code.__str__() + ": " + AgentUIDownChecker.get_status_text(
                        signup_response.status_code),
                    "dom_status": "UNABLE_TO_CHECK",
                    "form_data": {}
                },
                'checkout': {
                    'url': checkout_page_url,
                    'status': "UNABLE_TO_CHECK",
                    "dom_status": "UNABLE_TO_CHECK",
                    "form_data": {}
                }
            }

        soup = BeautifulSoup(signup_response.content, 'html.parser')
        form = soup.find('form', {'id': 'customer_form'})

        if not form:
            dom_status_signup = False
            return {
                'signup': {
                    'url': signup_page_url,
                    'status': signup_response.status_code.__str__() + ": " + AgentUIDownChecker.get_status_text(
                        signup_response.status_code),
                    "dom_status": "FORM_NOT_FOUND",
                    "form_data": {}
                },
                'checkout': {
                    'url': checkout_page_url,
                    'status': "UNABLE_TO_CHECK",
                    "dom_status": "UNABLE_TO_CHECK",
                    "form_data": {}
                }
            }

        # Step 3: Extract form inputs into a dictionary
        form_data = {}
        fake = Faker()
        for input_tag in form.find_all('input'):
            input_name = input_tag.get('name')
            input_value = input_tag.get('value', '')  # default to empty string if no value
            if input_name:
                if input_name == "customer[first_name]":
                    form_data[input_name] = fake.first_name()
                elif input_name == "customer[last_name]":
                    form_data[input_name] = fake.last_name()
                elif input_name == "customer[address]":
                    form_data[input_name] = fake.address()
                elif input_name == "customer[postcode]":
                    form_data[input_name] = fake.postcode()
                elif input_name == "customer[city]":
                    form_data[input_name] = fake.city()
                elif input_name == "customer[email]":
                    form_data[input_name] = fake.email()
                elif input_name == "customer[phone]":
                    form_data[input_name] = fake.phone_number()
                else:
                    form_data[input_name] = input_value

        # Step 5: Submit the form using requests
        form_method = form['method'].lower()  # Extract the form method (POST or GET)
        target_url = root_domain + form['action']
        if form_method == "post":
            signed_up_response = form_session.post(target_url, data=form_data)
        else:
            signed_up_response = form_session.get(target_url, data=form_data)

        dom_status_signup = True

        # Define the target URL for the form submission
        if signed_up_response.status_code != 200:
            return {
                'signup': {
                    'url': signup_page_url,
                    'status': signup_response.status_code.__str__() + ": " + AgentUIDownChecker.get_status_text(
                        signup_response.status_code),
                    'form_data': form_data,
                    "dom_status": "OK" if dom_status_signup else "NOT OK"
                },
                'checkout': {
                    'url': checkout_page_url,
                    'status': signed_up_response.status_code.__str__() + ": " + AgentUIDownChecker.get_status_text(
                        signed_up_response.status_code),
                    "dom_status": "UNABLE_TO_CHECK",
                    "form_data": {}
                }
            }

        soup = BeautifulSoup(signed_up_response.content, 'html.parser')
        checkout_page = soup.find('div', class_="payment")

        if not checkout_page:
            return {
                'signup': {
                    'url': signup_page_url,
                    'status': signup_response.status_code.__str__() + ": " + AgentUIDownChecker.get_status_text(
                        signup_response.status_code),
                    'form_data': form_data,
                    "dom_status": "OK" if dom_status_signup else "NOT OK"
                },
                'checkout': {
                    'url': checkout_page_url,
                    'status': signed_up_response.status_code.__str__() + ": " + AgentUIDownChecker.get_status_text(
                        signed_up_response.status_code),
                    "dom_status": "NOT_CHECKOUT_PAGE",
                    "form_data": {}
                }
            }

        checkout_form = checkout_page.find("form")
        if not checkout_form:
            return {
                'signup': {
                    'url': signup_page_url,
                    'status': signup_response.status_code.__str__() + ": " + AgentUIDownChecker.get_status_text(
                        signup_response.status_code),
                    'form_data': form_data,
                    "dom_status": "OK"
                },
                'checkout': {
                    'url': checkout_page_url,
                    'status': signed_up_response.status_code.__str__() + ": " + AgentUIDownChecker.get_status_text(
                        signed_up_response.status_code),
                    "dom_status": "CHECKOUT_FORM_NOT_FOUND",
                    "form_data": {}
                }
            }

        return {
            'signup': {
                'url': signup_page_url,
                'status': signup_response.status_code.__str__() + ": " + AgentUIDownChecker.get_status_text(
                    signup_response.status_code),
                'form_data': form_data,
                "dom_status": "OK"
            },
            'checkout': {
                'url': checkout_page_url,
                'status': signed_up_response.status_code.__str__() + ": " + AgentUIDownChecker.get_status_text(
                    signed_up_response.status_code),
                "dom_status": "OK",
                "form_data": {}
            }
        }

    def process(self):
        print("Running: " + self.__class__.__name__)
        results = []
        # Send an HTTP request to get the page content
        if self.response is None:
            self.response = requests.get(self.url)

            # Check if the request was successful
            if self.response.status_code != 200:
                self.has_error = True
                return [{"URL": self.url, "Error": f"HTTP {self.response.status_code}"}]

        # Parse the page content with BeautifulSoup
        soup = BeautifulSoup(self.response.content, 'html.parser')

        try:
            # Initialize a dictionary to hold all plan information
            merchant_data = {
                "url": self.url,
                "form_check_data": []
            }

            # Find the 'pricings' div
            pricings_div = soup.find(class_="pricings")
            if not pricings_div:
                self.has_error = True
                return [{"URL": self.url, "Error": f"'pricings' div not found"}]

            # Find the 'pricings-container' div within the 'pricings' div
            pricings_container_div = pricings_div.find(class_="pricings-container")
            if not pricings_container_div:
                self.has_error = True
                return [{"URL": self.url, "Error": f"'pricings-container' div not found"}]

            # Find all 'pricing' divs within the 'pricings-container' div
            pricing_divs = pricings_container_div.find_all(class_="pricing")

            # Process each 'pricing' div
            for pricing_div in pricing_divs:
                plan_data = {}

                # Extract the plan name
                name_element = pricing_div.find(class_="type-wrap")
                plan_data["plan_name"] = name_element.get_text(strip=True) if name_element else ""

                # Extract the price
                pricing_wrap_div = pricing_div.find(class_="pricing-wrap")
                if pricing_wrap_div:
                    price_element = pricing_wrap_div.find(class_="price")
                    if price_element:
                        raw_price = price_element.get_text(strip=True)
                        plan_data["price"] = re.sub(r'\s+', ' ', raw_price).strip()
                    else:
                        plan_data["price"] = "Unavailable"
                else:
                    plan_data["price"] = "Unavailable"

                # Check if "Sign up" button exists and extract product_id from the button href
                signup_button = pricing_div.find(class_="pricing-btn")
                if signup_button and signup_button.get("href"):
                    signup_button_href = signup_button['href']
                    plan_data["btn_link"] = signup_button_href
                    plan_data['forms'] = self.process_signup_form(signup_button_href)

                else:
                    plan_data["btn_link"] = "Not found"

                # Append each plan data to the 'Plans' list within the single merchant data
                merchant_data["form_check_data"].append(plan_data)

            # Add the merchant data (with all plans) to the results list
            results.append(merchant_data)

        except Exception as e:
            self.has_error = True
            results.append({
                "url": self.url,
                "form_check_data": [],
                "Error": e
            })

        self.has_error = (len(results) == 0)
        return results
