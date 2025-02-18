import sqlite3
import re
import os
from datetime import datetime

def convert_to_sqlite_datetime(start_time_str):
    try:
        return datetime.strptime(start_time_str, "%m/%d %H:%M").strftime("%m-%d %H:%M:%S")
    except ValueError:
        return start_time_str  # If parsing fails, return the original

def get_correct_year(start_date):
    """
    Determines the correct year for the given start_date (MM/DD).
    - If start_date matches today's month and day -> use current year.
    - If start_date is in the past, check if it's before or on 12/31:
      - If yes, use last year.
      - Otherwise, use the current year.
    """
    return datetime.now().year

def convert_decimal_hours_to_hm(decimal_hours):
    hours = int(decimal_hours)  # Get the whole number part (hours)
    minutes = round((decimal_hours - hours) * 60)  # Convert the fractional part to minutes
    return hours, minutes

# Database setup
db_file = "./database/licenses.db"
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

#cursor.execute("DROP TABLE IF EXISTS temp_data")
#conn.commit()

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
        Start_day TEXT,
        Start_date TEXT,
        Start_time TEXT,
        Duration_Hours TEXT
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
    r"(\S+)\s+(\S+)\s+(\S+)\s+(\d+)\s+\((v\d+\.\d+)\)\s+\(([^)]+)\), start (\S+) (\d+/\d+) (\d+:\d+)"
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
            continue  # Move to next line after processing license header

        # Process user data only if a valid license is being tracked
        if current_license:
            user_match = user_pattern.match(line.strip())
            if user_match:
                user, hostname, display, pid, version, server, start_day, start_date, start_time = user_match.groups()

                # Store data in license_data dictionary
                license_data[current_license]["users"].append({
                    "User": user,
                    "Hostname": hostname,
                    "Display": display,
                    "PID": pid,
                    "Version": version,
                    "Server": server,
                    "Start_day": start_day,
                    "Start_date": start_date,
                    "Start_time": start_time,
                })

                print(license_data[current_license]["users"])    

                # Convert start_date and start_time to a full datetime object for duration calculation
                try:
                    # Get the correct year for the start_date
                    year = get_correct_year(start_date)

                    # Convert start_date and start_time into a full datetime object
                    start_dt = datetime.strptime(f"{year}/{start_date} {start_time}", "%Y/%m/%d %H:%M")

                    # Calculate duration in hours
                    duration_hours_raw = (datetime.now() - start_dt).total_seconds() / 3600
                    hours, minutes = convert_decimal_hours_to_hm(duration_hours_raw)

                    duration_hours = f"{hours}h {minutes}m"

                    print(year, start_dt, duration_hours, datetime.now())
                except ValueError:
                    duration_hours = None  # Handle unexpected date format gracefully

                # Insert into database
                cursor.execute('''INSERT INTO temp_data (License, User, Hostname, Display, PID, Version, Server, Start_day, Start_date, Start_time, Duration_Hours)
                                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                               (current_license, user, hostname, display, pid, version, server, start_day, start_date, start_time, duration_hours))
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
            outfile.write(f"    Start Day: {user['Start_day']}\n")
            outfile.write(f"    Start Date: {user['Start_date']}\n")
            outfile.write(f"    Start Time: {user['Start_time']}\n")
            outfile.write("\n")


print("Filtered output has been saved to 'filtered_output.txt'")

# Close the database connection
conn.close()
