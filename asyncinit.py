import argparse
import asyncio
import json
import logging
import os
import re
import traceback

import pandas as pd
import requests
from bs4 import BeautifulSoup

from agents.crm.agent_crm import AgentCRM
from agents.iframe.agent_iframe_integrity import AgentIframeIntegrity
from agents.ui.agent_form_signup_checkout import AgentFormChecker
from agents.ui.agent_price_plan import AgentUIPricePlan
from agents.ui.agent_ui_down_checker import AgentUIDownChecker
from agents.ui.agent_ui_languages import AgentUILanguages
from lib.telegram import send_telegram_notification

site_keys = []
client = None

# logging.basicConfig(filename="working",
#                     filemode='a',
#                     format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
#                     datefmt='%H:%M:%S',
#                     level=logging.DEBUG)


def log_to_laravel(merged_dict):
    headers = {'Content-Type': 'application/json'}
    url = f"{os.getenv('LARAVEL_API')}/api/montool/log"
    data = {
        'site_id': int(merged_dict.get('id', 0)),  # Cast to int
        'plans': json.dumps(merged_dict.get('plans')),
        'language_count': int(merged_dict.get('Language Count', 0)),  # Cast to int
        'languages': merged_dict.get('Languages', ''),
        'status_code': int(merged_dict.get('Status Code', 0)),  # Cast to int
        'status': merged_dict.get('Status', ''),
        'iframe_integrity_status': merged_dict.get('Iframe_Integrity_Status', ''),
        'iframe_url': merged_dict.get('Iframe_URL', ''),
        'form_check_data': json.dumps(merged_dict.get('form_check_data')),
        'iframe_concept_result': json.dumps(merged_dict.get('iframe_concept_result')),
        'crm_data': json.dumps(merged_dict.get('crm_data')),
        'has_error': bool(merged_dict.get('has_error', False)),  # Ensure it's a boolean
    }

    response = requests.request('POST', url, json={'data': data}, headers=headers)
    logging.info(response.content)


def start_agents(site_data):
    if site_data.empty:
        print("No sites found in the database.")
        return

    site_row = site_data.iloc[0]  # Get the first (and only) row

    merchant_name = site_row['company_name']
    url = site_row['url']
    # merged_results = []
    print("Running test cases on " + merchant_name + " site : " + url)
    # Merge results and prepare for saving
    merged_dict = {**site_row}
    try:
        response = requests.get(url)
        results_status = AgentUIDownChecker(merchant_name, url, response).process()
        # Check if the request was successful
        if response.status_code != 200:
            merged_dict = {**site_row, **results_status[0]}
            merged_dict = {**merged_dict, **{"has_error": True}}
            if client is not None:
                found_issues = "";
                if "Status" in results_status[0]:
                    found_issues += f'<blockquote><b>Webshop</b> {results_status[0]["Status"]}  </blockquote> \n'
                else:
                    found_issues += f'<blockquote><b>Webshop</b> Could not load the website  </blockquote> \n'
                send_telegram_notification(None,
                                           f' {str(url).replace(".", "_").replace("https://","")} \n\n <i>Issues:</i> \n '
                                           + found_issues
                                           , client['telegram_bot_token'],
                                           client['telegram_chat_id'])
        else:

            agent_price_plan = AgentUIPricePlan(merchant_name, url, response)
            agent_ui_languages = AgentUILanguages(merchant_name, url, response)
            agent_iframe_integrity = AgentIframeIntegrity(site_row)
            agent_signup = AgentFormChecker(merchant_name, url, response)
            agent_crm = AgentCRM(site_row)

            # Process the results from the agents
            results_crm_plan = agent_crm.process()
            results_languages = agent_ui_languages.process()
            results_price_plan = agent_price_plan.process()
            results_iframe_integrity = agent_iframe_integrity.process()
            results_form = agent_signup.process()

            if results_status:
                merged_dict = {**site_row, **results_status[0]}

            if results_languages:
                merged_dict = {**merged_dict, **results_languages[0]}

            if results_price_plan:
                merged_dict = {**merged_dict, **results_price_plan[0]}

            if results_iframe_integrity:
                merged_dict = {**merged_dict, **results_iframe_integrity[0]}

            if results_form:
                merged_dict = {**merged_dict, **results_form[0]}

            if results_form:
                merged_dict = {**merged_dict, **results_crm_plan}

            if agent_crm.has_error or agent_ui_languages.has_error or agent_iframe_integrity.has_error or \
                    agent_signup.has_error or agent_price_plan.has_error:
                merged_dict = {**merged_dict, **{"has_error": True}}
                found_issues = ""
                if agent_crm.has_error:
                    if "crm_plans_status" in results_crm_plan[0]:
                        found_issues += f'<blockquote><b>CRM</b> {results_crm_plan[0]["crm_plans_status"]} </blockquote> \n'
                    else:
                        found_issues += f'<blockquote><b>CRM</b> Something went wrong in the CRM Plans </blockquote> \n'

                if agent_ui_languages.has_error:
                    if "Error" in results_languages[0]:
                        found_issues += f'<blockquote><b>Languages</b> Could not check languages </blockquote> \n'
                    else:
                        found_issues += f'<blockquote><b>Languages</b> Something went wrong in the languages </blockquote> \n'

                if "Language Count" in results_languages[0]:
                    if results_languages[0]["Language Count"] < 24:
                        found_issues += f'<blockquote><b>Languages</b> {str(results_languages[0]["Language Count"])} found, 24 should be there </blockquote> \n'

                if agent_iframe_integrity.has_error:
                    if "Iframe_Integrity_Status" in results_iframe_integrity[0]:
                        found_issues += f'<blockquote><b>IFrame:</b> {str(results_iframe_integrity[0]["Iframe_Integrity_Status"])} </blockquote> \n'
                    else:
                        found_issues += f'<blockquote><b>IFrame:</b> Something went wrong in the iframe </blockquote> \n'

                if agent_signup.has_error:
                    if "Error" in results_form[0]:
                        found_issues += f'<blockquote><b>Forms</b> {str(results_form[0]["Error"])} </blockquote> \n'
                    else:
                        found_issues += f'<blockquote><b>Forms</b> Something went wrong </blockquote> \n'

                if agent_price_plan.has_error:
                    if "Error" in results_price_plan[0]:
                        found_issues += f'<blockquote><b>Price Plan</b> {str(results_price_plan[0]["Error"])} </blockquote> \n'
                    else:
                        found_issues += f'<blockquote><b>Price Plan</b> Something went wrong </blockquote> \n'


                if client is not None:
                    send_telegram_notification(None, f'{str(url).replace(".","_").replace("https://","")} \n\n <i>Issues:</i> \n '
                                               + found_issues
                                               , client['telegram_bot_token'],
                                               client['telegram_chat_id'])

        # merged_results.append(merged_dict)
        # Save the results to the log table
        # db.log(site_row, merged_dict)
        return merged_dict

    except Exception as e:
        merged_dict = {**site_row, **{
            'Status': f"Exception: {e} || {' | '.join(traceback.format_exception(e))}",
            'Status Code': "-1",
        }}
        merged_dict = {**merged_dict, **{"has_error": True}}
        if client is not None:
            send_telegram_notification(None, f'!! 𝑰𝒔𝒔𝒖𝒆 𝑭𝒐𝒖𝒏𝒅 !!\n\n URL: {url}', client['telegram_bot_token'],
                                       client['telegram_chat_id'])
        return merged_dict

    # Close the database connection
    # db.close()


async def get_sitekeys(sites, cookie, crmhost, pagenum=1):
    url = f"{crmhost}/administrator/app/subscription/service/list?tl=en&filter%5B_sort_order%5D=DESC&filter%5B_page%5D={pagenum}&filter%5B_per_page%5D=192"
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'priority': 'u=0, i',
        'sec-ch-ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'cookie': f'hl=en; PHPSESSID={cookie}',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            entries = soup.select("form .table tbody tr")
            if entries.__len__() == 0:
                return {'status': False, "message": "Could not update"}
            pagination = soup.select(".pagination > li")
            max_pages = 0
            for page in pagination:
                if page.text.isnumeric():
                    max_pages = max(max_pages, int(page.text))

            # Extract site info
            for site_row in entries:
                site_url = site_row.select("td.sonata-ba-list-field")[7].get_text(strip=True)
                site_api_button = site_row.select_one(
                    "td.sonata-ba-list-field-actions .btn-group div button[data-target]"
                )
                site_api_key = ""
                match = re.search(r"alert\('([A-Za-z0-9]+)'\);", site_api_button['onclick'])
                if match:
                    site_api_key = match.group(1)
                    if site_url in sites:
                        site_keys.append({
                            'url': site_url,
                            'site_api_key': site_api_key
                        })
            # Recursive call if there are more pages
            if pagenum < max_pages:
                return await get_sitekeys(sites, cookie, crmhost, pagenum + 1)

            return {"status": True, "message": "API keys updated successfully"}

        else:
            # db.close()
            return {"status": False, "message": "Error fetching data from the website"}
    except Exception as e:
        # db.close()
        return {"status": False, "message": f"Error fetching URL {url}: {e}"}

    finally:
        # db.close()
        return


async def refresh_sitekeys(sites, cookie, crmhost):
    try:
        await get_sitekeys(sites, cookie, crmhost)
    except Exception as e:
        print(e)

    headers = {'Content-Type': 'application/json'}
    url = f"{os.getenv('LARAVEL_API')}/api/montool/sitekeys/refresh"
    response = requests.request('POST', url, json={'data': site_keys}, headers=headers)
    logging.info(response.content)


def main():
    parser = argparse.ArgumentParser(description='Manage database migrations and sites')
    parser.add_argument('command',
                        help='The command to execute (e.g., migrate, create_migration, import_sites, add_site, delete_site, view_logs, view_sites)',
                        choices=['run', 'get_sitekeys'])
    parser.add_argument('--data', help='Data for the site')
    parser.add_argument('--client', help='Client Data for the site')
    parser.add_argument('--cookie', help='CRM Cookie for the site')
    parser.add_argument('--crmhost', help='CRM HOST URL')

    args = parser.parse_args()
    if args.command == 'run':
        if args.data and args.client:
            try:
                data = json.loads(args.data)
                global client
                client = json.loads(args.client)
                if client is not None:
                    if isinstance(client, list):
                        client = client[0]
                try:
                    results = start_agents(pd.DataFrame([data]))
                    log_to_laravel(results)
                except Exception as ex:
                    site_row = pd.DataFrame([data]).iloc[0]

                    merged_dict = {**site_row, **{
                        'Status': f"Exception: {ex} || {' | '.join(traceback.format_exception(ex))}",
                        'Status Code': "-1",
                    }}
                    merged_dict = {**merged_dict, **{"has_error": True}}
                    log_to_laravel(merged_dict)
            except Exception as e:
                logging.info(e)
                # logging.info(traceback.extract_tb(e.__traceback__))
        else:
            print("Please pass the site list in json using --data and client data using --client")

    if args.command == 'get_sitekeys':

        if not args.data:
            print("Please pass the site list in json using --data")
        if not args.cookie:
            print("Please pass the crm cookie using --cookie")
        if not args.crmhost:
            print("Please pass the crm host using --crmhost")

        sites = json.loads(args.data)
        cookie = args.cookie
        crmhost = args.crmhost
        loop = asyncio.get_event_loop()
        loop.run_until_complete(refresh_sitekeys(sites, cookie, crmhost))


main()
