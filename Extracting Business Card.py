## import requirment pakages
import streamlit as st
import cv2
import pytesseract
import re
import nltk
import psycopg2
from psycopg2 import Error
import numpy as np
import pandas as pd

##  functions for particular pattern extraction from bussiness card
def filter_websites(text):
    pattern = r'\b(?:https?://|www\.)\S+\b'
    return (re.findall(pattern, text), re.sub(pattern, '<sss>', text))

def replace_newline_before_six_digit(text):
    pattern = r'\n(?=\d{6})'
    replaced_text = re.sub(pattern, ' ', text)
    return replaced_text

def filter_phone_number(text):
    pattern = r'\+\d{0,}-\d{0,}-\d{0,}|\d{0,}-\d{0,}-\d{0,}'
    return (re.findall(pattern, text), re.sub(pattern, '<sss>', text))

def filter_valid_email(text):
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
    return (re.findall(pattern, text), re.sub(pattern, '<sss>', text))

def store_data_in_database(data):
    try:
        # Establish a connection to the PostgreSQL database
        connection = psycopg2.connect(
            host="localhost",
            port = "5432",
            database="ocr_data",
            user="postgres",
            password="Open@new0"
        )

        cursor = connection.cursor()

        # Insert the data into the database
        insert_query = """
            INSERT INTO data_tab (name, designation, address, email, contact,company, website)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (
            data['name'],
            data['designation'],
            data['address'],
            data['email'],
            data['contact'],
            data['company'],
            data['website']
            
        ))

        connection.commit()
        # st.success("Data stored successfully!")

    except (Exception, Error) as error:
        st.error(f"Error while connecting to PostgreSQL or storing data: {error}")

    finally:
        # Close the database connection
        if connection:
            cursor.close()
            connection.close()

def main():
    # Set the app title and description
    st.title("Extracting Business Card")
    st.markdown("Upload an image and extract information from it.")

    # Upload image
    uploaded_image = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])

    if uploaded_image is not None:
        # Load the image using OpenCV
        image = cv2.imdecode(np.fromstring(uploaded_image.read(), np.uint8), 1)

        # Extract text from the image using Tesseract
        text = pytesseract.image_to_string(image)
        text = text.replace('\n\n', ' <nextline_1> ')
        text = replace_newline_before_six_digit(text)
        text = re.sub(r'\n+', ' <nextline> ', text)
        email, text = filter_valid_email(text)
        contact, text = filter_phone_number(text)
        website, text = filter_websites(text)
        gg = [[t for t in tt.split('<nextline>') if t.find('<sss>') == -1] for tt in text.split('<nextline_1>')]
        address = ''
        company = ''
        designation = ''
        name = ''

        for i, d in enumerate(gg):
            if not bool(d):
                continue

            if i == 0 and len(d) > 1:
                name = d[0].strip()
                try:
                    designation = d[1].strip()
                    continue
                except:
                    continue
            elif i == 0:
                name = d[0].strip()
                continue

            if i == 1 and not designation and not address and name and not bool(re.findall(r'\d{6}', d[0])):
                designation = d[0].strip()
                continue

            if len(d) > 1 and i != 0:
                if d[0].find('St.') != -1 or d[0].find(',') != -1:
                    address += d[0].strip()
                    if bool(re.findall(r'\d{6}', d[1])):
                        address += d[1].strip()
                        continue

                else:
                    company += d[0].strip() + ' '
                    company += d[1].strip()
                    continue

            elif d[0].find('St.') != -1 or d[0].find(',') != -1:
                address += d[0].strip()
                continue

            if not company:
                company = d[0].strip()

        extracted = [name, designation, address, email, contact, website, company]
        tags = ['name', 'designation', 'address', 'email', 'contact', 'website', 'company']
        data = dict(((tag, '; '.join(i) if type(i) == list else re.sub(r'^\)', '', i).strip()) for tag, i in zip(tags, extracted)))
        print(data)
        st.header("Extracted Data:")
        st.write(pd.DataFrame(data, index=[0]))
        if st.button("Save Data"):
            # Call the function to store data in the database
            store_data_in_database(data)
            st.success("Data stored successfully!")

if __name__ == '__main__':
    main()    



