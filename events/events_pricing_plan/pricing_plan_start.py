class PricingPlanStart:
    """Handles URL and merchant name validation."""

    def __init__(self, url, merchant_name):
        self.url = url
        self.merchant_name = merchant_name
        self.state = None
        self.SUCCESS_MESSAGE = (f"URL and merchant name validated successfully: '{self.merchant_name}' with URL: {self.url}.")
        self.FAILURE_MESSAGE = (f"Validation failed for merchant '{self.merchant_name}' due to missing parameters. "
                                f"URL provided: {self.url if self.url else 'None'}.")

    def validate(self):
        """Validate the URL and merchant name."""
        if self.url and self.merchant_name:
            self.state = 'success'
            self._handle_success()
        else:
            self.state = 'failure'
            self._handle_failure()

    def _handle_success(self):
        """Handle the success state by printing the success message."""
        print(self.SUCCESS_MESSAGE)

    def _handle_failure(self):
        """Handle the failure state by printing the failure message."""
        print(self.FAILURE_MESSAGE)
