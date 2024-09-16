import requests
from bs4 import BeautifulSoup


class AgentUILanguages:
    url = None
    merchant_name = None
    response = None

    def __init__(self, merchant_name, url, response=None):
        self.url = url
        self.merchant_name = merchant_name
        self.response = response

    def process(self):
        results = []
        # Send an HTTP request to get the page content
        if self.response is None:
            self.response = requests.get(self.url)

            # Check if the request was successful
            if self.response.status_code != 200:
                print(f"Error fetching the page: {self.url}")
                return [{"Merchant": self.merchant_name, "URL": self.url, "Error": f"HTTP {self.response.status_code}"}]

        soup = BeautifulSoup(self.response.content, 'html.parser')

        # Find all the language elements
        language_buttons = soup.find('div',  {"id": "languages"}).find_all('a', class_='lang-button')

        # Extract the language names and add them to results
        for button in language_buttons:
            lang_name = button.find('div', class_='text-wrapper-3').text.strip()
            results.append(lang_name)

        print(str(len(results)) + " available Languages for " + self.merchant_name + " URL: " + self.url)
        print(results)
        # Prepare the final result
        result_dict = {
            "Merchant": self.merchant_name,
            "URL": self.url,
            "Language Count": len(results),
            "Languages": ','.join(results),
        }

        return [result_dict]
