import json
import os

import requests
from bs4 import BeautifulSoup


class AgentIframeIntegrity:
    url = None
    merchant_name = None
    response = None
    login_url = None
    login_post_url = None
    login_nonce_key = None
    username = None
    password = None
    level = None
    product_type = None
    has_error = False
    row = None

    def __init__(self, row, level="1"):
        self.url = row['url']
        self.level = level
        self.merchant_name = row['company_name']
        self.product_type = row['type']
        self.username = row['test_user_l' + self.level + '_login']
        self.password = row['test_user_l' + self.level + '_password']
        self.login_url = self.url + "/login"
        self.row = row

    def process_concept(self):
        results = []
        for i in range(1, 4):
            temp = {
                'level': i.__str__(),
            }

            if not self.row['test_user_l' + i.__str__() + '_login'] or not self.row[
                'test_user_l' + i.__str__() + '_password']:
                temp['status'] = "Credentials Not Found"
                results.append(temp)
                continue

            (login_response, session) = self.login_response(level=i.__str__())
            if login_response is None or login_response.status_code != 200:
                print(f"AgentIframeIntegrity: Error fetching the page: {self.login_post_url}")
                result_dict = {
                    "URL": self.url,
                    'Iframe_Integrity_Status': "HTTP_NOT_OK: " + "HTTP_" + str(login_response.status_code) + "_FOUND"
                }
                self.has_error = True
                return [result_dict]

            authenticated_soup = BeautifulSoup(login_response.content, 'html.parser')
            iframe = authenticated_soup.find('iframe', class_='dashboard-content')

            if iframe:
                iframe_src = iframe.get('src')
                temp['concept_url'] = iframe_src

            results.append(temp)
            session.close()
        return results

    def login_response(self, level="1"):
        username = self.row['test_user_l' + level + '_login']
        password = self.row['test_user_l' + level + '_password']

        session = requests.Session()
        session.headers.update({
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
        self.response = session.get(self.login_url)

        soup = BeautifulSoup(self.response.content, 'html.parser')

        # Find the form element and extract the action attribute
        form = soup.find('form', class_='login-form')
        self.login_post_url = (self.url + form.get('action')) if form else None

        # Find the hidden input for 'login-form-nonce' and extract the value
        nonce_input = form.find('input', {'name': 'login-form-nonce'}) if form else None
        if nonce_input:
            login_nonce_key = nonce_input.get('value') if nonce_input else None
            payload = {
                'username': username,
                'password': password,
                'login-form-nonce': login_nonce_key,
                'task': 'login.login',
                'rememberme': '1'  # Optional if the form includes a "remember me" checkbox
            }
            login_response = session.post(self.login_post_url, data=payload)
        else:
            login_response = None
        # Perform the POST request to submit the login form
        return [login_response, session]

    def process(self):
        print("Running: " + self.__class__.__name__)
        results = []
        iframe_concept_result = None
        (login_response, session) = self.login_response(level=self.level)

        if login_response is None or login_response.status_code != 200:
            print(f"AgentIframeIntegrity: Error fetching the page: {self.login_post_url}")
            result_dict = {
                "URL": self.url,
                'Iframe_Integrity_Status': "HTTP_NOT_OK: " + "HTTP_" + str(login_response.status_code) + "_FOUND"
            }
            self.has_error = True
            return [result_dict]

        authenticated_soup = BeautifulSoup(login_response.content, 'html.parser')
        iframe = authenticated_soup.find('iframe', class_='dashboard-content')

        iframe_src = None
        if iframe:
            iframe_src = iframe.get('src')
        else:
            result_dict = {
                "URL": self.url,
                'Iframe_Integrity_Status': "IFRAME_NOT_FOUND"
            }
            self.has_error = True
            return [result_dict]

        if not iframe_src:
            result_dict = {
                "URL": self.url,
                'Iframe_Integrity_Status': "IFRAME_NOT_LINKED"
            }
            self.has_error = True
            return [result_dict]

        iframe_response = session.get(iframe_src)

        if iframe_response.status_code != 200:
            print(f"AgentIframeIntegrity: Error fetching the page: {iframe_src}")
            self.has_error = True
            result_dict = {
                "URL": self.url,
                'Iframe_Integrity_Status': "IFRAME_HTTP_NOT_OK: " + "HTTP_" + str(
                    iframe_response.status_code) + "_FOUND",
                'Iframe_URL': str(iframe_src),
                'iframe_concept_result': iframe_concept_result
            }
        else:
            iframe_concept_result = self.process_concept()
            result_dict = {
                "URL": self.url,
                'Iframe_Integrity_Status': "CONNECTED",
                'Iframe_URL': str(iframe_src),
                'iframe_concept_result': iframe_concept_result
            }

        return [result_dict]
