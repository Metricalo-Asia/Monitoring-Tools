import requests

class PricingPlanUrlCheck:
    """Handles HTTP status code validation."""

    def __init__(self, url, merchant_name):
        self.url = url
        self.merchant_name = merchant_name
        self.state = None
        self.SUCCESS_MESSAGE = (f"HTTP status code check passed for merchant '{self.merchant_name}' with URL: {self.url}.")
        self.FAILURE_MESSAGE = (f"HTTP status code check failed for merchant '{self.merchant_name}' with URL: {self.url}.")
    
    def validate(self):
        """Check the HTTP status code of the URL."""
        try:
            response = requests.get(self.url)
            if response.status_code == 200:
                self.state = 'success'
                self._handle_success()
            else:
                self.state = 'failure'
                print(f"Invalid HTTP status code {response.status_code} for URL: {self.url}.")
        except requests.exceptions.RequestException as e:
            self.state = 'failure'
            print(f"Error fetching the URL for merchant '{self.merchant_name}': {e}")
    
    def _handle_success(self):
        """Handle the success state by printing the success message."""
        print(self.SUCCESS_MESSAGE)

    def _handle_failure(self):
        """Handle the failure state by printing the failure message."""
        print(self.FAILURE_MESSAGE)
