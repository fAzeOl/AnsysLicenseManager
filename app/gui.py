import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from ttkbootstrap import Style
import subprocess
import os
from datetime import datetime
import filterLicense
import getLicenseStatus


class Database:
    """Handles SQLite database setup, queries, and connection management."""

    def __init__(self):
        """Initializes database connection and ensures necessary tables exist."""
        self.folderPath = "./database"
        self.db_file = "./database/licenses.db"
        self.conn = None
        self.cursor = None
        self.setup_database()

    def setup_database(self):
        """Creates required tables if they do not already exist."""
        if not os.path.exists(self.folderPath):
            os.mkdir(self.folderPath)

        self.conn = sqlite3.connect(self.db_file)
        self.cursor = self.conn.cursor()

        # Create tables if they don't exist
        self.cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS License (
                License TEXT PRIMARY KEY,
                Name TEXT NOT NULL
            )
        ''')

        self.cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS Server (
                Server TEXT PRIMARY KEY,
                Status TEXT NOT NULL
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS User (
                UserName TEXT PRIMARY KEY,
                Status TEXT NOT NULL
            )
        ''')

        self.conn.commit()

    def execute_query(self, query, params=None):
        """Executes a SQL query and returns the fetched results."""
        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)
        return self.cursor.fetchall()

    def commit(self):
        """Commits the current transaction."""
        self.conn.commit()

    def close(self):
        """Closes the database connection."""
        self.conn.close()


class LicenseMonitorApp:
    """Main GUI application to monitor, manage, and track licenses."""

    def __init__(self, root, db):
        """Initializes the GUI and database connection."""
        self.root = root
        self.db = db
        self.style = Style("darkly")
        self.setup_gui()
        self.setup_scripts()

    def setup_scripts(self):
        """Configures output directories and paths for filtered results."""
        self.folderOutput = "./output"
        self.FILTERED_OUTPUT_FILE = f"{self.folderOutput}/filtered_output.txt"

    def setup_gui(self):
        """Configures GUI styles, creates frames, and sets up interface components."""
        self.style.configure("TLabel", font=("Arial", 12))
        self.style.configure("TButton", font=("Arial", 12))
        self.style.configure("Treeview", font=("Arial", 12))
        self.style.configure("Treeview.Heading", font=("Arial", 12, "bold"))
        self.style.configure("Treeview", rowheight=25)
        self.style.configure("TNotebook.Tab", font=("Arial", 12))
        self.root.title("License Monitor GUI")
        self.root.geometry("825x750")

        # Creating the notebook and frames
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.main_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.main_frame, text="License Monitor")

        self.license_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.license_frame, text="Manage Licenses")

        self.server_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.server_frame, text="Manage Servers")

        self.user_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.user_frame, text="Manage Users")

        self.setup_main_frame()
        self.setup_license_frame()
        self.setup_server_frame()
        self.setup_user_frame()

    def setup_main_frame(self):
        """Sets up the main dashboard frame with a refresh button and license tables."""
        # Refresh button
        self.refresh_button = ttk.Button(self.main_frame, text="Refresh", command=self.run_refresh_sequence, width=12)
        self.refresh_button.pack(pady=5)

        self.timestamp_label = ttk.Label(self.main_frame, text="")
        self.timestamp_label.pack(pady=5)

        # Tables for displaying licenses, users, etc.
        self.setup_license_tables()
    
    def on_focus_in(self, event):
        """Clears placeholder text when an entry field gains focus."""
        if event.widget.get() == event.widget.placeholder:
            event.widget.delete(0, tk.END)  # Clear the placeholder text

    def on_focus_out(self, event):
        """Restores placeholder text if an entry field is left empty."""
        if not event.widget.get():  # If empty, restore placeholder
            event.widget.insert(0, event.widget.placeholder)

    def on_tab_switch(self, event):
        """Prevents unwanted focus on entry fields when switching tabs."""
        # Set focus to a different widget
        event.widget.focus()  # Set focus to the frame instead of the entry   

    def copy_license_to_clipboard(self, event, treeview):
        """
        Copies the formatted license information to the clipboard for the selected active user.
        """
        conn = sqlite3.connect('./database/licenses.db') 
        cursor = conn.cursor()  # Create a cursor object to interact with the database

        # Identify the row where the user clicked
        item = treeview.identify_row(event.y)

        if not item:
            self.messagebox.showerror("Error", "No item selected.")
            return

        # Retrieve the item values
        values = treeview.item(item, "values")
        if len(values) < 2:
            self.messagebox.showerror("Error", "Invalid selection.")
            return

        user_name, license_name = values[0], values[1]

        # Query database
        cursor.execute("""
            SELECT User, Hostname, Display, PID, Version, Server, Start_day, Start_date, Start_time
            FROM temp_data
            WHERE User = ? AND License = ?
        """, (user_name, license_name))

        user_data = cursor.fetchone()

        if user_data:
            formatted_text = (
                f"\n{license_name} {user_data[0]} {user_data[1]} {user_data[2]} {user_data[3]} "
                f"({user_data[4]}) ({user_data[5]}), {user_data[6]} {user_data[7]} {user_data[8]}"
            )

            # Copy to clipboard
            self.root.clipboard_clear()
            self.root.clipboard_append(formatted_text)
            self.root.update()

            #print(f"Copied to clipboard: {formatted_text}")  # Debugging purpose    
        else:
            self.messagebox.showerror("Error", "No data found for the selected user/license.")
        
        conn.close()

    def setup_license_tables(self):
        """Set-up dashboard for licenses - User, Available and Fully"""
        self.user_label = ttk.Label(self.main_frame, text="User's Licenses",)
        self.user_label.pack(anchor=tk.W)

        self.user_tree = ttk.Treeview(self.main_frame, columns=("User", "License Name"), show="headings", height=1, selectmode="none")
        self.user_tree.bind("<Shift-1>", lambda event: self.copy_license_to_clipboard(event, self.user_tree))

        for col in ("User", "License Name"):
            self.user_tree.heading(col, text=col, anchor=tk.W)
            self.user_tree.column(col, anchor=tk.W, width=250)
        self.user_tree.pack(fill=tk.BOTH, expand=True, pady=5)

        self.available_label = ttk.Label(self.main_frame, text="Available Licenses")
        self.available_label.pack(anchor=tk.W)

        self.available_tree = ttk.Treeview(self.main_frame, columns=("License Name", "Usage", "Status"), show="headings", height=1, selectmode="none")
        self.available_tree.bind("<Shift-1>", lambda event: self.copy_license_to_clipboard(event, self.available_tree))
        for col in ("License Name", "Usage", "Status"):
            anchor_value = tk.W if col == "License Name" else tk.CENTER
            self.available_tree.heading(col, text=col, anchor=anchor_value)
            self.available_tree.column(col, anchor=anchor_value, width=200)
        self.available_tree.pack(fill=tk.BOTH, expand=True, pady=5)

        self.full_label = ttk.Label(self.main_frame, text="Fully Used Licenses")
        self.full_label.pack(anchor=tk.W)

        self.full_tree = ttk.Treeview(self.main_frame, columns=("License Name", "Usage", "Status"), show="headings", height=1, selectmode="none")
        self.full_tree.bind("<Shift-1>", lambda event: self.copy_license_to_clipboard(event, self.full_tree))
        for col in ("License Name", "Usage", "Status"):
            anchor_value = tk.W if col == "License Name" else tk.CENTER
            self.full_tree.heading(col, text=col, anchor=anchor_value)
            self.full_tree.column(col, anchor=anchor_value)
        self.full_tree.pack(fill=tk.BOTH, expand=True, pady=5)

    def setup_license_frame(self):
        """Set-up tab for managing licenses"""
        # License management GUI
        self.license_entry = ttk.Entry(self.license_frame)
        self.license_entry.pack(pady=5)
        self.license_entry.placeholder = "Enter License"  # Store placeholder text
        self.license_entry.insert(0, self.license_entry.placeholder)
        self.license_entry.bind("<FocusIn>", self.on_focus_in)
        self.license_entry.bind("<FocusOut>", self.on_focus_out)

        self.name_entry = ttk.Entry(self.license_frame)
        self.name_entry.pack(pady=5)
        self.name_entry.placeholder = "Enter License"  # Store placeholder text        
        self.name_entry.insert(0, self.license_entry.placeholder)
        self.name_entry.bind("<FocusIn>", self.on_focus_in)
        self.name_entry.bind("<FocusOut>", self.on_focus_out)

        # Prevent automatic focus on the entry when the tab is switched
        self.license_frame.bind("<Visibility>", self.on_tab_switch)

        self.add_license_button = ttk.Button(self.license_frame, text="Add License", command=self.add_license, width=12)
        self.add_license_button.pack(pady=5)

        self.license_table = ttk.Treeview(self.license_frame, columns=("License", "Name"), show="headings")
        self.license_table.heading("License", text="License", anchor="w")
        self.license_table.heading("Name", text="Name", anchor="w")
        self.license_table.pack(fill=tk.BOTH, expand=True, pady=5)

        self.delete_license_button = ttk.Button(self.license_frame, text="Delete Selected License", command=self.delete_license, width=20)
        self.delete_license_button.pack(pady=5)

        self.load_license_table()

    def setup_server_frame(self):
        """Set-up tab for managing server"""
        # Server management GUI
        self.server_entry = ttk.Entry(self.server_frame)
        self.server_entry.pack(pady=5)
        self.server_entry.placeholder = "Enter Server"  # Store placeholder text
        self.server_entry.insert(0, self.server_entry.placeholder)
        self.server_entry.bind("<FocusIn>", self.on_focus_in)
        self.server_entry.bind("<FocusOut>", self.on_focus_out)        

        self.add_server_button = ttk.Button(self.server_frame, text="Add Server", command=self.add_server, width=12)
        self.add_server_button.pack(pady=5)

        # Prevent automatic focus on the entry when the tab is switched
        self.server_frame.bind("<Visibility>", self.on_tab_switch)

        self.server_table = ttk.Treeview(self.server_frame, columns=("Server", "Status"), show="headings")
        self.server_table.heading("Server", text="Server", anchor="w")
        self.server_table.heading("Status", text="Status", anchor="w")
        self.server_table.pack(fill=tk.BOTH, expand=True, pady=5)

        self.delete_server_button = ttk.Button(self.server_frame, text="Delete Selected Server", command=self.delete_server, width=20)
        self.delete_server_button.pack(pady=5)

        self.update_server_status = ttk.Button(self.server_frame, text="Update Server Status", command=self.update_server, width=20)
        self.update_server_status.pack(pady=5)

        self.load_server_table()

    def setup_user_frame(self):
        """Set-up tab for managing users"""
        # User management GUI
        self.user_entry = ttk.Entry(self.user_frame)
        self.user_entry.pack(pady=5)
        self.user_entry.placeholder = "Enter User Name"
        self.user_entry.insert(0, self.user_entry.placeholder)
        self.user_entry.bind("<FocusIn>", self.on_focus_in)
        self.user_entry.bind("<FocusOut>", self.on_focus_out)         

        self.add_user_button = ttk.Button(self.user_frame, text="Add User", command=self.add_user, width=12)
        self.add_user_button.pack(pady=5)

        # Prevent automatic focus on the entry when the tab is switched
        self.user_frame.bind("<Visibility>", self.on_tab_switch)

        self.user_table = ttk.Treeview(self.user_frame, columns=("User", "Status"), show="headings")
        self.user_table.heading("User", text="User", anchor="w")
        self.user_table.heading("Status", text="Status", anchor="w")
        self.user_table.pack(fill=tk.BOTH, expand=True, pady=5)

        self.delete_user_button = ttk.Button(self.user_frame, text="Delete Selected User", command=self.delete_user, width=20)
        self.delete_user_button.pack(pady=5)

        self.load_user_table()

    def run_refresh_sequence(self):
        """Runs external scripts to refresh license data."""
        try:
            # Run the first script function
            try:
                getLicenseStatus.main()
            except Exception as e:
                messagebox.showerror("Error", f"Error running '{self.GET_LICENSE_SCRIPT}':\n{e}")
                return

            # Run the second script function
            try:
                filterLicense.main()
            except Exception as e:
                messagebox.showerror("Error", f"Error running '{self.FILTER_LICENSE_SCRIPT}':\n{e}")
                return

            # Continue with the refresh sequence
            self.display_filtered_output()
            self.update_timestamp()

        except Exception as e:
            messagebox.showerror("Error", f"Unexpected failure during refresh: {e}")

    def display_filtered_output(self):
        """Displays parsed license data in UI tables."""
        if not os.path.exists(self.FILTERED_OUTPUT_FILE):
            messagebox.showerror("Error", "Filtered output file not found. Please try refreshing.")
            return
    
        with open(self.FILTERED_OUTPUT_FILE, "r") as file:
            output_content = file.readlines()
    
        for item in self.available_tree.get_children():
            self.available_tree.delete(item)
        for item in self.full_tree.get_children():
            self.full_tree.delete(item)
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)
    
        license_data = self.parse_filtered_output(output_content)
        active_users = self.get_active_users()
    
        for lic, data in license_data.items():
            issued = data["issued"]
            used = data["used"]
            status = "Available" if used < issued else "Fully Used"
            color_tag = "green" if used < issued else "red"
            target_tree = self.available_tree if status == "Available" else self.full_tree
            parent = target_tree.insert("", "end", values=(lic, f"{used}/{issued}", status), tags=(color_tag,))

            # Display users associated with each license in the user tree
            for user in data["users"]:
                target_tree.insert(parent, "end", values=(user["User"], f"{user['Start_day']} {user['Start_date']} {user['Start_time']}", user["Duration_Hours"]))
                if user["User"] in active_users:
                    self.user_tree.insert("", "end", values=(user["User"], lic))  # Display user license
    
        self.available_tree.tag_configure("green", foreground="green")
        self.full_tree.tag_configure("red", foreground="red")
    
    
    def parse_filtered_output(self, lines):
        """Parse the filtered data."""
        license_data = {}
        current_license = None
        conn = sqlite3.connect('./database/licenses.db') 
        cursor = conn.cursor()  # Create a cursor object to interact with the database

        licenses_in_output = set()

        for line in lines:
            line = line.strip()
            if line.startswith("License:"):
                parts = line.split(": ")
                if len(parts) == 2:
                    current_license = parts[1]
                    licenses_in_output.add(current_license)
                    if current_license not in license_data:
                        license_data[current_license] = {"issued": 0, "used": 0, "users": []}
            elif "Total Issued:" in line:
                license_data[current_license]["issued"] = int(line.split(": ")[1])
            elif "Total Used:" in line:
                license_data[current_license]["used"] = int(line.split(": ")[1])

        # Query for users per license
        # Fetch the users for this license
        
        for lic in licenses_in_output:
            cursor.execute("""
                SELECT User, Start_day, Start_date, Start_time, Duration_Hours 
                FROM temp_data WHERE License = ?
            """, (lic,))
            users = cursor.fetchall()
        # Append the user information
            for user in users:
                user_info = {
                    "User": user[0],
                    "Start_day": user[1],
                    "Start_date": user[2],
                    "Start_time": user[3],
                    "Duration_Hours": user[4]
                }
                license_data[lic]["users"].append(user_info)  # Append the user info to the license
        conn.close()  # close the connection after done
        return license_data

    def get_active_users(self):
        return [row[0] for row in self.db.execute_query("SELECT UserName FROM User WHERE Status = 'Active'")]

    def update_timestamp(self):
        """Updates the last refresh timestamp label."""
        self.timestamp_label.config(text=f"Last Refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def add_user(self):
        """Adds a new user to the database."""
        user_name = self.user_entry.get().strip()
        if not user_name:
            messagebox.showerror("Error", "Please enter a User Name.")
            return
        try:
            self.db.execute_query("INSERT INTO User (UserName, Status) VALUES (?, ?)", (user_name, "Active"))
            self.db.commit()
            self.load_user_table()
            self.user_entry.delete(0, tk.END)
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "User already exists.")

    def load_user_table(self):
        """Fill in table with user data"""
        for item in self.user_table.get_children(): #erase data after refresh from UI
            self.user_table.delete(item)
        for user, status in self.db.execute_query("SELECT UserName, Status FROM User"):
            self.user_table.insert("", "end", values=(user, status))

    def load_license_table(self):
        """Fill in table with license data"""
        for item in self.license_table.get_children():
            self.license_table.delete(item)
        for lic, name in self.db.execute_query("SELECT License, Name FROM License"):
            self.license_table.insert("", "end", values=(lic, name))

    def load_server_table(self):
        """Fill in table with server data"""
        for item in self.server_table.get_children():
            self.server_table.delete(item)
        for server, status in self.db.execute_query("SELECT Server, Status FROM Server"):
            self.server_table.insert("", "end", values=(server, status))

    def delete_user(self):
        """Deletes the selected user from the database."""
        selected_items = [self.user_table.item(item)["values"][0] for item in self.user_table.selection()]
        if selected_items:
            for user in selected_items:
                self.db.execute_query("DELETE FROM User WHERE UserName = ?", (user,))
            self.db.commit()
            self.load_user_table()

    def delete_license(self):
        selected_items = [self.license_table.item(item)["values"][0] for item in self.license_table.selection()]
        if selected_items:
            for license_id in selected_items:
                self.db.execute_query("DELETE FROM License WHERE License = ?", (license_id,))
            self.db.commit()
            self.load_license_table()

    def delete_server(self):
        selected_items = [self.server_table.item(item)["values"][0] for item in self.server_table.selection()]
        if selected_items:
            for server in selected_items:
                self.db.execute_query("DELETE FROM Server WHERE Server = ?", (server,))
            self.db.commit()
            self.load_server_table()
    
    def add_license(self):
        """Adds a new license to the database."""
        license_id = self.license_entry.get().strip()
        license_name = self.name_entry.get().strip()

        if not license_id or not license_name:
            messagebox.showerror("Error", "Please enter both License ID and Name.")
            return

        try:
            # Insert the new license into the database
            self.db.execute_query("INSERT INTO License (License, Name) VALUES (?, ?)", (license_id, license_name))
            self.db.commit()

            # Reload the license table to display the new license
            self.load_license_table()

            # Clear the input fields
            self.license_entry.delete(0, tk.END)
            self.name_entry.delete(0, tk.END)

        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "License already exists.")
    
    def add_server(self):
        server_name = self.server_entry.get().strip()

        if not server_name:
            messagebox.showerror("Error", "Please enter a Server Name.")
            return

        try:
            # Set the status for the new server
            server_status = "Active"

            # Deactivate any other active servers
            self.db.execute_query("UPDATE Server SET Status = 'Inactive'")
            
            # Insert or update the server in the database
            self.db.execute_query("INSERT OR REPLACE INTO Server (Server, Status) VALUES (?, ?)", (server_name, server_status))
            self.db.commit()

            # Reload the server table to reflect the changes
            self.load_server_table()

            # Clear the input field
            self.server_entry.delete(0, tk.END)

        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Server already exists.")
        
    def update_server(self):
        """Updates the status of the selected server."""
        selected_items = [self.server_table.item(item)["values"][0] for item in self.server_table.selection()]
        
        if len(selected_items) > 1:
            messagebox.showerror("Error", "Please select only 1 server.")
            return

        if selected_items:
            server_name = selected_items[0]

            # Deactivate all servers before updating
            self.db.execute_query("UPDATE Server SET Status = 'Inactive'")

            # Activate the selected server
            self.db.execute_query("UPDATE Server SET Status = 'Active' WHERE Server = ?", (server_name,))
            self.db.commit()

            # Reload the server table to reflect the updated status
            self.load_server_table()


# Main execution block
if __name__ == "__main__":
    root = tk.Tk()
    db = Database()
    app = LicenseMonitorApp(root, db)
    root.mainloop()
