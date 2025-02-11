import sqlite3
import re
import os

# Database setup
db_file = "./database/licenses.db"
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

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

with open(OUTPUT_FILE, "r") as infile:
    current_license = None
    for line in infile:
        print(f"Processing line: {line.strip()}")

        match = re.match(r"Users of (\S+):\s*\(Total of (\d+)\s*licenses? issued;\s*Total of (\d+)\s*licenses? in use\)", line)

        if match:
            lic_name, issued, used = match.groups()
            if lic_name in target_licenses:
                current_license = lic_name
                license_data[lic_name]["issued"] = int(issued)
                license_data[lic_name]["used"] = int(used)
            else:
                current_license = None

        if current_license and "start" in line.lower():
            user_info = line.strip()
            license_data[current_license]["users"].append(user_info)

with open(FILTERED_OUTPUT_FILE, "w") as outfile:
    for lic, data in license_data.items():
        outfile.write(f"License: {lic}\n")
        outfile.write(f"  Total Issued: {data['issued']}\n")
        outfile.write(f"  Total Used: {data['used']}\n")
        outfile.write("  Users:\n")
        for user in data["users"]:
            outfile.write(f"    {user}\n")
        outfile.write("\n")

print("Filtered output has been saved to 'filtered_output.txt'")

# Close the database connection
conn.close()