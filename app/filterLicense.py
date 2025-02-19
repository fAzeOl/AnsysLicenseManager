import sqlite3
import re
import os
from datetime import datetime

def convert_to_sqlite_datetime(start_time_str):
    try:
        return datetime.strptime(start_time_str, "%m/%d %H:%M").strftime("%m-%d %H:%M:%S")
    except ValueError:
        return start_time_str

def get_correct_year(start_date):
    return datetime.now().year

def convert_decimal_hours_to_hm(decimal_hours):
    hours = int(decimal_hours)
    minutes = round((decimal_hours - hours) * 60)
    return f"{hours}h {minutes}m"

def setup_database(db_file):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
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
    cursor.execute("DELETE FROM temp_data")
    conn.commit()
    return conn, cursor

def load_target_licenses(cursor):
    cursor.execute("SELECT License FROM License")
    return [row[0] for row in cursor.fetchall()]

def parse_output_file(output_file, target_licenses):
    if not os.path.exists(output_file):
        print(f"Error: '{output_file}' not found.")
        exit(1)
    
    license_data = {lic: {"issued": 0, "used": 0, "users": []} for lic in target_licenses}
    license_header_pattern = re.compile(r"Users of (\S+):\s*\(Total of (\d+)\s*licenses? issued;\s*Total of (\d+)\s*licenses? in use\)")
    user_pattern = re.compile(
        r"(\S+)\s+(\S+)\s+(\S+)\s+(\d+)\s+\((v\d+\.\d+)\)\s+\(([^)]+)\), start (\S+) (\d+/\d+) (\d+:\d+)"
    )
    
    with open(output_file, "r") as infile:
        current_license = None
        for line in infile:
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
                    user, hostname, display, pid, version, server, start_day, start_date, start_time = user_match.groups()
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
    return license_data

def insert_into_database(cursor, conn, license_data):
    for lic, data in license_data.items():
        for user in data["users"]:
            try:
                year = get_correct_year(user["Start_date"])
                start_dt = datetime.strptime(f"{year}/{user['Start_date']} {user['Start_time']}", "%Y/%m/%d %H:%M")
                duration_hours = convert_decimal_hours_to_hm((datetime.now() - start_dt).total_seconds() / 3600)
            except ValueError:
                duration_hours = None

            cursor.execute('''INSERT INTO temp_data (License, User, Hostname, Display, PID, Version, Server, Start_day, Start_date, Start_time, Duration_Hours)
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                           (lic, user["User"], user["Hostname"], user["Display"], user["PID"], user["Version"], user["Server"], user["Start_day"], user["Start_date"], user["Start_time"], duration_hours))
    conn.commit()

def save_filtered_output(filtered_output_file, license_data):
    with open(filtered_output_file, "w") as outfile:
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

def main():
    db_file = "./database/licenses.db"
    output_file = "./output/output.txt"
    filtered_output_file = "./output/filtered_output.txt"
    
    conn, cursor = setup_database(db_file)
    target_licenses = load_target_licenses(cursor)
    if not target_licenses:
        print("No target licenses specified. Please add licenses to the database.")
        exit(1)
    
    license_data = parse_output_file(output_file, target_licenses)
    insert_into_database(cursor, conn, license_data)
    save_filtered_output(filtered_output_file, license_data)
    
    #print("Filtered output has been saved to 'filtered_output.txt'")
    conn.close()

if __name__ == "__main__":
    main()
