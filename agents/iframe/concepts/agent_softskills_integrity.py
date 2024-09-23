import requests
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
import re
import json

class AgentSoftskillsIntegrity:
    def __init__(self, url):
        self.url = url
        self.tier = self.get_tier_from_url(url)
        self.rows = []
        self.scripts = []
        self.js_script = None
        self.if_else_block = None

    def get_tier_from_url(self, url):
        """Extract tier from the URL."""
        tier_pattern = r'tier=(\d+)'  # Extract tier as digits
        match = re.search(tier_pattern, url)
        if match:
            return int(match.group(1))  # Return the matched tier number as an integer
        return None

    def extract_if_else_block(self, js_script):
        """Extract the if-else block from the JavaScript code."""
        if_else_block = re.search(r'(if\s*\(.*?\}\s*else\s*if.*?else\s*{.*?})', js_script, re.DOTALL)
        return if_else_block.group(0) if if_else_block else None

    def extract_js_script(self):
        """Extract JavaScript logic from the HTML."""
        for script in self.scripts:
            if "const urlParams" in script.string:
                self.js_script = script.string
                break

    def generate_simulation_function(self, if_else_block):
        """Generate Python function to simulate row visibility based on the extracted if-else block."""
        function_code = "def simulate_row_visibility(tier, rows):\n"
        indentation = "    "
        
        if "if (tier == '1')" in if_else_block:
            function_code += f"{indentation}if tier == 1:\n"
            function_code += f"{indentation*2}return rows  # All rows visible for tier 1\n"

        if "else if (tier == '2')" in if_else_block:
            function_code += f"{indentation}elif tier == 2:\n"
            function_code += f"{indentation*2}return [row for index, row in enumerate(rows) if index < 14]  # Hide rows with index >= 14\n"

        if "else if (tier == '3')" in if_else_block:
            function_code += f"{indentation}elif tier == 3:\n"
            function_code += f"{indentation*2}return [row for index, row in enumerate(rows) if index < 7]  # Hide rows with index >= 7\n"

        if "else" in if_else_block:
            function_code += f"{indentation}else:\n"
            function_code += f"{indentation*2}return []  # All rows hidden for any other tier\n"

        return function_code

    def execute_generated_function(self, generated_function_code):
        """Execute the generated Python function."""
        exec(generated_function_code, globals())

    def check_url(self, url):
        """Check the validity of a URL and return its status."""
        try:
            response = requests.head(url, allow_redirects=True)
            return response.status_code == 200, response.status_code
        except requests.RequestException:
            return False, None

    def extract_course_data(self, row):
        """Extract course data from a row and return it in the specified format."""
        cells = row.find_all('td')
        if len(cells) >= 3:  # Ensure there are at least 3 cells
            course_number = cells[0].get_text(strip=True)
            course_name = cells[1].get_text(strip=True)

            # Extract href if present
            link = cells[2].find('a')
            href_present = "yes" if link else "no"
            href = link['href'] if link else None

            # Check URL validity
            href_valid, href_status = self.check_url(href) if href else (False, None)

            return {
                "course_number": course_number,
                "course_name": course_name,
                "course_button": {
                    "href_present": href_present,
                    "href": href,
                    "href_valid": href_valid,
                    "href_status": href_status,
                }
            }
        return None

    def generate_json_output(self, visible_rows):
        """Generate JSON output from the list of visible rows."""
        final_data = [self.extract_course_data(row) for row in visible_rows]
        final_data = [data for data in final_data if data]  # Filter out None values
        return json.dumps(final_data, indent=4)

    def process(self):
        """Main processing function to create the final JSON result."""
        response = requests.get(self.url)
        soup = BeautifulSoup(response.text, "lxml")

        self.rows = soup.select('tbody tr')
        self.scripts = soup.find_all("script", src=None)  # Find all inline scripts
        self.extract_js_script()
        
        self.if_else_block = self.extract_if_else_block(self.js_script)
        generated_function_code = self.generate_simulation_function(self.if_else_block)
        self.execute_generated_function(generated_function_code)

        visible_rows = simulate_row_visibility(self.tier, self.rows)

        json_output = self.generate_json_output(visible_rows)
        print(json_output)

# Example usage
if __name__ == "__main__":
    url = 'https://dpmsbucket.s3.ap-south-1.amazonaws.com/Demo/ots2024/E-Learning+Courses/softskill.html?tier=3&amp;user_id=[WEBSITE_USER_ID]&amp;c_id=23e99e99-99f7-4101-8b9e-8e1da860368b&amp;w_id=8f1e74b9ec53&amp;c_id=23e99e99-99f7-4101-8b9e-8e1da860368b&amp;w_id=8f1e74b9ec53'  # Replace with your target URL
    agent = AgentSoftskillsIntegrity(url)
    agent.process()
    

    