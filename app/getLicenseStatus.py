import sqlite3
import subprocess
import os

# Database setup
db_file = "./database/licenses.db"
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

folderPath = "./output"

if not os.path.exists(folderPath):
    os.mkdir(folderPath)

# Retrieve the active server from the database
cursor.execute("SELECT Server FROM Server WHERE Status = 'Active'")
active_server_row = cursor.fetchone()
active_server = active_server_row[0] if active_server_row else None

if not active_server:
    print("No active server found. Please ensure there is an active server in the database.")
    exit(1)

# Properly formatted PowerShell command
command = rf'& "C:\\Program Files\\ANSYS Inc\\v212\\licensingclient\\winx64\\lmutil.exe" lmstat -c {active_server} -a'

try:
    # Run the command using PowerShell
    result = subprocess.run(["powershell.exe", "-Command", command], capture_output=True, text=True)

    # Write the result to a file
    with open(f"{folderPath}/output.txt", "w") as file:
        file.write(result.stdout)

    print("Return Code:", result.returncode)
    print("Output written to output.txt")

except Exception as e:
    print("Error running the command:", e)

# Close the database connection
conn.close()
