import re
import os

# Path for license configuration file
LICENSE_FILE = "./additionalInfo/licenses.txt"
OUTPUT_FILE = "./output.txt"
FILTERED_OUTPUT_FILE = "./filtered_output.txt"

# Ensure the additional info directory exists
os.makedirs("./additionalInfo", exist_ok=True)

# Read the licenses from the configuration file
if os.path.exists(LICENSE_FILE):
    with open(LICENSE_FILE, "r") as file:
        target_licenses = [line.strip() for line in file if line.strip()]
else:
    target_licenses = []  # Default to an empty list if the file doesn't exist

if not target_licenses:
    print("No target licenses specified. Please add licenses in './additionalInfo/licenses.txt'")
    exit(1)

# Initialize a dictionary to store license information
license_data = {license: {"issued": 0, "used": 0, "users": []} for license in target_licenses}

# Open the output file to read
if not os.path.exists(OUTPUT_FILE):
    print(f"Error: '{OUTPUT_FILE}' not found.")
    exit(1)

with open(OUTPUT_FILE, "r") as infile:
    current_license = None
    for line in infile:
        # Debug: Print line that doesn't match for better understanding
        print(f"Processing line: {line.strip()}")

        # Updated match pattern with more lenient whitespace handling
        match = re.match(r"Users of (\S+):\s*\(Total of (\d+)\s*licenses? issued;\s*Total of (\d+)\s*licenses? in use\)", line)

        if match:
            lic_name, issued, used = match.groups()
            if lic_name in target_licenses:
                current_license = lic_name
                # Update issued and used count
                license_data[lic_name]["issued"] = int(issued)
                license_data[lic_name]["used"] = int(used)
            else:
                current_license = None  # Reset if it's not a target license
        else:
            print("No match found for this line.")

        # Match user details if within the correct license section
        if current_license and "start" in line.lower():
            user_info = line.strip()
            license_data[current_license]["users"].append(user_info)

# Write the filtered results to a new file
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
