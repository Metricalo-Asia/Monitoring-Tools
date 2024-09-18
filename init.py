import re
import csv
import pandas as pd
import requests
from openpyxl import Workbook

from agents.iframe.agent_iframe_integrity import AgentIframeIntegrity
from agents.ui.agent_price_plan import AgentUIPricePlan
from agents.ui.agent_ui_down_checker import AgentUIDownChecker
from agents.ui.agent_ui_languages import AgentUILanguages

from lib.smtpService import send_email_with_attachment
from lib.telegram import send_telegram_notification, list_chat_ids


# Function to load URLs from a CSV file
def load_urls_from_csv(csv_filename, chunksize=10000):
    # Create an empty DataFrame to append chunks
    full_data = pd.DataFrame()

    # Read the CSV file in chunks
    for chunk in pd.read_csv(csv_filename, chunksize=chunksize):
        # Append each chunk to the DataFrame
        full_data = pd.concat([full_data, chunk], ignore_index=True)

    return full_data


# Function to save the results to Excel
def save_results_to_excel(results, output_filename):
    df = pd.DataFrame(results)
    df.to_excel(output_filename, index=False)


# Main function
def main():
    # Read the list of URLs and related data from the CSV file
    csv_filename = "pricing_plan.csv"  # Replace with your actual CSV file
    output_filename = "results.xlsx"  # Replace with desired output filename
    full_data = load_urls_from_csv(csv_filename)  # Now returns a DataFrame with all columns

    all_results = []

    # Process each row in the DataFrame
    for index, row in full_data.iterrows():

        merchant_name = row['Company name']
        url = row['URL']
        merged_results = []
        print("Running test cases on " + merchant_name + " site : " + url)

        response = requests.get(url)

        results_status = AgentUIDownChecker(merchant_name, url, response).process()

        # Check if the request was successful
        if response.status_code != 200:
            print(f"Error fetching the page: {url}")
        else:
            agent_price_plan = AgentUIPricePlan(merchant_name, url, response)
            agent_ui_languages = AgentUILanguages(merchant_name, url, response)
            agent_iframe_integrity = AgentIframeIntegrity(row)
            results_price_plan = agent_price_plan.process()
            results_languages = agent_ui_languages.process()
            results_iframe_integrity = agent_iframe_integrity.process()

            if results_languages and results_status:
                merged_dict = {**row, **results_price_plan[0], **results_languages[0], **results_status[0],
                               **results_iframe_integrity[0]}
                merged_results.append(merged_dict)

        all_results.extend(merged_results)
        save_results_to_excel(all_results, output_filename)
        print(f"Results saved to {output_filename} for {merchant_name} site: {url}")

    # Save all results to an Excel file


if __name__ == "__main__":
    main()

# list_chat_ids()
# send_telegram_notification("pricing_plan.csv",'There is an issue found. The latest research found ')

# send_email_with_attachment("Latest scan report from Monitoring tools", "templates/email/regular-report.html", "pricing_plan.csv")
