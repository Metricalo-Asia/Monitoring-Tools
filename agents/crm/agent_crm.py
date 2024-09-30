import json
import os

import requests
from bs4 import BeautifulSoup


class AgentCRM:
    url = None
    site_api_key = None
    site_api_this_webshop_url = None
    row = None
    merchant_name = None
    response = None
    has_error = False

    def __init__(self, row):
        self.row = row
        self.url = row['url']
        self.site_api_this_webshop_url = f"{os.getenv('CRM_HOST')}/api/s/v3/this/webshop"
        self.site_api_key = row['site_api_key']
        self.merchant_name = row['company_name']

    def process(self):
        print("Running: " + self.__class__.__name__)
        results = []
        # Send an HTTP request to get the page content

        if self.site_api_key is None:
            self.has_error = (len(results) == 0)
            return {
                "URL": self.url,
                "crm_plans_status": "API_KEY_NOT_FOUND",
                "crm_plans": len(results),
            }

        headers = {
            'x-api-key': self.site_api_key
        }
        response = requests.get(self.site_api_this_webshop_url, None, headers=headers);

        if response.status_code != 200:
            self.has_error = (len(results) == 0)
            return {
                "URL": self.url,
                "crm_plans_status": "INVALID SITE API KEY OR CRM HOST",
                "crm_plans": results,
            }

        response = json.loads(response.content)

        if "data" in response.keys():
            if "products" in response["data"].keys():
                return {
                    "URL": self.url,
                    "crm_plans_status": "OK",
                    "crm_data": response['data'],
                }
            else:
                self.has_error = (len(results) == 0)
                return {
                    "URL": self.url,
                    "crm_plans_status": "INVALID PRODUCT RESPONSE FROM CRM",
                    "crm_data": results,
                }
        else:
            self.has_error = (len(results) == 0)
            return {
                "URL": self.url,
                "crm_plans_status": "INVALID DATA RESPONSE FROM CRM",
                "crm_data": results,
            }

        #
        # soup = BeautifulSoup(self.response.content, 'html.parser')
        #
        # # Find all the language elements
        # language_buttons = soup.find('div',  {"id": "languages"}).find_all('a', class_='lang-button')
        #
        # # Extract the language names and add them to results
        # for button in language_buttons:
        #     lang_name = button.find('div', class_='text-wrapper-3').text.strip()
        #     results.append(lang_name)
        # # Prepare the final result
        # result_dict = {
        #     "URL": self.url,
        #     "Language Count": len(results),
        #     "Languages": ','.join(results),
        # }
        #
        # self.has_error = (len(results) == 0)
        #
        # return [result_dict]
