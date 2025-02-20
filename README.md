# ANSYS License Monitor GUI 🎛️  

![Python](https://img.shields.io/badge/Python-3.8%2B-blue) ![Tkinter](https://img.shields.io/badge/Tkinter-GUI-orange) ![SQLite](https://img.shields.io/badge/SQLite-Database-green)

## 📌 Overview  

This project started as a side project — a way for me to learn how to integrate an SQLite database into a small application. At the same time, working daily with ANSYS, I found the built-in ANSYS License Manager confusing and cluttered with too much unnecessary data.  

So, I thought — why not combine both? 

The result? A cleaner, more intuitive ANSYS License Monitor that:  

✅ **Filters out unnecessary information**, showing only what’s relevant  
✅ **Clearly visualizes** which licenses are **in use**, **fully occupied**, or **available**  
✅ **Makes it easier for teams** to track license usage and avoid unnecessary delays  

It’s a small but useful tool that helps teams work more efficiently with ANSYS licenses - especially when licenses are limited within the team!

**Note** - The app works with Windows and was tested on ANSYS 2021R2.

## Features  

🔹 **Integrated SQLite Database** – Stores license, user, and server information  
🔹 **Real-time ANSYS License Tracking** – Displays usage in an easy-to-read format  
🔹 **User Identification** – See exactly **who** is using which license  
🔹 **Available vs Fully Used Licenses** – Quickly check which licenses are occupied  
🔹 **Search & Filter Licenses** – No more scrolling through irrelevant data  
🔹 **Clipboard Copying** – Copy license details with a simple **Shift + Click**  
🔹 **Standalone Executable** – Package the tool into a Windows `.exe` with PyInstaller 


## 🏗️ Building a Standalone Application
To generate a Windows executable using PyInstaller, run:

``` 
pyinstaller gui.py --onefile --windowed --name AnsysLicenseMonitor
```
