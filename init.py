import re
import csv
import pandas as pd
import requests

from agents.ui.agent_price_plan import AgentUIPricePlan
from agents.ui.agent_ui_languages import AgentUILanguages
from lib.smtpService import send_email_with_attachment
from lib.telegram import send_telegram_notification, list_chat_ids


# Function to load URLs from a CSV file
def load_urls_from_csv(csv_filename):
    urls = []
    with open(csv_filename, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if len(row) == 2:
                merchant_name, url = row
                urls.append((merchant_name, url))
    return urls


# Function to save the results to Excel
def save_results_to_excel(results, output_filename):
    df = pd.DataFrame(results)
    df.to_csv(output_filename, index=False, encoding='utf-8')


# Main function
def main():
    # Read the list of URLs from a CSV file
    csv_filename = "pricing_plan.csv"  # Replace with your actual CSV file
    urls = load_urls_from_csv(csv_filename)

    all_results = []

    # Process each URL
    for merchant_name, url in urls:
        response = requests.get(url)

        # Check if the request was successful
        if response.status_code != 200:
            print(f"Error fetching the page: {url}")
        else:

            # results = AgentUIPricePlan(merchant_name, url, response).process()
            results = AgentUILanguages(merchant_name, url, response).process()
            all_results.extend(results)

    # Save all results to an Excel file
    output_filename = "results.csv"  # Replace with desired output filename
    save_results_to_excel(all_results, output_filename)
    print(f"Results saved to {output_filename}")


if __name__ == "__main__":
    main()

# list_chat_ids()
# send_telegram_notification("pricing_plan.csv",'There is an issue found. The latest research found ')

# send_email_with_attachment("Latest scan report from Monitoring tools", "templates/email/regular-report.html", "pricing_plan.csv")