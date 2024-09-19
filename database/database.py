import json
import sqlite3
import os
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()


class Database:
    def __init__(self):
        db_name = os.getenv('DATABASE_NAME')
        self.db_path = f"database/{db_name}"

        # Check if the 'database' directory exists, if not create it
        if not os.path.exists('database'):
            os.makedirs('database')

        # Check if the database file exists
        if not os.path.isfile(self.db_path):
            print(f"Database '{db_name}' does not exist. Creating...")
            self.create_database()
        else:
            print(f"Database '{db_name}' already exists.")

        # Establish connection for further use
        self.conn = sqlite3.connect(self.db_path)

    def create_database(self):
        # Establish a connection to create the database
        conn = sqlite3.connect(self.db_path)
        print(f"Database created at '{self.db_path}'")
        conn.close()

    def execute(self, query, params=None):
        """Execute a simple SQL query with optional parameters."""
        with self.conn:
            if params:
                self.conn.execute(query, params)
            else:
                self.conn.execute(query)

    def log(self, site_row, results):
        """
        Save the processed results into the log table.
        :param db: Instance of the Database class.
        :param site_row: Row of the site that was processed.
        :param results: Merged results dictionary from the agents.
        """
        insert_query = """
        INSERT INTO log (site_id, plans, language_count, languages, status_code, status, iframe_integrity_status, iframe_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        # Extract necessary fields for logging
        params = (
            site_row.get('id').item(),  # Foreign key to the sites table
            json.dumps(results.get('Plans')),  # Store plans (as JSON text)
            results.get('Language Count', 0),  # Language count
            results.get('Languages', ''),  # List of languages
            results.get('Status Code', 0),  # Status code
            results.get('Status', ''),  # Status message
            results.get('Iframe_Integrity_Status', ''),  # Iframe integrity status
            results.get('Iframe_URL', '')  # Iframe URL
        )

        self.execute(insert_query, params)
        # Update the last_run timestamp for the processed site

        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        updates = "last_run = ?"
        condition = "id = ?"
        update_params = (current_time, site_row.get('id').item())

        # Use the existing update function
        self.update('sites', updates, condition, update_params)

    def fetchall(self, query, params=None):
        """Fetch all rows for a given query."""
        with self.conn:
            cursor = self.conn.execute(query, params or [])
            return cursor.fetchall()

    def process_sql(self, sql_query_or_script, params=None):
        """
        Execute a raw SQL query or script. The query can either be a simple
        SQL command or a more complex SQL script.

        :param sql_query_or_script: SQL string or script to be executed.
        :param params: Parameters to safely inject into the SQL query.
        :return: Result of the query (if applicable).
        """
        try:
            with self.conn:
                if params:
                    result = self.conn.execute(sql_query_or_script, params)
                else:
                    result = self.conn.execute(sql_query_or_script)

                # If the query returns rows, fetch the result
                if result.description:
                    return result.fetchall()

        except sqlite3.Error as e:
            print(f"An error occurred while processing SQL: {e}")
            return None

        print("SQL executed successfully.")

    def delete(self, table, condition, params):
        """
        Delete records from the database.

        :param table: The table name where you want to delete records.
        :param condition: The condition to select the records to delete.
        :param params: Parameters for the condition (e.g., tuple with values).
        """
        delete_sql = f"DELETE FROM {table} WHERE {condition}"
        try:
            with self.conn:
                self.conn.execute(delete_sql, params)
            print(f"Record(s) deleted from {table}.")
        except sqlite3.Error as e:
            print(f"An error occurred while deleting data: {e}")

    def update(self, table, updates, condition, params):
        """
        Update records in the database.

        :param table: The table name where you want to update records.
        :param updates: The columns and values to update (e.g., "name = ?").
        :param condition: The condition to select the records to update.
        :param params: Parameters for the update and condition (e.g., tuple with values).
        """
        update_sql = f"UPDATE {table} SET {updates} WHERE {condition}"
        try:
            with self.conn:
                self.conn.execute(update_sql, params)
            print(f"Record(s) updated in {table}.")
        except sqlite3.Error as e:
            print(f"An error occurred while updating data: {e}")

    def close(self):
        """Close the connection to the database."""
        if self.conn:
            self.conn.close()
            print("Connection to the database has been closed.")
