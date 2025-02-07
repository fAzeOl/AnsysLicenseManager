import tkinter as tk
from tkinter import messagebox
import subprocess
import os

# Paths for scripts
GET_LICENSE_SCRIPT = "getLicenseStatus.py"
FILTER_LICENSE_SCRIPT = "filterLicense.py"
FILTERED_OUTPUT_FILE = "filtered_output.txt"


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

    except Exception as e:
        messagebox.showerror("Error", f"Failed to refresh: {e}")


def display_filtered_output():
    """
    Display the filtered output in the text widget.
    """
    try:
        if not os.path.exists(FILTERED_OUTPUT_FILE):
            messagebox.showerror("Error", "Filtered output file not found. Please try refreshing.")
            return

        with open(FILTERED_OUTPUT_FILE, "r") as file:
            output_content = file.read()

        # Clear the text widget before inserting new data
        text_widget.delete(1.0, tk.END)
        text_widget.insert(tk.END, output_content)

    except Exception as e:
        messagebox.showerror("Error", f"Failed to display output: {e}")


# GUI Setup
root = tk.Tk()
root.title("License Monitor GUI")
root.geometry("600x400")

frame = tk.Frame(root, padx=10, pady=10)
frame.pack(fill=tk.BOTH, expand=True)

# Refresh button
refresh_button = tk.Button(frame, text="Refresh", command=run_refresh_sequence)
refresh_button.grid(row=0, column=0, padx=5, pady=5)

# Text widget to display filtered output
text_widget = tk.Text(frame, wrap=tk.WORD, height=20, width=80)
text_widget.grid(row=1, column=0, pady=10)

root.mainloop()
