import tkinter as tk
from tkinter import ttk, messagebox
from ttkbootstrap import Style
import subprocess
import os
from datetime import datetime

# Paths for scripts and configuration
GET_LICENSE_SCRIPT = "getLicenseStatus.py"
FILTER_LICENSE_SCRIPT = "filterLicense.py"
FILTERED_OUTPUT_FILE = "filtered_output.txt"
LICENSE_FILE = "./additionalInfo/licenses.txt"
SERVER_FILE = "./additionalInfo/servers.txt"

# Ensure additionalInfo directory exists
os.makedirs("./additionalInfo", exist_ok=True)


def run_refresh_sequence():
    """
    Runs the entire refresh sequence: get license status, filter, and display.
    """
    try:
        # Run getLicenseStatus script
        result = subprocess.run(["python", GET_LICENSE_SCRIPT], capture_output=True, text=True)
        if result.returncode != 0:
            messagebox.showerror("Error", f"Error running '{GET_LICENSE_SCRIPT}':\n{result.stderr}")
            return

        # Run filterLicense script
        result = subprocess.run(["python", FILTER_LICENSE_SCRIPT], capture_output=True, text=True)
        if result.returncode != 0:
            messagebox.showerror("Error", f"Error running '{FILTER_LICENSE_SCRIPT}':\n{result.stderr}")
            return

        # Display the filtered output
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

        # Clear the previous data in the treeviews
        for item in available_tree.get_children():
            available_tree.delete(item)
        for item in full_tree.get_children():
            full_tree.delete(item)

        # Parse and display the licenses
        license_data = parse_filtered_output(output_content)
        for lic, data in license_data.items():
            issued = data["issued"]
            used = data["used"]
            status = "Available" if used < issued else "Fully Used"
            color_tag = "green" if used < issued else "red"

            # Insert into the respective tree based on status
            target_tree = available_tree if status == "Available" else full_tree
            parent = target_tree.insert("", "end", values=(lic, f"{used}/{issued}", status), tags=(color_tag,))

            # Add users as expandable children
            for user in data["users"]:
                target_tree.insert(parent, "end", values=("", user, ""))

        # Style tags for green and red indicators
        available_tree.tag_configure("green", foreground="green")
        full_tree.tag_configure("red", foreground="red")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to display output: {e}")


def parse_filtered_output(lines):
    """
    Parse the lines from the filtered output to extract license data.
    """
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


def update_timestamp():
    """
    Update the timestamp label to show the last refresh time.
    """
    timestamp_label.config(text=f"Last Refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def load_entries(file_path):
    """
    Load entries from the specified file.
    """
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            return [line.strip() for line in file if line.strip()]
    return []


def save_entries(file_path, entries):
    """
    Save entries back to the specified file.
    """
    with open(file_path, "w") as file:
        file.write("\n".join(entries) + "\n")


def add_license():
    """
    Add a new license to the list and update the file.
    """
    license_name = license_entry.get().strip()
    if license_name:
        licenses = load_entries(LICENSE_FILE)
        if license_name not in licenses:
            licenses.append(license_name)
            save_entries(LICENSE_FILE, licenses)
            load_license_table()
        license_entry.delete(0, tk.END)
    else:
        messagebox.showerror("Error", "Please enter a valid license name.")


def add_server():
    """
    Add a new server to the list and update the file.
    """
    server_data = server_entry.get().strip()
    if server_data:
        servers = load_entries(SERVER_FILE)
        if server_data not in servers:
            servers.append(server_data)
            save_entries(SERVER_FILE, servers)
            load_server_table()
        server_entry.delete(0, tk.END)
    else:
        messagebox.showerror("Error", "Please enter a valid server address.")


def delete_license():
    """
    Delete selected licenses from the file and GUI.
    """
    selected_items = [license_table.item(item)["values"][0] for item in license_table.selection()]
    if selected_items:
        licenses = load_entries(LICENSE_FILE)
        for item in selected_items:
            if item in licenses:
                licenses.remove(item)
        save_entries(LICENSE_FILE, licenses)
        load_license_table()


def delete_server():
    """
    Delete selected servers from the file and GUI.
    """
    selected_items = [server_table.item(item)["values"][0] for item in server_table.selection()]
    if selected_items:
        servers = load_entries(SERVER_FILE)
        for item in selected_items:
            servers = [s for s in servers if s.lstrip("#") != item]
        save_entries(SERVER_FILE, servers)
        load_server_table()


def load_license_table():
    """
    Load licenses into the table.
    """
    for item in license_table.get_children():
        license_table.delete(item)
    licenses = load_entries(LICENSE_FILE)
    for lic in licenses:
        license_table.insert("", "end", values=(lic,))


def load_server_table():
    """
    Load servers into the table.
    """
    for item in server_table.get_children():
        server_table.delete(item)
    servers = load_entries(SERVER_FILE)
    for server in servers:
        active = "Active" if not server.startswith("#") else "Inactive"
        server_name = server.lstrip("#")
        server_table.insert("", "end", values=(server_name, active))

# Remove newline artifacts from license names if any are present
def sanitize_license_name(license_name):
    return license_name.replace("\n", "").strip()

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
root.geometry("700x750")

notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True)

# Main Tab
main_frame = ttk.Frame(notebook, padding=10)
notebook.add(main_frame, text="License Monitor")

refresh_button = ttk.Button(main_frame, text="Refresh", command=run_refresh_sequence)
refresh_button.pack(pady=5)

# Timestamp label
timestamp_label = ttk.Label(main_frame, text="")
timestamp_label.pack(pady=5)


# Treeview for Available Licenses
available_label = ttk.Label(main_frame, text="Available Licenses")
available_label.pack(anchor=tk.W)

available_tree = ttk.Treeview(main_frame, columns=("License Name", "Usage", "Status"), show="headings")
for col in ("License Name", "Usage", "Status"):
    anchor_value = tk.W if col == "License Name" else tk.CENTER
    available_tree.heading(col, text=col, anchor=anchor_value)
    available_tree.column(col, anchor=anchor_value, width=200)
available_tree.pack(fill=tk.BOTH, expand=True, pady=5)

# Treeview for Fully Used Licenses
full_label = ttk.Label(main_frame, text="Fully Used Licenses")
full_label.pack(anchor=tk.W)

full_tree = ttk.Treeview(main_frame, columns=("License Name", "Usage", "Status"), show="headings")
for col in ("License Name", "Usage", "Status"):
    anchor_value = tk.W if col == "License Name" else tk.CENTER
    full_tree.heading(col, text=col, anchor=anchor_value)
    full_tree.column(col, anchor=anchor_value)
full_tree.pack(fill=tk.BOTH, expand=True, pady=5)

# Tab for managing licenses
license_frame = ttk.Frame(notebook, padding=10)
notebook.add(license_frame, text="Manage Licenses")

license_entry = ttk.Entry(license_frame)
license_entry.pack(pady=5)
add_license_button = ttk.Button(license_frame, text="Add License", command=add_license)
add_license_button.pack(pady=5)

license_table = ttk.Treeview(license_frame, columns=("License"), show="headings")
license_table.heading("License", text="License", anchor="w")
license_table.pack(fill=tk.BOTH, expand=True, pady=5)


delete_license_button = ttk.Button(license_frame, text="Delete Selected License", command=delete_license)
delete_license_button.pack(pady=5)

load_license_table()

# Tab for managing servers
server_frame = ttk.Frame(notebook, padding=10)
notebook.add(server_frame, text="Manage Servers")

server_entry = ttk.Entry(server_frame)
server_entry.pack(pady=5)

add_server_button = ttk.Button(server_frame, text="Add Server", command=add_server)
add_server_button.pack(pady=5)

server_table = ttk.Treeview(server_frame, columns=("Server", "Status"), show="headings")
server_table.heading("Server", text="Server", anchor="w")
server_table.heading("Status", text="Status")
server_table.pack(fill=tk.BOTH, expand=True, pady=5)

delete_server_button = ttk.Button(server_frame, text="Delete Selected Server", command=delete_server)
delete_server_button.pack(pady=5)

load_server_table()

root.mainloop()