import sqlite3
import subprocess
import os

DB_FILE = "./database/licenses.db"
OUTPUT_FOLDER = "./output"
OUTPUT_FILE = f"{OUTPUT_FOLDER}/output.txt"
LMUTIL_PATH = r"C:\Program Files\ANSYS Inc\v212\licensingclient\winx64\lmutil.exe"

def setup_database():
    """Connects to the SQLite database."""
    if not os.path.exists(DB_FILE):
        print("Database file not found. Please ensure the database exists.")
        exit(1)
    return sqlite3.connect(DB_FILE)

def get_active_server(cursor):
    """Retrieves the active server from the database."""
    cursor.execute("SELECT Server FROM Server WHERE Status = 'Active'")
    active_server_row = cursor.fetchone()
    return active_server_row[0] if active_server_row else None

def ensure_output_directory():
    """Creates the output directory if it does not exist."""
    if not os.path.exists(OUTPUT_FOLDER):
        os.mkdir(OUTPUT_FOLDER)

def run_lmutil_command(active_server):
    """Runs the lmutil command and captures its output."""
    command = rf'& "{LMUTIL_PATH}" lmstat -c {active_server} -a'
    try:
        result = subprocess.run(["powershell.exe", "-Command", command], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        return result.stdout, result.returncode
    except Exception as e:
        print("Error running the command:", e)
        return None, -1

def save_output_to_file(output):
    """Writes command output to a file."""
    with open(OUTPUT_FILE, "w") as file:
        file.write(output)

def main():
    """Main function to coordinate execution."""
    conn = setup_database()
    cursor = conn.cursor()

    active_server = get_active_server(cursor)
    if not active_server:
        print("No active server found. Please ensure there is an active server in the database.")
        conn.close()
        exit(1)

    ensure_output_directory()
    output, return_code = run_lmutil_command(active_server)

    if output is not None:
        save_output_to_file(output)
        #print("Return Code:", return_code)
        #print(f"Output written to {OUTPUT_FILE}")

    conn.close()

if __name__ == "__main__":
    main()
