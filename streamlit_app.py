import streamlit as st
import openai
import pandas as pd
from langchain.llms import OpenAI
import pytesseract
from PIL import Image, ImageFilter
import re
import os
import requests

# Load your API Key
my_secret_key = st.secrets['MyOpenAIKey']
os.environ["OPENAI_API_KEY"] = my_secret_key

llm = OpenAI(
    model_name="gpt-4o-mini",
    temperature=0.7,
    openai_api_key=my_secret_key
)

# Cache Function for External API Calls
@st.cache
def get_exchange_rates(base_currency="USD"):
    url = f"https://api.exchangerate-api.com/v4/latest/{base_currency}"
    response = requests.get(url).json()
    return response.get("rates", {})

@st.cache
def get_dynamic_interests(destination):
    # Placeholder for dynamic interest suggestions (Replace with real API)
    return ["Local Food", "Museums", "Hiking", "Shopping"]

# Functions
def get_gpt4_response(input_text, no_words, blog_style):
    try:
        if not no_words.isdigit():
            return "Invalid word count! Please enter a number."
        no_words = int(no_words)
        prompt = f"Write a blog for a {blog_style} job profile on the topic '{input_text}'. Limit the content to approximately {no_words} words."
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message["content"]
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

def fetch_flight_prices(origin, destination, departure_date):
    try:
        serper_api_key = st.secrets["SerperAPIKey"]
        headers = {"X-API-KEY": serper_api_key, "Content-Type": "application/json"}
        payload = {"q": f"flights from {origin} to {destination} on {departure_date}"}
        response = requests.post("https://google.serper.dev/search", headers=headers, json=payload)
        response.raise_for_status()
        return response.json().get("answerBox", {}).get("snippet", "No flight prices found.")
    except Exception as e:
        return f"Error fetching flight prices: {e}"

def preprocess_and_extract(image):
    try:
        image = image.convert("L").filter(ImageFilter.SHARPEN)
        custom_config = r'--psm 6'
        raw_text = pytesseract.image_to_string(image, config=custom_config)
        amount = re.search(r'(\d+\.\d{2})', raw_text)
        date = re.search(r'\d{2}/\d{2}/\d{4}', raw_text)
        categories = ["food", "transport", "accommodation", "entertainment", "miscellaneous"]
        category = next((kw for kw in categories if kw.lower() in raw_text.lower()), "Unknown")
        return {
            "Raw Text": raw_text,
            "Amount": float(amount.group(1)) if amount else None,
            "Date": date.group(0) if date else None,
            "Type": category
        }
    except Exception as e:
        st.error(f"Error during OCR processing: {e}")
        return None

# Streamlit UI Configuration
st.set_page_config(page_title="Travel Planning Assistant", page_icon="🛫", layout="centered")

st.header("Travel Planning Assistant 🛫")
st.sidebar.title("Navigation")
branch = st.sidebar.radio("Select a branch", ["Generate Blogs", "Plan Your Travel", "Post-travel", "OCR Receipts", "Feedback"])

if branch == "Generate Blogs":
    st.header("Generate Blogs 🛫")
    input_text = st.text_input("Enter the Blog Topic")
    no_words = st.text_input("Number of Words")
    blog_style = st.selectbox("Writing the blog for", ["Researchers", "Data Scientist", "Common People", "Other"])
    if blog_style == "Other":
        custom_style = st.text_input("Enter your custom style")
        if custom_style:
            blog_style = custom_style
    submit = st.button("Generate")
    if submit:
        blog_content = get_gpt4_response(input_text, no_words, blog_style)
        st.write(blog_content)

elif branch == "Plan Your Travel":
    st.header("Plan Your Travel 🗺️")
    origin = st.text_input("Flying From (Origin)")
    destination = st.text_input("Flying To (Destination)")
    travel_dates = st.date_input("Select Travel Dates")
    budget = st.selectbox("Budget", ["Low (up to $5,000)", "Medium ($5,000 to $10,000)", "High ($10,000+)"])
    if st.button("Generate Itinerary"):
        itinerary = f"Example itinerary from {origin} to {destination} for a {budget} budget on {travel_dates}"
        st.write(itinerary)

elif branch == "Post-travel":
    st.header("Post-travel: Data Summary")
    uploaded_file = st.file_uploader("Upload Travel Data (Excel)", type=["xlsx"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        st.write("Data Preview:", df.head())
        st.write("Total Expenses:", df["Amount"].sum())

elif branch == "OCR Receipts":
    st.header("OCR Receipts")
    uploaded_receipt = st.file_uploader("Upload Receipt Image", type=["png", "jpg", "jpeg"])
    if uploaded_receipt:
        image = Image.open(uploaded_receipt)
        extracted_data = preprocess_and_extract(image)
        st.write("Extracted Data:", extracted_data)

elif branch == "Feedback":
    st.header("We value your feedback!")
    feedback = st.text_area("Share your feedback with us.")
    if st.button("Submit Feedback"):
        st.success("Thank you for your feedback!")
