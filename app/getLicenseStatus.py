import subprocess

# Properly formatted PowerShell command
command = r'& "C:\Program Files\ANSYS Inc\v212\licensingclient\winx64\lmutil.exe" lmstat -c 1055@SRVLICANS02 -a'

# Run the command using PowerShell
result = subprocess.run(["powershell.exe", "-Command", command], capture_output=True, text=True)

# Write the result to a file
with open(".\output.txt", "w") as file:
    file.write(result.stdout)

print("Return Code:", result.returncode)
print("Output written to output.txt")
