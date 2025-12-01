🚀 ThinkPad Ultimate Command Center (Fan & Battery Control)
This application is a comprehensive system management tool written in Python, designed to override the aggressive thermal management policies and limited battery settings often found in modern Lenovo ThinkPad E-series (E15 Gen 2 and similar) laptops.

Our Goal: To grant the user absolute control over the laptop's thermal and power hardware.

✨ Core Features
Aggressive Persistence Loop: Utilizes a "Stubborn Mode" to continuously override the BIOS, ensuring the fan speed remains locked at your desired level (Levels 1-7 or Turbo).

Full Manual Fan Control: Direct access to fan speed levels 1 (Silent) through 7 (Performance), plus the extreme TURBO JET mode (0x40).

Precision Battery Limiter: Allows setting custom Start and Stop charge thresholds to preserve battery health (writes directly to EC registers 0xB0/0xB1).

Deep Battery Health Stats: Reads precise Cycle Count and Wear Level (%) by parsing the authoritative Windows PowerCfg /BatteryReport.

System Monitoring (Dashboard): Provides real-time tracking of CPU, RAM, and Disk usage via live progress bars.

Global Hotkeys: Control fan modes instantly within games or other full-screen applications using global keyboard shortcuts (Ctrl + Alt + 1/2/3).

User Experience: Features a modern, clean (CustomTkinter) Dark Mode interface and dual TR/EN language support.

⚠️ The Critical Problem Solved (EC/BIOS Conflict)
The core difficulty in this project was bypassing the proprietary Embedded Controller (EC) chip. The application successfully overcomes the most common hardware failure points:

EC "Busy" Flag (128 Error): The EC often sends an error signal (128 or 0x80) when simultaneously asked for temperature and write commands. Our current solution prevents this by stabilizing the hardware channel.

BIOS Watchdog: The application defeats the BIOS's attempt to reset manual fan speeds (the constant cutting out of fan power) by implementing an aggressive, repeating command loop.

🛠️ Installation and Usage
1. Requirements
The application requires the inpoutx64.dll driver for low-level hardware access.

2. Run as Administrator (Mandatory)
The application must be run with Administrator privileges to execute hardware-level commands (Port I/O).

3. Usage
Fan Control: Use the buttons on the FAN CONTROL tab, or use the global hotkeys for immediate control.

Battery Thresholds: Go to the BATTERY tab, adjust the sliders, and click "APPLY SETTINGS". (Settings persist across reboots).

VIRUS TOTAL TEST LINK: https://www.virustotal.com/gui/file/b2bfabeaf524a8e42a84323ce1cd6abb74d5c3a3fc31ad595ace52b94ccfe539/detection

🛑 Hardware Safety Disclaimer
This utility performs direct low-level hardware manipulation on your laptop's Embedded Controller. Use at your own risk. Although the application is designed to revert to the safe BIOS/Automatic mode upon exit, incorrect use of the lowest speeds without external thermal monitoring could potentially damage hardware.
