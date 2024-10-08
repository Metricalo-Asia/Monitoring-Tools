import requests
from bs4 import BeautifulSoup


class AgentUIDownChecker:
    url = None
    merchant_name = None
    response = None
    has_error = False
    def __init__(self, merchant_name, url, response=None):
        self.url = url
        self.merchant_name = merchant_name
        self.response = response
        has_error = False

    @staticmethod
    def get_status_text(status_code):
        status_codes = {
            100: 'Continue',
            101: 'Switching Protocols',
            102: 'Processing',
            200: 'OK',
            201: 'Created',
            202: 'Accepted',
            203: 'Non-Authoritative Information',
            204: 'No Content',
            205: 'Reset Content',
            206: 'Partial Content',
            207: 'Multi-Status',
            300: 'Multiple Choices',
            301: 'Moved Permanently',
            302: 'Found',
            303: 'See Other',
            304: 'Not Modified',
            305: 'Use Proxy',
            307: 'Temporary Redirect',
            400: 'Bad Request',
            401: 'Unauthorized',
            402: 'Payment Required',
            403: 'Forbidden',
            404: 'Not Found',
            405: 'Method Not Allowed',
            406: 'Not Acceptable',
            407: 'Proxy Authentication Required',
            408: 'Request Timeout',
            409: 'Conflict',
            410: 'Gone',
            411: 'Length Required',
            412: 'Precondition Failed',
            413: 'Payload Too Large',
            414: 'URI Too Long',
            415: 'Unsupported Media Type',
            416: 'Range Not Satisfiable',
            417: 'Expectation Failed',
            418: "I'm a teapot",
            421: 'Misdirected Request',
            422: 'Unprocessable Entity',
            423: 'Locked',
            424: 'Failed Dependency',
            425: 'Too Early',
            426: 'Upgrade Required',
            428: 'Precondition Required',
            429: 'Too Many Requests',
            431: 'Request Header Fields Too Large',
            451: 'Unavailable For Legal Reasons',
            500: 'Internal Server Error',
            501: 'Not Implemented',
            502: 'Bad Gateway',
            503: 'Service Unavailable',
            504: 'Gateway Timeout',
            505: 'HTTP Version Not Supported',
            506: 'Variant Also Negotiates',
            507: 'Insufficient Storage',
            508: 'Loop Detected',
            510: 'Not Extended',
            511: 'Network Authentication Required'
        }
        return status_codes.get(status_code, 'Unknown Status Code')

    def process(self):
        print("Running: " + self.__class__.__name__)
        # Send an HTTP request to get the page content
        if self.response is None:
            self.response = requests.get(self.url)

        if self.response.status_code != 200:
            self.has_error = True

        result_dict = {
            "URL": self.url,
            "Status Code": self.response.status_code,
            "Status": AgentUIDownChecker.get_status_text(self.response.status_code),
        }

        return [result_dict]
