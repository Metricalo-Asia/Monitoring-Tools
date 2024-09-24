# Monitoring-Tools

The application will monitor the status of each connected services of the metricalo merchants.

## Requirements

The installation requirements are given below

- Python 3.12

## Installation

The installation is very simple, you can just install the dependencies by running the following command

`pip install -r .\requirements.txt`

You can use any python environment that you may like.

## Management Tool

You can find a file called `metman.py` in the project root, which is a useful tool for managing the sites, logs, and database migrations. The available commands are given below:

### Commands

- **`migrate`**: Runs all pending database migrations that haven't been applied yet.
  - Example
    ```sh
    python metman.py migrate
    ```

- **`create_migration`**: Creates a new migration file in the `migrations` directory.
  - `--name`: Specifies the name of the migration file. For example:
    ```sh
    python metman.py create_migration --name=create_sites_table
    ```

- **`import_sites`**: Imports site data from a CSV file into the database.
  - `--csv`: Specifies the path to the CSV file containing the site data. For example:
    ```sh
    python metman.py import_sites --csv=path/to/sites.csv
    ```

- **`add_site`**: Adds a single site to the database.
  - `--merchant_number`: The merchant number for the site.
  - `--company_name`: The company name for the site.
  - `--url`: The URL of the site.
  - `--type`: The type of the site.
  - `--test_user_l1_login`: Login for Test User L1.
  - `--test_user_l1_password`: Password for Test User L1.
  - `--test_user_l2_login`: Login for Test User L2.
  - `--test_user_l2_password`: Password for Test User L2.
  - `--test_user_l3_login`: Login for Test User L3.
  - `--test_user_l3_password`: Password for Test User L3.

  Example:
    ```sh
      python metman.py add_site --merchant_number=001 --company_name="Acme Corp" --url=https://example.com --type=Retail --test_user_l1_login=login1 --test_user_l1_password=password1 --test_user_l2_login=login2 --test_user_l2_password=password2 --test_user_l3_login=login3 --test_user_l3_password=password3
    ```

- **`delete_site`**: Deletes a site by its ID.
  - `--id`: The ID of the site to delete. For example:
    ```sh
    python metman.py delete_site --id=123
    ```

- **`clear_log`**: Clears all data from the `log` table.

  Example:
    ```sh
    python metman.py clear_log
    ```

- **`view_logs`**: Displays the latest logs from the `log` table.
  - `--limit`: The number of logs to display (default is 10). For example:
    ```sh
    python metman.py view_logs --limit=5
    ```

- **`view_sites`**: Displays sites with pagination from the `sites` table.
  - `--page`: The page number to display (default is 1).
  - `--page_size`: The number of sites per page (default is 10). For example:
    ```sh
    python metman.py view_sites --page=1 --page_size=5
    ```

- **`get_sitekey`**: Refreshes the `sites` with the latest site keys from CRM.
  - `--cookie`: The Cookie is the one you can find it in your network tab in the request header after logging into the CRM.
    ```sh
    python metman.py get_sitekey --cookie=9mqf99gmcgrmpe1h1bok
    ```
