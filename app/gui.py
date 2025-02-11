import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from ttkbootstrap import Style
import subprocess
import os
from datetime import datetime

# Database setup
folderPath = "./database"
if not os.path.exists(folderPath):
    os.mkdir(folderPath)

db_file = "./database/licenses.db"
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# Create the License table if it doesn't exist
cursor.execute(''' 
    CREATE TABLE IF NOT EXISTS License (
        License TEXT PRIMARY KEY,
        Name TEXT NOT NULL
    )
''')

# Create the Server table if it doesn't exist
cursor.execute(''' 
    CREATE TABLE IF NOT EXISTS Server (
        Server TEXT PRIMARY KEY,
        Status TEXT NOT NULL
    )
''')

# Create the User table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS User (
        UserName TEXT PRIMARY KEY,
        Status TEXT NOT NULL
    )
''')

conn.commit()

# Paths for scripts
folderOutput = "./output"
GET_LICENSE_SCRIPT = "getLicenseStatus.py"
FILTER_LICENSE_SCRIPT = "filterLicense.py"
FILTERED_OUTPUT_FILE = f"{folderOutput}/filtered_output.txt"

# GUI Functions
def run_refresh_sequence():
    """
    Runs the entire refresh sequence: get license status, filter, and display.
    """
    try:
        result = subprocess.run(["python", GET_LICENSE_SCRIPT], capture_output=True, text=True)
        if result.returncode != 0:
            messagebox.showerror("Error", f"Error running '{GET_LICENSE_SCRIPT}':\n{result.stderr}")
            return

        result = subprocess.run(["python", FILTER_LICENSE_SCRIPT], capture_output=True, text=True)
        if result.returncode != 0:
            messagebox.showerror("Error", f"Error running '{FILTER_LICENSE_SCRIPT}':\n{result.stderr}")
            return

        display_filtered_output()
        update_timestamp()

    except Exception as e:
        messagebox.showerror("Error", f"Failed to refresh: {e}")


def display_filtered_output():
    """
    Display the filtered output in the GUI.
    """
    try:
        if not os.path.exists(FILTERED_OUTPUT_FILE):
            messagebox.showerror("Error", "Filtered output file not found. Please try refreshing.")
            return

        with open(FILTERED_OUTPUT_FILE, "r") as file:
            output_content = file.readlines()

        for item in available_tree.get_children():
            available_tree.delete(item)
        for item in full_tree.get_children():
            full_tree.delete(item)
        for item in user_tree.get_children():
            user_tree.delete(item)

        license_data = parse_filtered_output(output_content)
        active_users = get_active_users()

        for lic, data in license_data.items():
            issued = data["issued"]
            used = data["used"]
            status = "Available" if used < issued else "Fully Used"
            color_tag = "green" if used < issued else "red"
            target_tree = available_tree if status == "Available" else full_tree
            parent = target_tree.insert("", "end", values=(lic, f"{used}/{issued}", status), tags=(color_tag,))

            for user in data["users"]:
                target_tree.insert(parent, "end", values=("", user, ""))

                if user in active_users:
                    user_tree.insert("", "end", values=(user, lic))

        available_tree.tag_configure("green", foreground="green")
        full_tree.tag_configure("red", foreground="red")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to display output: {e}")


def parse_filtered_output(lines):
    license_data = {}
    current_license = None
    for line in lines:
        line = line.strip()
        if line.startswith("License:"):
            parts = line.split(": ")
            if len(parts) == 2:
                current_license = parts[1]
                license_data[current_license] = {"issued": 0, "used": 0, "users": []}
        elif "Total Issued:" in line:
            license_data[current_license]["issued"] = int(line.split(": ")[1])
        elif "Total Used:" in line:
            license_data[current_license]["used"] = int(line.split(": ")[1])
        elif line.startswith("Users:"):
            continue
        elif current_license and line:
            license_data[current_license]["users"].append(line)
    return license_data


def get_active_users():
    """
    Retrieve the list of active users from the database.
    """
    cursor.execute("SELECT UserName FROM User WHERE Status = 'Active'")
    return [row[0] for row in cursor.fetchall()]


def update_timestamp():
    timestamp_label.config(text=f"Last Refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def load_user_table():
    cursor.execute("SELECT UserName, Status FROM User")
    for user, status in cursor.fetchall():
        user_table.insert("", "end", values=(user, status))


def load_license_table():
    for item in license_table.get_children():
        license_table.delete(item)
    cursor.execute("SELECT License, Name FROM License")
    for lic, name in cursor.fetchall():
        license_table.insert("", "end", values=(lic, name))


def load_server_table():
    for item in server_table.get_children():
        server_table.delete(item)
    cursor.execute("SELECT Server, Status FROM Server")
    for server, status in cursor.fetchall():
        server_table.insert("", "end", values=(server, status))


def add_user():
    user_name = user_entry.get().strip()

    if not user_name:
        messagebox.showerror("Error", "Please enter a User Name.")
        return

    try:
        cursor.execute("INSERT INTO User (UserName, Status) VALUES (?, ?)", (user_name, "Active"))
        conn.commit()
        load_user_table()
        user_entry.delete(0, tk.END)
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "User already exists.")


def add_license():
    license_name = license_entry.get().strip()
    license_owner = name_entry.get().strip()

    if not license_name or not license_owner:
        messagebox.showerror("Error", "Please enter both License and Name.")
        return

    try:
        cursor.execute("INSERT INTO License (License, Name) VALUES (?, ?)", (license_name, license_owner))
        conn.commit()
        load_license_table()
        license_entry.delete(0, tk.END)
        name_entry.delete(0, tk.END)
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "License already exists.")


def add_server():
    server_name = server_entry.get().strip()

    if not server_name:
        messagebox.showerror("Error", "Please enter a Server.")
        return

    try:
        server_status = "Active"
        cursor.execute("UPDATE Server SET Status = 'Inactive'")
        cursor.execute("INSERT OR REPLACE INTO Server (Server, Status) VALUES (?, ?)", (server_name, server_status))
        conn.commit()
        load_server_table()
        server_entry.delete(0, tk.END)
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Server already exists.")


def delete_user():
    selected_items = [user_table.item(item)["values"][0] for item in user_table.selection()]
    if selected_items:
        for user in selected_items:
            cursor.execute("DELETE FROM User WHERE UserName = ?", (user,))
        conn.commit()
        load_user_table()


def delete_license():
    selected_items = [license_table.item(item)["values"][0] for item in license_table.selection()]
    if selected_items:
        for license_id in selected_items:
            cursor.execute("DELETE FROM License WHERE License = ?", (license_id,))
        conn.commit()
        load_license_table()


def delete_server():
    selected_items = [server_table.item(item)["values"][0] for item in server_table.selection()]
    if selected_items:
        for server_id in selected_items:
            cursor.execute("DELETE FROM Server WHERE Server = ?", (server_id,))
        conn.commit()
        load_server_table()

def update_server():
    selected_items = [server_table.item(item)["values"][0] for item in server_table.selection()]
    if len(selected_items) > 1:
        messagebox.showerror("Error", "Please select only 1 server.")
        return
    if selected_items:
        cursor.execute("UPDATE Server SET Status = 'Inactive'")
        cursor.execute("UPDATE Server SET Status = 'Active' WHERE Server = ?", (selected_items[0],))
        conn.commit()
        load_server_table()


# GUI Setup with ttkbootstrap
style = Style("darkly")
style.configure("TLabel", font=("Arial", 12))
style.configure("TButton", font=("Arial", 12))
style.configure("Treeview", font=("Arial", 12))
style.configure("Treeview.Heading", font=("Arial", 12, "bold"))
style.configure("Treeview", rowheight=25)
style.configure("TNotebook.Tab", font=("Arial", 12))
root = style.master
root.title("License Monitor GUI")
root.geometry("800x750")

notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True)

main_frame = ttk.Frame(notebook, padding=10)
notebook.add(main_frame, text="License Monitor")

refresh_button = ttk.Button(main_frame, text="Refresh", command=run_refresh_sequence)
refresh_button.pack(pady=5)

timestamp_label = ttk.Label(main_frame, text="")
timestamp_label.pack(pady=5)

user_label = ttk.Label(main_frame, text="User's Licenses",)
user_label.pack(anchor=tk.W)

user_tree = ttk.Treeview(main_frame, columns=("User", "License Name"), show="headings", height=1.1)
for col in ("User", "License Name"):
    user_tree.heading(col, text=col, anchor=tk.W)
    user_tree.column(col, anchor=tk.W, width=250)
user_tree.pack(fill=tk.BOTH, expand=True, pady=5)

available_label = ttk.Label(main_frame, text="Available Licenses")
available_label.pack(anchor=tk.W)

available_tree = ttk.Treeview(main_frame, columns=("License Name", "Usage", "Status"), show="headings", height=1)
for col in ("License Name", "Usage", "Status"):
    anchor_value = tk.W if col == "License Name" else tk.CENTER
    available_tree.heading(col, text=col, anchor=anchor_value)
    available_tree.column(col, anchor=anchor_value, width=200)
available_tree.pack(fill=tk.BOTH, expand=True, pady=5)


full_label = ttk.Label(main_frame, text="Fully Used Licenses")
full_label.pack(anchor=tk.W)

full_tree = ttk.Treeview(main_frame, columns=("License Name", "Usage", "Status"), show="headings", height=1)
for col in ("License Name", "Usage", "Status"):
    anchor_value = tk.W if col == "License Name" else tk.CENTER
    full_tree.heading(col, text=col, anchor=anchor_value)
    full_tree.column(col, anchor=anchor_value)
full_tree.pack(fill=tk.BOTH, expand=True, pady=5)

license_frame = ttk.Frame(notebook, padding=10)
notebook.add(license_frame, text="Manage Licenses")

license_entry = ttk.Entry(license_frame)
license_entry.pack(pady=5)
license_entry.insert(0, "Enter License")

name_entry = ttk.Entry(license_frame)
name_entry.pack(pady=5)
name_entry.insert(0, "Enter Name")

add_license_button = ttk.Button(license_frame, text="Add License", command=add_license)
add_license_button.pack(pady=5)

license_table = ttk.Treeview(license_frame, columns=("License", "Name"), show="headings")
license_table.heading("License", text="License", anchor="w")
license_table.heading("Name", text="Name", anchor="w")
license_table.pack(fill=tk.BOTH, expand=True, pady=5)

delete_license_button = ttk.Button(license_frame, text="Delete Selected License", command=delete_license)
delete_license_button.pack(pady=5)

load_license_table()

server_frame = ttk.Frame(notebook, padding=10)
notebook.add(server_frame, text="Manage Servers")

server_entry = ttk.Entry(server_frame)
server_entry.pack(pady=5)
server_entry.insert(0, "Enter Server")

add_server_button = ttk.Button(server_frame, text="Add Server", command=add_server)
add_server_button.pack(pady=5)

server_table = ttk.Treeview(server_frame, columns=("Server", "Status"), show="headings")
server_table.heading("Server", text="Server", anchor="w")
server_table.heading("Status", text="Status", anchor="w")
server_table.pack(fill=tk.BOTH, expand=True, pady=5)

delete_server_button = ttk.Button(server_frame, text="Delete Selected Server", command=delete_server)
delete_server_button.pack(pady=5)

update_server_status = ttk.Button(server_frame, text="Update Server Status", command=update_server)
update_server_status.pack(pady=5)

load_server_table()

user_frame = ttk.Frame(notebook, padding=10)
notebook.add(user_frame, text="Manage Users")

user_entry = ttk.Entry(user_frame)
user_entry.pack(pady=5)
user_entry.insert(0, "Enter User Name")

add_user_button = ttk.Button(user_frame, text="Add User", command=add_user)
add_user_button.pack(pady=5)

user_table = ttk.Treeview(user_frame, columns=("User", "Status"), show="headings")
user_table.heading("User", text="User", anchor="w")
user_table.heading("Status", text="Status", anchor="w")
user_table.pack(fill=tk.BOTH, expand=True, pady=5)

delete_user_button = ttk.Button(user_frame, text="Delete Selected User", command=delete_user)
delete_user_button.pack(pady=5)

load_user_table()

root.mainloop()

# Close the database connection
conn.close()
