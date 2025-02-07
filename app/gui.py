import tkinter as tk
from tkinter import messagebox
import subprocess
import os

# Paths for scripts
GET_LICENSE_SCRIPT = "getLicenseStatus.py"
FILTER_LICENSE_SCRIPT = "filterLicense.py"


def run_script(script_name):
    """
    Run a Python script located in the same folder.
    """
    try:
        result = subprocess.run(["python", script_name], capture_output=True, text=True)
        if result.returncode == 0:
            messagebox.showinfo("Success", f"Script '{script_name}' ran successfully.")
        else:
            messagebox.showerror("Error", f"Error running '{script_name}':\n{result.stderr}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to run script '{script_name}': {e}")


def displayFilteredOutput():
    """
    Display the filtered output in the text widget.
    """
    filtered_output_file = "filtered_output.txt"
    try:
        if not os.path.exists(filtered_output_file):
            messagebox.showerror("Error", "Filtered output file not found. Run the filter script first.")
            return

        with open(filtered_output_file, "r") as file:
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

# Buttons
run_command_button = tk.Button(frame, text="Run License Status Script", command=lambda: run_script(GET_LICENSE_SCRIPT))
run_command_button.grid(row=0, column=0, padx=5, pady=5)

filter_button = tk.Button(frame, text="Run Filter Script", command=lambda: run_script(FILTER_LICENSE_SCRIPT))
filter_button.grid(row=0, column=1, padx=5, pady=5)

show_output_button = tk.Button(frame, text="Show Filtered Output", command=displayFilteredOutput)
show_output_button.grid(row=0, column=2, padx=5, pady=5)

# Text widget to display filtered output
text_widget = tk.Text(frame, wrap=tk.WORD, height=20, width=80)
text_widget.grid(row=1, column=0, columnspan=3, pady=10)

root.mainloop()
