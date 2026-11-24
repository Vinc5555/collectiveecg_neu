import csv
#import subprocess
import asyncio
import tkinter as tk
from datetime import datetime

# Function that prompts the user to enter the sensor's ID code
def get_id_from_popup():
    root = tk.Tk()
    root.withdraw()  # Hide the main tkinter window
    popup = tk.Toplevel(root)
    popup.title("Enter Sensor Info")
    popup.geometry("300x150")

    # Sensor Code Label & Entry
    tk.Label(popup, text="Sensor Code:").pack()
    id_entry = tk.Entry(popup)
    id_entry.pack()

    # Optional Text Label & Entry
    tk.Label(popup, text="Optional Filename (leave empty for date):").pack()
    text_entry = tk.Entry(popup)
    text_entry.pack()

    # Variable to store user input
    user_input = {"id_value": None, "optional_text": None}

    # Function to store values and close pop-up
    def submit():
        user_input["id_value"] = id_entry.get().strip()
        user_input["optional_text"] = text_entry.get().strip()
        popup.destroy()  # Close the pop-up

    # Submit Button
    tk.Button(popup, text="Submit", command=submit).pack()
    
    # Wait for user input
    popup.wait_window()

    # If the user didn't enter an optional text, use the current date
    if not user_input["optional_text"]:
        user_input["optional_text"] = datetime.now().strftime("%Y-%m-%d")

    return user_input["id_value"], user_input["optional_text"]
        
# Function that reads the input parameters from csv given the sensor's ID code
# Return the matching row as a dictionary
def read_params_from_csv(csv_filename, id_value):
    with open(csv_filename, mode='r', newline='') as file:
        reader = csv.DictReader(file, delimiter=';')
        for row in reader:
            if row.get('code') == id_value:
                return row
    return None

# Function that runs the collectiveHeart script
async def run_collective_heart(params, optional_text):
    command = [
        "python", "collectiveHeart.py",
        "-sn", params['serialnumber'],
        "-p",  params['port'],
        "-tp", params['triggerport'],
        "-o",  f"{params['code']}_{optional_text}" 
    ]
    print(f"Starting collectiveHeart for sensor {params['code']}")
    # Run the subprocess asynchronously so it doesn't block
    process = await asyncio.create_subprocess_exec(*command)
     # Wait for the process to complete (in the background)
    await process.wait() 

# Main function
async def main():
    csv_filename = "parameters.csv" 
    while True:
        id_value, optional_text = get_id_from_popup()
        if id_value is None:
            print("Process finished by user.")
            break
        
        params = read_params_from_csv(csv_filename, id_value)
        if params:
            asyncio.create_task(run_collective_heart(params, optional_text))
        else:
            print(f"No entry found for code {id_value}")

if __name__ == "__main__":
    asyncio.run(main())
