import os
import urllib.parse
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from langchain_core.tools import Tool
from langchain_community.utilities import GoogleSerperAPIWrapper
import openai
import streamlit as st
import time

# Load API keys
#my_secret_key = st.secrets['IS883-OpenAIKey-RV']
#openai.api_key = my_secret_key
os.environ["OPENAI_API_KEY"] = st.secrets['MyOpenAIKey']
os.environ["SERPER_API_KEY"] = st.secrets["SerperAPIKey"]

# Function to generate Google Maps link
def generate_maps_link(place_name, city_name):
    base_url = "https://www.google.com/maps/search/?api=1&query="
    full_query = f"{place_name}, {city_name}"
    return base_url + urllib.parse.quote(full_query)

# Function to clean and extract valid place names
def extract_place_name(activity_line):
    prefixes_to_remove = ["Visit", "Explore", "Rest", "the", "Last-minute Shopping in"]
    for prefix in prefixes_to_remove:
        if activity_line.lower().startswith(prefix.lower()):
            activity_line = activity_line.replace(prefix, "").strip()
    return activity_line

# Initialize the Google Serper API Wrapper
search = GoogleSerperAPIWrapper()
serper_tool = Tool(
    name="GoogleSerper",
    func=search.run,
    description="Useful for when you need to look up some information on the internet.",
)

# OpenAI API call with token usage tracking
def format_flight_prices_with_chatgpt(raw_response, origin, destination, departure_date):
    try:
        prompt = f"""
        You are a helpful assistant. I received the following raw flight information for a query:
        'Flights from {origin} to {destination} on {departure_date}':
        {raw_response}

        Please clean and reformat this information into a professional, readable format. Use bullet points,
        categories, or a table wherever appropriate to make it easy to understand. Also include key highlights
        like the cheapest fare, airlines, and travel dates. Ensure that any missing or irrelevant text is ignored.
        """
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        token_usage = response.usage.total_tokens
        return response.choices[0].message["content"], token_usage
    except Exception as e:
        return f"An error occurred while formatting the response: {e}", 0

# Function to fetch flight prices and calculate token usage
def fetch_flight_prices(origin, destination, departure_date):
    try:
        query = f"flights from {origin} to {destination} on {departure_date}"
        raw_response = serper_tool.func(query)
        formatted_response, token_usage = format_flight_prices_with_chatgpt(
            raw_response, origin, destination, departure_date
        )
        return formatted_response, token_usage
    except Exception as e:
        return f"An error occurred while fetching or formatting flight prices: {e}", 0

# Function to generate an itinerary and calculate token usage
def generate_itinerary_with_chatgpt(origin, destination, travel_dates, interests, budget):
    try:
        prompt_template = """
        You are a travel assistant. Create a detailed itinerary for a trip from {origin} to {destination}. 
        The user is interested in {interests}. The budget level is {budget}. 
        The travel dates are {travel_dates}. For each activity, include the expected expense in both local currency 
        and USD. Provide a total expense at the end. Include at least 5 places to visit and list them as "Activity 1", "Activity 2", etc.
        """
        prompt = prompt_template.format(
            origin=origin,
            destination=destination,
            interests=", ".join(interests) if interests else "general activities",
            budget=budget,
            travel_dates=travel_dates
        )
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        token_usage = response.usage.total_tokens
        return response.choices[0].message["content"], token_usage
    except Exception as e:
        return f"An error occurred while generating the itinerary: {e}", 0

# Function to create a PDF from the itinerary and flight prices
def create_pdf(itinerary, flight_prices):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    styles = getSampleStyleSheet()
    title_style = styles["Heading1"]
    section_style = styles["Heading2"]
    text_style = styles["BodyText"]

    elements = []

    elements.append(Paragraph("Travel Itinerary", title_style))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Itinerary:", section_style))
    for line in itinerary.splitlines():
        elements.append(Paragraph(line, text_style))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Flight Prices:", section_style))
    for line in flight_prices.splitlines():
        elements.append(Paragraph(line, text_style))
    elements.append(Spacer(1, 20))

    doc.build(elements)
    buffer.seek(0)
    return buffer

# Streamlit UI Configuration
st.set_page_config(page_title="Travel Planning Assistant", page_icon="🛫", layout="wide")

# Sidebar Inputs
with st.sidebar:
    st.header("🛠️ Trip Details")
    origin = st.text_input("Flying From", placeholder="Enter your departure city/airport")
    destination = st.text_input("Flying To", placeholder="Enter your destination city/airport")
    travel_dates = st.date_input("📅 Travel Dates", [])
    budget = st.selectbox("💰 Budget Level", ["Low", "Medium", "High"])
    interests = st.multiselect("🎯 Interests", ["Beach", "Hiking", "Museums"])

# Generate Itinerary Button
if st.button("📝 Generate Travel Itinerary"):
    if not origin or not destination or len(travel_dates) != 2:
        st.error("⚠️ Please provide all required details.")
    else:
        with st.spinner("Fetching details..."):
            flight_prices, flight_tokens = fetch_flight_prices(
                origin, destination, travel_dates[0].strftime("%Y-%m-%d")
            )
            itinerary, itinerary_tokens = generate_itinerary_with_chatgpt(
                origin, destination, travel_dates, interests, budget
            )
            st.session_state["flight_prices"] = flight_prices
            st.session_state["itinerary"] = itinerary
            st.session_state["token_usage"] = {
                "flight_prices": flight_tokens,
                "itinerary": itinerary_tokens,
            }

# Display Evaluation Metrics
if "token_usage" in st.session_state:
    st.subheader("📊 Evaluation Metrics")
    OPENAI_COST_PER_1K_TOKENS = 0.0025
    total_tokens = sum(st.session_state["token_usage"].values())
    total_cost = (total_tokens / 1000) * OPENAI_COST_PER_1K_TOKENS

    st.write(f"- **Total Tokens Used**: {total_tokens}")
    st.write(f"- **Estimated OpenAI API Cost**: ${total_cost:.4f}")
