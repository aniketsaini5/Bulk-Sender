from flask import Flask, request, render_template
import pywhatkit as kit
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

app = Flask(__name__)

# Function to send message via WhatsApp
def send_whatsapp_message(number, message):
    try:
        kit.sendwhatmsg_instantly(f"+{number}", message, wait_time=8)
        time.sleep(15)  # Wait for 10 seconds before sending to the next number
    except Exception as e:
        print(f"Error: {e}")

# Load numbers from Excel
def load_numbers_from_excel(file):
    file_extension = file.filename.split('.')[-1]  # Get the file extension
    if file_extension == 'xlsx':
        df = pd.read_excel(file, engine='openpyxl')  # Use 'openpyxl' for .xlsx files
    elif file_extension == 'xls':
        df = pd.read_excel(file, engine='xlrd')  # Use 'xlrd' for .xls files
    else:
        raise ValueError("Unsupported file format. Please upload a .xls or .xlsx file.")
    return df['PhoneNumber'].tolist()

# Load numbers from Google Sheets
def load_numbers_from_google_sheet(sheet_id, sheet_name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("path/to/credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(sheet_id).worksheet(sheet_name)
    data = sheet.get_all_values()
    return [row[0] for row in data[1:]]  # Assuming phone numbers are in the first column

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send', methods=['POST'])
def send_message():
    message = request.form.get('message')
    numbers = []

    # Check if Excel file is uploaded and is not empty
    if 'file' in request.files and request.files['file'].filename != '':
        file = request.files['file']
        numbers += load_numbers_from_excel(file)

    # Check if Google Sheet link is provided
    google_sheet_link = request.form.get('google_sheet_link')
    if google_sheet_link:
        sheet_id, sheet_name = google_sheet_link.split(',')
        numbers += load_numbers_from_google_sheet(sheet_id.strip(), sheet_name.strip())

    # Add manually typed numbers
    manual_numbers = request.form.get('manual_numbers')
    if manual_numbers:
        numbers += manual_numbers.split(',')

    # Send WhatsApp message to each number
    for number in numbers:
        send_whatsapp_message(str(number).strip(), message)  # Convert number to string and strip

    return render_template('index.html', success=True)

if __name__ == '__main__':
    app.run(debug=True)
