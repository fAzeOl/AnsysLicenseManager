import sqlite3
import re
import os
from datetime import datetime

def convert_to_sqlite_datetime(start_time_str):
    try:
        return datetime.strptime(start_time_str, "%m/%d %H:%M").strftime("%m-%d %H:%M:%S")
    except ValueError:
        return start_time_str  # If parsing fails, return the original

# Database setup
db_file = "./database/licenses.db"
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# Create temp_data table if not exists
cursor.execute('''
    CREATE TABLE IF NOT EXISTS temp_data (
        License TEXT,
        User TEXT,
        Hostname TEXT,
        Display TEXT,
        PID INTEGER,
        Version TEXT,
        Server TEXT,
        Start TEXT,
        Duration_Hours REAL
    )
''')
conn.commit()

# Clear existing data in temp_data before inserting new records
cursor.execute("DELETE FROM temp_data")
conn.commit()

folderPath = "./output"
if not os.path.exists(folderPath):
    os.mkdir(folderPath)

OUTPUT_FILE = f"{folderPath}/output.txt"
FILTERED_OUTPUT_FILE = f"{folderPath}/filtered_output.txt"

# Initialize a dictionary to store license information
cursor.execute("SELECT License FROM License")
target_licenses = [row[0] for row in cursor.fetchall()]

if not target_licenses:
    print("No target licenses specified. Please add licenses to the database.")
    exit(1)

license_data = {license: {"issued": 0, "used": 0, "users": []} for license in target_licenses}

if not os.path.exists(OUTPUT_FILE):
    print(f"Error: '{OUTPUT_FILE}' not found.")
    exit(1)

# Regex patterns
license_header_pattern = re.compile(r"Users of (\S+):\s*\(Total of (\d+)\s*licenses? issued;\s*Total of (\d+)\s*licenses? in use\)")
user_pattern = re.compile(
    r"(\S+)\s+(\S+)\s+(\S+)\s+(\d+)\s+\((v\d+\.\d+)\)\s+\(([^)]+)\), start (.+)"
)


with open(OUTPUT_FILE, "r") as infile:
    current_license = None
    for line in infile:
        print(f"Processing line: {line.strip()}")

        match = license_header_pattern.match(line)
        if match:
            lic_name, issued, used = match.groups()
            if lic_name in target_licenses:
                current_license = lic_name
                license_data[lic_name]["issued"] = int(issued)
                license_data[lic_name]["used"] = int(used)
            else:
                current_license = None
            continue

        if current_license:
            user_match = user_pattern.match(line.strip())
            if user_match:
                user, hostname, display, pid, version, server, start_time = user_match.groups()
                formatted_start_time = convert_to_sqlite_datetime(start_time)
                license_data[current_license]["users"].append({
                    "User": user,
                    "Hostname": hostname,
                    "Display": display,
                    "PID": pid,
                    "Version": version,
                    "Server": server,
                    "Start": formatted_start_time,
                })

                try:
                    start_dt = datetime.strptime(formatted_start_time, "%Y-%m-%d %H:%M:%S")
                    duration_hours = (datetime.now() - start_dt).total_seconds() / 3600
                except ValueError:
                    duration_hours = None  # Handle unexpected date format gracefully
                
                # Insert into database
                cursor.execute('''INSERT INTO temp_data (License, User, Hostname, Display, PID, Version, Server, Start, Duration_Hours)
                                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                               (current_license, user, hostname, display, pid, version, server, formatted_start_time, duration_hours))
                conn.commit()

with open(FILTERED_OUTPUT_FILE, "w") as outfile:
    for lic, data in license_data.items():
        outfile.write(f"License: {lic}\n")
        outfile.write(f"  Total Issued: {data['issued']}\n")
        outfile.write(f"  Total Used: {data['used']}\n")
        outfile.write("  Users:\n")
        for user in data["users"]:
            outfile.write(f"    User: {user['User']}\n")
            outfile.write(f"    Hostname: {user['Hostname']}\n")
            outfile.write(f"    Display: {user['Display']}\n")
            outfile.write(f"    PID: {user['PID']}\n")
            outfile.write(f"    Version: {user['Version']}\n")
            outfile.write(f"    Server: {user['Server']}\n")
            outfile.write(f"    Start: {user['Start']}\n")
            outfile.write("\n")

print("Filtered output has been saved to 'filtered_output.txt'")

# Close the database connection
conn.close()
