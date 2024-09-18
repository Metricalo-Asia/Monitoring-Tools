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
    has_error = False

    def __init__(self, row, level="1"):
        self.url = row['URL']
        self.level = level
        self.merchant_name = row['Company name']
        self.username = row['Test User L' + level + ' Login']
        self.password = row['Test User L' + level + ' Password']
        self.login_url = self.url + "/login"

    def process(self):
        print("Running: " + self.__class__.__name__)
        results = []

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
        self.login_nonce_key = nonce_input.get('value') if nonce_input else None

        payload = {
            'username': self.username,
            'password': self.password,
            'login-form-nonce': self.login_nonce_key,
            'task': 'login.login',
            'rememberme': '1'  # Optional if the form includes a "remember me" checkbox
        }

        # Perform the POST request to submit the login form
        login_response = session.post(self.login_post_url, data=payload)
        if login_response.status_code != 200:
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
            iframe_src = iframe.get('src') if nonce_input else None
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

        iframeSession = requests.Session()
        iframe_response = iframeSession.get(iframe_src)

        if iframe_response.status_code != 200:
            print(f"AgentIframeIntegrity: Error fetching the page: {iframe_src}")
            self.has_error = True
            result_dict = {
                "URL": self.url,
                'Iframe_Integrity_Status': "IFRAME_HTTP_NOT_OK: " + "HTTP_" + str(iframe_response.status_code) + "_FOUND",
                'Iframe_URL': str(iframe_src)
            }

        else:
            result_dict = {
                "URL": self.url,
                'Iframe_Integrity_Status': "CONNECTED",
                'Iframe_URL': str(iframe_src)
            }

        return [result_dict]
