import re

# Define the licenses we are interested in
target_licenses = ["mech_2", "anshpc_pack", "preppost", "ansys"]

# Initialize a dictionary to store license information
license_data = {license: {"issued": 0, "used": 0, "users": []} for license in target_licenses}

# Open the output file to read
with open("./output.txt", "r") as infile:
    current_license = None
    for line in infile:
        # regX expression to match line from output
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
with open("./filtered_output.txt", "w") as outfile:
    for lic, data in license_data.items():
        outfile.write(f"License: {lic}\n")
        outfile.write(f"  Total Issued: {data['issued']}\n")
        outfile.write(f"  Total Used: {data['used']}\n")
        outfile.write("  Users:\n")
        for user in data["users"]:
            outfile.write(f"    {user}\n")
        outfile.write("\n")

print("Filtered output has been saved to 'filtered_output.txt'")
