import json
import os
import re
import subprocess
import sys

from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, Request as FRequest

import pandas as pd
import sqlite3
from pydantic import BaseModel
from typing import Optional, List

from database.database import Database

load_dotenv()
app = FastAPI()


class Site(BaseModel):
    merchant_number: str
    company_name: str
    url: str
    type: str
    test_user_l1_login: str
    test_user_l1_password: str
    test_user_l2_login: Optional[str] = None
    test_user_l2_password: Optional[str] = None
    test_user_l3_login: Optional[str] = None
    test_user_l3_password: Optional[str] = None


class DeleteSite(BaseModel):
    id: int


# Retrieve secret key from environment variables
SECRET_KEY = os.getenv("SECRET_KEY")


# Function to verify Bearer Token
def verify_bearer_token(request: FRequest):
    authorization: str = request.headers.get("Authorization")
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token missing or malformed",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ")[1]
    if token != SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.get("/")
def read_root():
    return {"status": True, "Message": "Welcome to Monitoring Tools"}


@app.post("/import-sites/")
async def import_sites_from_csv(file: UploadFile, token_verified: None = Depends(verify_bearer_token)):
    df = pd.read_csv(file.file)
    required_columns = [
        "Merchant Number", "Company name", "URL", "Type",
        "Test User L1 Login", "Test User L1 Password",
        "Test User L2 Login", "Test User L2 Password",
        "Test User L3 Login", "Test User L3 Password"
    ]

    if not all(col in df.columns for col in required_columns):
        return {"status": False,
                "message": f"CSV file must contain the following columns: {', '.join(required_columns)}"}

    db = Database()
    with db.conn:
        for _, row in df.iterrows():
            try:
                db.conn.execute('''
                    INSERT INTO sites (
                        merchant_number, company_name, url, type,
                        test_user_l1_login, test_user_l1_password,
                        test_user_l2_login, test_user_l2_password,
                        test_user_l3_login, test_user_l3_password,
                        last_run
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row["Merchant Number"], row["Company name"], row["URL"], row["Type"],
                    row["Test User L1 Login"], row["Test User L1 Password"],
                    row["Test User L2 Login"], row["Test User L2 Password"],
                    row["Test User L3 Login"], row["Test User L3 Password"],
                    None
                ))
            except sqlite3.IntegrityError:
                continue

    return {"status": True, "message": "Data imported successfully"}


@app.post("/add-site/")
def add_site(site: Site, token_verified: None = Depends(verify_bearer_token)):
    db = Database()
    with db.conn:
        try:
            db.conn.execute('''
                INSERT INTO sites (
                    merchant_number, company_name, url, type,
                    test_user_l1_login, test_user_l1_password,
                    test_user_l2_login, test_user_l2_password,
                    test_user_l3_login, test_user_l3_password,
                    last_run
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                site.merchant_number, site.company_name, site.url, site.type,
                site.test_user_l1_login, site.test_user_l1_password,
                site.test_user_l2_login, site.test_user_l2_password,
                site.test_user_l3_login, site.test_user_l3_password,
                None
            ))
        except Exception as ex:
            return {'status': False, "message": f"Unable to add the site: {site.company_name}, {ex.__str__()}"}
    return {"message": f"Site added successfully: {site.company_name}"}


@app.delete("/delete-site/")
def delete_site(site: DeleteSite, token_verified: None = Depends(verify_bearer_token)):
    db = Database()
    with db.conn:
        cursor = db.conn.execute('DELETE FROM sites WHERE id = ?', (site.id,))
        if cursor.rowcount > 0:
            return {"status": True, "message": f"Site with ID {site.id} deleted successfully."}
        else:
            return {"status": False, "message": f"No site found with ID {site.id}."}


@app.delete("/clear-log/")
def clear_log(token_verified: None = Depends(verify_bearer_token)):
    db = Database()
    with db.conn:
        try:
            db.conn.execute('DELETE FROM log')
        except Exception as ex:
            return {"status": False, "message": f"Could not delete the log, {ex.__str__()}"}
    return {"status": True, "message": "All data cleared from the 'log' table."}


@app.get("/latest-logs/")
def view_latest_logs(limit: int = 10, page: int = 1, status: int = -1,
                     token_verified: None = Depends(verify_bearer_token)):
    db = Database()

    # Fetch total number of logs
    if status == -1:
        count_query = "SELECT COUNT(*) FROM log"
        total_logs = db.process_sql(count_query)[0][0]
    else:
        count_query = "SELECT COUNT(*) FROM log WHERE has_error = ?"
        total_logs = db.process_sql(count_query, (status,))[0][0]

    max_pages = (total_logs + limit - 1) // limit  # Calculate maximum number of pages
    offset = (page - 1) * limit

    # Dynamically change query based on status
    if status == -1:
        query = """
            SELECT 
                log.id, 
                log.site_id, 
                log.plans, 
                log.language_count, 
                log.languages, 
                log.status_code, 
                log.status, 
                log.iframe_integrity_status, 
                log.iframe_url, 
                log.iframe_concept_result, 
                log.form_check_data, 
                log.has_error, 
                log.created_at,
                sites.merchant_number, 
                sites.company_name, 
                sites.url, 
                sites.type
            FROM log
            LEFT JOIN sites ON log.site_id = sites.id
            ORDER BY log.created_at DESC
            LIMIT ? OFFSET ?
        """
        logs = db.process_sql_wcolumn(query, (limit, offset))
    else:
        query = """
            SELECT 
                log.id, 
                log.site_id, 
                log.plans, 
                log.language_count, 
                log.languages, 
                log.status_code, 
                log.status, 
                log.iframe_integrity_status, 
                log.iframe_url, 
                log.iframe_concept_result, 
                log.form_check_data, 
                log.has_error, 
                log.created_at,
                sites.merchant_number, 
                sites.company_name, 
                sites.url, 
                sites.type
            FROM log
            LEFT JOIN sites ON log.site_id = sites.id
            WHERE log.has_error = ?
            ORDER BY log.created_at DESC
            LIMIT ? OFFSET ?
        """
        logs = db.process_sql_wcolumn(query, (status, limit, offset))

    if logs:
        return {
            'status': True,
            "max_pages": max_pages,
            "logs": logs
        }
    else:
        return {
            'status': False,
            "message": "No logs found for this page."
        }


@app.get("/view-sites/")
def view_sites(page: int = 1, page_size: int = 10, token_verified: None = Depends(verify_bearer_token)):
    db = Database()

    # Fetch total number of sites
    total_sites = db.process_sql("SELECT COUNT(*) FROM sites")[0][0]  # Assuming process_sql returns a list of tuples
    max_pages = (total_sites + page_size - 1) // page_size  # Calculate maximum number of pages

    offset = (page - 1) * page_size
    sites = db.process_sql_wcolumn("SELECT * FROM sites LIMIT ? OFFSET ?", (page_size, offset))

    if sites:
        return {
            'status': True,
            "page": page,
            "max_pages": max_pages,
            "sites": sites
        }
    else:
        return {'status': False, "message": "No sites found for this page."}


@app.get("/get-sitekey/")
async def get_sitekey(cookie: str, pagenum: int = 1, token_verified: None = Depends(verify_bearer_token)):
    db = Database()

    url = f"{os.getenv('CRM_HOST')}/administrator/app/subscription/service/list?tl=en&filter%5B_sort_order%5D=DESC&filter%5B_page%5D={pagenum}&filter%5B_per_page%5D=192"
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
                    updates = "site_api_key = ?"
                    condition = "url = ?"
                    update_params = (site_api_key, site_url)
                    db.update('sites', updates, condition, update_params)

            # Recursive call if there are more pages
            if pagenum < max_pages:
                return await get_sitekey(cookie, pagenum + 1, token_verified)

            return {"status": True, "message": "API keys updated successfully"}

        else:
            db.close()
            return {"status": False, "message": "Error fetching data from the website"}

    except Exception as e:
        db.close()
        return {"status": False, "message": f"Error fetching URL {url}: {e}"}

    finally:
        db.close()


@app.post("/run")
def run_init_script(token_verified: None = Depends(verify_bearer_token)):
    try:
        # Use the absolute path to the Python executable
        result = subprocess.run([os.getenv("PYTHON_PATH"), "init.py"], capture_output=True, text=True)

        if result.returncode == 0:
            return {"status": True, "message": "Successful run", "output": result.stdout}
        else:
            return {"status": False, "message": "Error running init.py", "details": result.stderr}

    except Exception as e:
        return {"status": False, "message": str(e)}


@app.post("/async/run")
async def async_run_init_script(request: FRequest, token_verified: None = Depends(verify_bearer_token)):
    try:
        # Extract raw JSON data from the request
        request_data = await request.json()
        data = request_data.get("data")

        if not data:
            return {"status": False, "message": "Missing 'data' in request body"}

        # Get the directory where the current script (api.py) is located
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Path to the asyncinit.py script in the same directory as api.py
        script_path = os.path.join(current_dir, "asyncinit.py")

        # Use the absolute path to the Python executable
        python_path = os.getenv("PYTHON_PATH",
                                sys.executable)  # Use current Python executable if PYTHON_PATH is not set

        # Run the asyncinit.py script with the passed data (arguments should be separate in the list)
        subprocess.run([python_path, script_path, "run", "--data", data], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)

        return {"status": True, "message": "Successful run"}
    except Exception as e:
        return {"status": False, "message": str(e)}


@app.post("/async/get_sitekeys")
async def async_get_sitekeys(request: FRequest, token_verified: None = Depends(verify_bearer_token)):
    try:
        # Extract raw JSON data from the request
        request_data = await request.json()
        cookie = request_data.get("cookie")
        sites = request_data.get("sites")
        crm_host = request_data.get("crm_host")

        if not cookie:
            return {"status": False, "message": "Missing 'cookie' in request body"}
        if not sites:
            return {"status": False, "message": "Missing 'sites' in request body"}
        if not crm_host:
            return {"status": False, "message": "Missing 'crm_host' in request body"}

        # Get the directory where the current script (api.py) is located
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Path to the asyncinit.py script in the same directory as api.py
        script_path = os.path.join(current_dir, "asyncinit.py")

        # Use the absolute path to the Python executable
        python_path = os.getenv("PYTHON_PATH",
                                sys.executable)  # Use current Python executable if PYTHON_PATH is not set

        # Run the asyncinit.py script with the passed data (arguments should be separate in the list)
        subprocess.Popen([python_path, script_path, "get_sitekeys", "--cookie", cookie, '--crmhost', crm_host, "--data",
                          json.dumps(sites)])
        # output = subprocess.run([python_path, script_path, "get_sitekeys", "--cookie", cookie, '--crmhost', crm_host, "--data",json.dumps(sites)], capture_output=True, text=True)
        # print(output)
        return {"status": True, "message": "Successful run"}
    except Exception as e:
        return {"status": False, "message": str(e)}
