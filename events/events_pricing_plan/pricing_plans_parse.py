class PricingPlanParse:
    """Handles parsing the pricing plan information from the page content."""

    def __init__(self, soup, url, merchant_name):
        self.soup = soup
        self.url = url
        self.merchant_name = merchant_name
        self.state = None
        self.SUCCESS_MESSAGE = (f"Pricing plan parsing completed successfully for merchant '{self.merchant_name}' with URL: {self.url}.")
        self.FAILURE_MESSAGES = {
            'missing_pricings_div': (f"'pricings' div not found for merchant '{self.merchant_name}' with URL: {self.url}."),
            'missing_pricings_container_div': (f"'pricings-container' div not found for merchant '{self.merchant_name}' with URL: {self.url}."),
            'parsing_error': (f"Error occurred while parsing pricing plans for merchant '{self.merchant_name}' with URL: {self.url}.")
        }

    def parse(self):
        """Parse the page content to extract pricing plans."""
        try:
            merchant_data = {
                "URL": self.url,
                "Plans": []  # List to hold all pricing plans
            }

            # Find the 'pricings' div
            pricings_div = self.soup.find(class_="pricings")
            if not pricings_div:
                self.state = 'failure'
                self._handle_failure('missing_pricings_div')
                return merchant_data

            # Find the 'pricings-container' div within the 'pricings' div
            pricings_container_div = pricings_div.find(class_="pricings-container")
            if not pricings_container_div:
                self.state = 'failure'
                self._handle_failure('missing_pricings_container_div')
                return merchant_data

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

            self.state = 'success'
            self._handle_success()
            return merchant_data

        except Exception as e:
            self.state = 'failure'
            self._handle_failure('parsing_error')
            return {"URL": self.url, "Error": str(e)}

    def extract_product_id(self, url):
        """Extract product ID from the URL."""
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        if 'product_id' in query_params:
            return query_params['product_id'][0]
        return "Product ID not found"

    def _handle_success(self):
        """Handle the success state by printing the success message."""
        print(self.SUCCESS_MESSAGE)

    def _handle_failure(self, failure_key):
        """Handle the failure state by printing the specific failure message."""
        print(self.FAILURE_MESSAGES.get(failure_key, self.FAILURE_MESSAGES['parsing_error']))
