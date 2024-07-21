import streamlit as st
import google.generativeai as genai
from PIL import Image
import pytesseract
import pdf2image
import io
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Set up the Streamlit app
st.title("Scholarship Matcher with  AI 🎓")
st.caption("This app uses AI to scans for scholarships matching a student's profile")

# Get Gemini API key from .env file
gemini_api_key = os.getenv("GEMINI_API_KEY")

# Initialize Gemini AI if API key is available
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-pro')

    # Function to extract text from image
    def extract_text_from_image(image):
        return pytesseract.image_to_string(image)

    # Function to extract text from PDF
    def extract_text_from_pdf(pdf_file):
        images = pdf2image.convert_from_bytes(pdf_file.read())
        text = ""
        for image in images:
            text += pytesseract.image_to_string(image)
        return text

    # Get student information
    st.subheader("Student Information")
    name = st.text_input("Full Name")
    age = st.number_input("Age", min_value=0, max_value=100)
    grade = st.number_input("Current Grade/GPA", min_value=0.0, max_value=4.0, step=0.1)
    major = st.text_input("Intended Major/Field of Study")

    # Get family information
    st.subheader("Family Information")
    siblings = st.number_input("Number of Siblings", min_value=0)
    siblings_in_school = st.number_input("Number of Siblings in School", min_value=0)

    # Upload financial documents
    st.subheader("Financial Information")
    payslip = st.file_uploader("Upload Parent/Guardian Payslip", type=["jpg", "jpeg", "png", "pdf"])
    other_docs = st.file_uploader("Upload Other Financial Documents", type=["jpg", "jpeg", "png", "pdf"], accept_multiple_files=True)

    if st.button("Find Matching Scholarships"):
        if payslip and other_docs:
            # Extract text from payslip
            if payslip.type == "application/pdf":
                payslip_text = extract_text_from_pdf(payslip)
            else:
                payslip_image = Image.open(payslip)
                payslip_text = extract_text_from_image(payslip_image)

            # Extract text from other documents
            other_docs_text = ""
            for doc in other_docs:
                if doc.type == "application/pdf":
                    other_docs_text += extract_text_from_pdf(doc)
                else:
                    doc_image = Image.open(doc)
                    other_docs_text += extract_text_from_image(doc_image)

            # Prepare the prompt for Gemini
            prompt = f"""
            Based on the following student profile and financial information, find and list suitable active scholarships in Africa:

            Student Information:
            - Name: {name}
            - Age: {age}
            - Grade/GPA: {grade}
            - Intended Major: {major}

            Family Information:
            - Number of Siblings: {siblings}
            - Siblings in School: {siblings_in_school}

            Financial Information:
            Payslip details: {payslip_text}

            Other financial documents: {other_docs_text}

            Please analyze this information and provide a list of active scholarships in Africa that this student might be eligible for. Include scholarship names, brief descriptions, any specific requirements that match the student's profile and link to that website.
            """

            # Generate response using Gemini
            response = model.generate_content(prompt)

            # Display the results
            st.subheader("Matching Scholarships")
            st.write(response.text)
        else:
            st.error("Please upload all required documents.")

else:
    st.error("Gemini API Key not found. Please check your .env file.")