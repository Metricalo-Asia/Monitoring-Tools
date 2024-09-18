import os
import argparse
from database.database import Database  # Assuming the Database class is in 'database/database.py'
import pandas as pd


def create_migrations_table(db):
    """
    Create the migrations table if it doesn't exist.
    This table will store the names of the migrations that have been applied.
    """
    db.execute('''
        CREATE TABLE IF NOT EXISTS migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("Migrations table is ready.")


def get_applied_migrations(db):
    """
    Get the list of applied migrations.
    """
    result = db.fetchall("SELECT name FROM migrations")
    return {row[0] for row in result}


def apply_migration(db, migration_name, migration_sql):
    """
    Apply a single migration and record it in the migrations table.
    """
    db.execute(migration_sql)
    db.execute("INSERT INTO migrations (name) VALUES (?)", (migration_name,))
    print(f"Applied migration: {migration_name}")


def run_migrations(db):
    """
    Run all pending migrations that haven't been applied yet.
    """
    migrations_dir = 'database/migrations'
    applied_migrations = get_applied_migrations(db)

    # Get all .sql files from the migrations directory
    migration_files = sorted(
        [f for f in os.listdir(migrations_dir) if f.endswith('.sql')]
    )

    for migration_file in migration_files:
        if migration_file not in applied_migrations:
            with open(os.path.join(migrations_dir, migration_file), 'r') as file:
                migration_sql = file.read()
            apply_migration(db, migration_file, migration_sql)

    print("All migrations have been run.")


import os


def create_migration(migration_name):
    """
    Create a new migration file in the 'database/migrations' directory.
    Migration files will be prefixed with an incremental number to maintain correct order.
    """
    migrations_dir = 'database/migrations'

    if not os.path.exists(migrations_dir):
        os.makedirs(migrations_dir)

    # Get all existing migration files to determine the next prefix
    existing_migrations = [f for f in os.listdir(migrations_dir) if f.endswith('.sql')]

    # Extract numerical prefixes and sort them
    if existing_migrations:
        existing_numbers = sorted(
            int(f.split('_')[0]) for f in existing_migrations if f.split('_')[0].isdigit()
        )
        next_number = existing_numbers[-1] + 1  # Increment the highest number by 1
    else:
        next_number = 1  # Start numbering from 1 if no migrations exist

    # Format the prefix to have leading zeros (e.g., 001, 002, ...)
    prefix = f"{next_number:03d}"  # 3 digits padding

    # Create the migration filename with the prefix
    migration_filename = f"{prefix}_{migration_name}.sql"
    migration_filepath = os.path.join(migrations_dir, migration_filename)

    # Check if migration file already exists
    if os.path.exists(migration_filepath):
        print(f"Migration '{migration_filename}' already exists!")
    else:
        # Create a blank migration file
        with open(migration_filepath, 'w') as file:
            file.write("-- SQL migration script\n")

        print(f"Migration '{migration_filename}' created successfully.")


def import_sites_from_csv(csv_file):
    """
    Import sites data from a CSV file into the 'sites' table in the database.
    """
    # Initialize the database connection
    db = Database()

    # Read the CSV file into a DataFrame
    df = pd.read_csv(csv_file)

    # Check if the CSV file has the correct columns
    required_columns = [
        "Merchant Number", "Company name", "URL", "Type",
        "Test User L1 Login", "Test User L1 Password",
        "Test User L2 Login", "Test User L2 Password",
        "Test User L3 Login", "Test User L3 Password"
    ]
    if not all(col in df.columns for col in required_columns):
        print(f"CSV file must contain the following columns: {', '.join(required_columns)}")
        return

    # Insert data into the 'sites' table
    with db.conn:
        for index, row in df.iterrows():
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
                None  # `last_run` is NULL by default
            ))

    print(f"Data imported successfully from '{csv_file}'.")


def add_site(args):
    """
    Add a single site to the 'sites' table.
    """
    db = Database()
    with db.conn:
        db.conn.execute('''
            INSERT INTO sites (
                merchant_number, company_name, url, type,
                test_user_l1_login, test_user_l1_password,
                test_user_l2_login, test_user_l2_password,
                test_user_l3_login, test_user_l3_password,
                last_run
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            args.merchant_number, args.company_name, args.url, args.type,
            args.test_user_l1_login, args.test_user_l1_password,
            args.test_user_l2_login, args.test_user_l2_password,
            args.test_user_l3_login, args.test_user_l3_password,
            None
        ))
    print(f"Site added successfully: {args.company_name}")


def delete_site(args):
    """
    Delete a site from the 'sites' table by its ID.
    """
    db = Database()
    with db.conn:
        cursor = db.conn.execute('''
            DELETE FROM sites WHERE id = ?
        ''', (args.id,))
        if cursor.rowcount > 0:
            print(f"Site with ID {args.id} deleted successfully.")
        else:
            print(f"No site found with ID {args.id}.")


def clear_log():
    """
    Clear all data from the 'log' table.
    """
    db = Database()
    with db.conn:
        db.conn.execute('DELETE FROM log')
    print("All data cleared from the 'log' table.")


def view_latest_logs(limit=10):
    """
    View the latest logs from the 'log' table.
    :param limit: The number of latest log entries to display (default is 10).
    """
    sql_query = f"SELECT * FROM log ORDER BY created_at DESC LIMIT ?"
    db = Database()
    logs = db.process_sql(sql_query, (limit,))

    if logs:
        print(f"Showing latest {limit} logs:")
        for log in logs:
            print(log)
    else:
        print("No logs found.")


def view_sites(page=1, page_size=10):
    """
    View sites with pagination from the 'sites' table.
    :param page: The page number to display (default is 1).
    :param page_size: The number of sites per page (default is 10).
    """
    db = Database()
    offset = (page - 1) * page_size
    sql_query = f"SELECT * FROM sites LIMIT ? OFFSET ?"
    sites = db.process_sql(sql_query, (page_size, offset))

    if sites:
        print(f"Showing page {page}:")
        for site in sites:
            print(site)
    else:
        print("No sites found for this page.")


def main():
    parser = argparse.ArgumentParser(description='Manage database migrations and sites')
    parser.add_argument('command',
                        help='The command to execute (e.g., migrate, create_migration, import_sites, add_site, delete_site, view_logs, view_sites)',
                        choices=['migrate', 'create_migration', 'import_sites', 'add_site', 'delete_site', 'view_logs',
                                 'clear_log', 'view_sites'])
    parser.add_argument('--name', help='Name of the migration (used with create_migration)')
    parser.add_argument('--csv', help='Path to the CSV file (used with import_sites)')
    parser.add_argument('--merchant_number', help='Merchant Number (used with add_site)')
    parser.add_argument('--company_name', help='Company Name (used with add_site)')
    parser.add_argument('--url', help='URL (used with add_site)')
    parser.add_argument('--type', help='Type (used with add_site)')
    parser.add_argument('--test_user_l1_login', help='Test User L1 Login (used with add_site)')
    parser.add_argument('--test_user_l1_password', help='Test User L1 Password (used with add_site)')
    parser.add_argument('--test_user_l2_login', help='Test User L2 Login (used with add_site)')
    parser.add_argument('--test_user_l2_password', help='Test User L2 Password (used with add_site)')
    parser.add_argument('--test_user_l3_login', help='Test User L3 Login (used with add_site)')
    parser.add_argument('--test_user_l3_password', help='Test User L3 Password (used with add_site)')
    parser.add_argument('--id', type=int, help='ID of the site to delete (used with delete_site)')
    parser.add_argument('--limit', type=int, default=10, help='Limit the number of logs to view (used with view_logs)')
    parser.add_argument('--page', type=int, default=1, help='Page number to view (used with view_sites)')
    parser.add_argument('--page_size', type=int, default=10, help='Number of sites per page (used with view_sites)')

    args = parser.parse_args()

    db = Database()
    create_migrations_table(db)  # Ensure the migrations table exists

    if args.command == 'migrate':
        run_migrations(db)
    elif args.command == 'create_migration':
        if args.name:
            create_migration(args.name)
        else:
            print("Please provide a migration name using --name")
    elif args.command == 'import_sites':
        if args.csv:
            import_sites_from_csv(args.csv)
        else:
            print("Please provide a CSV file path using --csv")
    elif args.command == 'add_site':
        if all([args.merchant_number, args.company_name, args.url, args.type,
                args.test_user_l1_login, args.test_user_l1_password,
                args.test_user_l2_login, args.test_user_l2_password,
                args.test_user_l3_login, args.test_user_l3_password]):
            add_site(args)
        else:
            print("Please provide all required arguments for adding a site.")
    elif args.command == 'delete_site':
        if args.id is not None:
            delete_site(args)
        else:
            print("Please provide the ID of the site to delete using --id")
    elif args.command == 'clear_log':
        clear_log()
    elif args.command == 'view_logs':
        view_latest_logs(args.limit)
    elif args.command == 'view_sites':
        view_sites(args.page, args.page_size)

    db.close()


if __name__ == '__main__':
    main()
