import subprocess
import os

# Path for server configuration file
SERVER_FILE = "./additionalInfo/servers.txt"
OUTPUT_FILE = "./output.txt"

# Ensure the additional info directory exists
os.makedirs("./additionalInfo", exist_ok=True)

# Read the server configurations
active_server = None
if os.path.exists(SERVER_FILE):
    with open(SERVER_FILE, "r") as file:
        # Look for the first non-commented, non-empty line as the active server
        for line in file:
            server = line.strip()
            if server and not server.startswith("#"):
                active_server = server
                break

if not active_server:
    print("No active server found. Please ensure './additionalInfo/servers.txt' contains a valid server.")
    exit(1)

# Properly formatted PowerShell command
command = rf'& "C:\Program Files\ANSYS Inc\v212\licensingclient\winx64\lmutil.exe" lmstat -c {active_server} -a'

try:
    # Run the command using PowerShell
    result = subprocess.run(["powershell.exe", "-Command", command], capture_output=True, text=True)

    # Write the result to a file
    with open(OUTPUT_FILE, "w") as file:
        file.write(result.stdout)

    print("Return Code:", result.returncode)
    print("Output written to output.txt")

except Exception as e:
    print("Error running the command:", e)