import re
import sqlite3
DB_FILE = 'local.db'

def extract_residential_id(text):
    words = [word.strip() for word in text.split() if word.strip()]  # Normalize text

    # **Extract English Name** (Last 3 consecutive English words)
    english_name = None
    if "IDENTI" in text:
        start_index = text.find("IDENTI")
        remaining_text = text[start_index:].strip()
        remaining_words = remaining_text.split()[1:4]
        english_name = " ".join(remaining_words)  # Join the words to form the full name


    # **Extract ID Number** (10-digit Arabic number)
    id_number_match = re.search(r'\b\d{10}\b', text)
    id_number = id_number_match.group() if id_number_match else None

    # **Extract Arabic Name** (Last 3 words before ID, excluding "الرفم")

    # **Extract Arabic Name Dynamically**
    arabic_name = None
    if id_number:
        text_before_id = text.split(id_number)[0]  # Get text before ID number
        arabic_phrases = re.findall(r'[\u0600-\u06FF\s]+', text_before_id)  # Extract Arabic phrases

        if arabic_phrases:
            arabic_words = arabic_phrases[-1].strip().split()
            # Remove unwanted words like "الرفم", "رقم", "هوية"
            arabic_words = [word for word in arabic_words if word not in ["الرفم", "رقم", "هوية", "الرقم"]]

            # Extract the last 3 Arabic words as the Arabic name
            arabic_name = " ".join(arabic_words[-4:]) if len(arabic_words) >= 3 else " ".join(arabic_words)


    # **Extract Nationality**
    nationality = None
    arabic_words = re.findall(r'[\u0600-\u06FF]+', text)  # Extract Arabic words

    # Look for the word "احنسبه" and capture the word right after it as nationality
    for i, word in enumerate(arabic_words):
        if word == "احنسبه" and i + 1 < len(arabic_words):
            nationality = arabic_words[i + 1]  # The word after "احنسبه"
            break


    # **Extract Date of Expiry (DOE) Dynamically (Next 6 words after الإننهاء)**
    arabic_words = re.findall(r'[\u0600-\u06FF]+', text)
    doe = None
    for i, word in enumerate(arabic_words):
      if word == "الإننهاء" and i + 6 <= len(arabic_words):
          doe = " ".join(arabic_words[i + 1:i + 6])  # Get the next 6 words after "الإننهاء"
          break



    # **Extract Profession Dynamically**
    arabic_words = re.findall(r'[\u0600-\u06FF]+', text)
    profession = None
    for i, word in enumerate(arabic_words):
      if word == "المهنة" and i + 1 < len(arabic_words):
          profession = arabic_words[i + 1]  # Get the word immediately after "المهنة"
          break


    return {
        "English Name": english_name,
        "Arabic Name": arabic_name,
        "Nationality": nationality,
        "ID Number": id_number,
        "Date of Expiry (DOE)": doe,
        "Profession": profession
    }




def vehicle_reg(text):
    # Normalize text (remove extra spaces and newlines)
    words = [word.strip() for word in text.split() if word.strip()]  # Split into words

    # **Extract ID Number (Owner's ID)**
    id_number_match = re.search(r'\b\d{10}\b', text)  # 10-digit number
    id_number = id_number_match.group() if id_number_match else None

    # **Extract Arabic Name (Owner's Name)**
    arabic_words = re.findall(r'[\u0600-\u06FF]+', text)  # Extract Arabic words
    owner_name = " ".join(arabic_words[arabic_words.index("المالك")+1:arabic_words.index("المستخدم")]) if "المالك" in arabic_words and "المستخدم" in arabic_words else None

    # **Extract Chassis Number** (English letters + numbers, remove spaces)
    chassis_match = re.search(r'رقم الهيكل\s+([A-Z0-9\s]+)', text)
    chassis_number = chassis_match.group(1).replace(" ", "") if chassis_match else None  # Join chassis parts

    # **Extract Make Year (Year of Manufacture)**
    # Define a list of valid years (2000-2030)
    valid_years = [str(year) for year in range(2000, 2031)]

    # Search for any valid year within the text
    make_year = None
    for year in valid_years:
        if year in text:
            make_year = year
            break  # Stop once the first valid year is found

    # **Extract Vehicle Capacity** (Single digit, near "حمولة المركبة")
    capacity_match = re.search(r'حمولة المركبة\s+(\d)', text)
    vehicle_capacity = capacity_match.group(1) if capacity_match else None

    # **Extract Vehicle Weight (after "وزن المركبة")**
    # Replace Arabic numerals with English numerals
    arabic_to_english_digits = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')  # Mapping Arabic digits to English
    text_english_digits = text.translate(arabic_to_english_digits)


    # **Extract Registration Type** (Arabic, e.g., "عام", "خاص")
    reg_type_match = re.search(r'نوع التسجيل\s+([\u0600-\u06FF]+)', text)
    registration_type = reg_type_match.group(1) if reg_type_match else None

    # **Extract Vehicle Make** (Arabic vehicle brand)
    vehicle_make_match = re.search(r'ماركة\s+المركبة\s+([\u0600-\u06FF]+)', text)
    vehicle_make = vehicle_make_match.group(1) if vehicle_make_match else None

    # **Extract Plate Number** (Dynamic plate number extraction: joined positions)
    plate_number = "".join(words[36:40]).replace(" ", "") if len(words) >= 40 else None

    # **Return structured output**
    return {
        "ID Number": id_number,
        "Owner Name": owner_name,
        "Chassis Number": chassis_number,
        "Make Year": make_year,
        "Vehicle Capacity": vehicle_capacity,
        "Registration Type": registration_type,
        "Vehicle Make": vehicle_make,
        "Plate Number": plate_number
    }

import easyocr
def clean_text(text):
    """Removes extra spaces, symbols, and normalizes Arabic text for better matching."""
    text = re.sub(r'[^a-zA-Z\u0600-\u06FF]', '', text)  # Keep only Arabic and English letters
    text = re.sub(r'\s+', '', text)  # Remove all extra spaces
    return text

# Normalize the text before searching
#normalized_text = clean_text(text)


def driving_license(text):
    # Normalize text (remove extra spaces and newlines)
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # Ensure we have enough lines
    if len(lines) < 2:
        return {"Error": "Text does not contain enough lines"}

    # **Extract last line only**
    last_line = lines[-1]

    # **Extract Arabic Name** (First 4 Arabic words from last line)
    arabic_words = re.findall(r'[\u0600-\u06FF]+', last_line)
    arabic_name = " ".join(arabic_words[:4]) if len(arabic_words) >= 4 else " ".join(arabic_words)

    # **Extract English Name** (Next 4 words after Arabic Name)
    remaining_text = last_line.split(arabic_name, 1)[-1].strip()  # Get text after Arabic name
    english_words = re.findall(r'[A-Za-z]+', remaining_text)  # Extract English words
    english_name = " ".join(english_words[:4]) if len(english_words) >= 4 else " ".join(english_words)

    # **Extract ID Number (10-digit number)**
    id_number_match = re.search(r'N0\.\s*(\d{10})', text)
    id_number = id_number_match.group(1) if id_number_match else None

    # **Extract Dates (DOB and Expiry)**
    date_matches = re.findall(r'\b\d{2}/\d{2}/\d{4}\b', text)
    dob = date_matches[0] if len(date_matches) > 0 else None
    doe = date_matches[1] if len(date_matches) > 1 else None

    # Return structured output
    return {
        "Arabic Name": arabic_name,
        "English Name": english_name,
        "ID Number": id_number,
        "Date of Birth": dob,
        "Date of Expiry": doe,

    }


def extract_national_id(text):
    """
    Extracts key information from a National ID OCR output.


    :param text: Raw OCR extracted text.
    :return: Dictionary containing extracted key information.
    """
    # Normalize text (remove extra spaces and newlines)
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # Ensure we have at least two lines
    if len(lines) < 2:
        return {"Error": "Text does not contain enough lines"}

    # Arabic Name: Take the last 5 words from the second line (right to left)
    second_line = lines[1]  # Skip the first line, take the second
    arabic_words = re.findall(r'[\u0600-\u06FF]+', second_line)  # Extract Arabic words

    arabic_name = " ".join(arabic_words[-5:]) if len(arabic_words) >= 5 else " ".join(arabic_words)

    # English Name: First occurrence of English words
    english_name_match = re.search(r'[A-Za-z]+(?:\s[A-Za-z]+)*', text)
    english_name = english_name_match.group().strip().replace("\n", " ") if english_name_match else None

    if english_name and english_name.split()[-1] in ["N", "No"]:  # Add more unwanted cases if needed
       english_name = " ".join(english_name.split()[:-1])  # Remove last word


    # Extract ID Number (10-digit number)
    id_number_match = re.search(r'\b\d{10}\b', text)
    id_number = id_number_match.group() if id_number_match else None

    # Extract Dates (DOB and DOE)
    date_matches = re.findall(r'\b\d{2}/\d{2}/\d{4}\b', text)
    dob = date_matches[0] if len(date_matches) > 0 else None  # First date = DOB
    doe = date_matches[1] if len(date_matches) > 1 else None  # Second date = DOE

    # Extract Arabic words appearing before "مكان الميلاد"
    doe_match = re.search(r'DOE:\s*\d{2}/\d{2}/\d{4}\s*[.\s]*([^\d\s.]+)', text)

    place_of_birth = doe_match.group(1).strip() if doe_match else None

    # Return structured output
    return {
        "Arabic Name": arabic_name,
        "English Name": english_name,
        "ID Number": id_number,
        "Date of Birth": dob,
        "Date of Expiry": doe,
        "Place of Birth": place_of_birth
    }


def store_id_data(id_type, filename, data):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    if id_type == "National ID":
        cursor.execute('''
            INSERT INTO NationalID (arabic_name, english_name, id_number, dob, doe, place_of_birth)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data['Arabic Name'], data['English Name'], data['ID Number'], data['Date of Birth'], data['Date of Expiry'], data['Place of Birth']))

    elif id_type == "Residential ID":
        cursor.execute('''
            INSERT INTO ResidentialID (english_name, arabic_name, nationality, id_number, doe, profession)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data['English Name'], data['Arabic Name'], data['Nationality'], data['ID Number'], data['Date of Expiry (DOE)'], data['Profession']))

    elif id_type == "Vehicle Registration":
        cursor.execute('''
            INSERT INTO VehicleRegistration (id_number, owner_name, chassis_number, make_year, vehicle_capacity, registration_type, vehicle_make, plate_number)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data['ID Number'], data['Owner Name'], data['Chassis Number'], data['Make Year'], data['Vehicle Capacity'], data['Registration Type'], data['Vehicle Make'], data['Plate Number']))

    elif id_type == "Driving License":
        cursor.execute('''
            INSERT INTO DrivingLicense (arabic_name, english_name, id_number, dob, doe)
            VALUES (?, ?, ?, ?, ?)
        ''', (data['Arabic Name'], data['English Name'], data['ID Number'], data['Date of Birth'], data['Date of Expiry']))

    conn.commit()
    conn.close()
