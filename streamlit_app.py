import os
import openai
import re
import pandas as pd
import streamlit as st
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from langchain_core.tools import Tool
from langchain_community.utilities import GoogleSerperAPIWrapper

# Load API keys
os.environ["OPENAI_API_KEY"] = st.secrets["MyOpenAIKey"]
os.environ["SERPER_API_KEY"] = st.secrets["SerperAPIKey"]

# Initialize Google Serper API Wrapper
search = GoogleSerperAPIWrapper()
serper_tool = Tool(
    name="GoogleSerper",
    func=search.run,
    description="Useful for when you need to look up some information on the internet.",
)

# Function to format flight price data with ChatGPT
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
        return response.choices[0].message["content"]
    except Exception as e:
        return f"An error occurred while formatting the response: {e}"

# Function to dynamically fetch interest suggestions using ChatGPT
def fetch_interests_with_chatgpt(destination):
    try:
        prompt = f"""
        You are a travel assistant. Suggest the top 10 points of interest or activities for tourists in {destination}.
        Ensure the suggestions cover a variety of activities such as cultural sites, natural attractions, local experiences, 
        and unique landmarks.
        """
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        interests = response.choices[0].message["content"].split("\n")
        return [interest.strip("- ") for interest in interests if interest]
    except Exception as e:
        return ["General Activities", "Other"]

# Function to fetch flight prices using Google Serper
def fetch_flight_prices(origin, destination, departure_date):
    try:
        query = f"flights from {origin} to {destination} on {departure_date}"
        raw_response = serper_tool.func(query)
        return format_flight_prices_with_chatgpt(raw_response, origin, destination, departure_date)
    except Exception as e:
        return f"An error occurred while fetching flight prices: {e}"

# Function to generate a detailed itinerary with ChatGPT
def generate_itinerary_with_chatgpt(origin, destination, travel_dates, interests, budget):
    try:
        prompt_template = """
        You are a travel assistant. Create a detailed itinerary for a trip from {origin} to {destination}. 
        The user is interested in {interests}. The budget level is {budget}. 
        The travel dates are {travel_dates}. For each activity, include:
        - Activity name
        - City and country context
        - Latitude and longitude for geocoding purposes
        Provide a minimum of 5 activities with full details for accurate location mapping.
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
        return response.choices[0].message["content"]
    except Exception as e:
        return f"An error occurred while generating the itinerary: {e}"

# Function to extract activities with coordinates from the itinerary
def extract_activities_with_coordinates(itinerary_text):
    pattern = re.compile(
        r"Activity Name: (.*?)\nCity and Country: (.*?)\n.*?Latitude & Longitude: ([\d.\-]+), ([\d.\-]+)",
        re.DOTALL
    )
    activities = []
    for match in pattern.finditer(itinerary_text):
        place, city, lat, lon = match.groups()
        activities.append({
            'Place': place.strip(),
            'City': city.strip(),
            'lat': float(lat.strip()),
            'lon': float(lon.strip())
        })
    return pd.DataFrame(activities)

# Fallback geocoding function
def geocode_places(places, context=""):
    geolocator = Nominatim(user_agent="travel_planner")
    geocoded_data = []
    for place in places:
        try:
            location = geolocator.geocode(f"{place}, {context}", timeout=10)
            if location:
                geocoded_data.append({'Place': place, 'lat': location.latitude, 'lon': location.longitude})
            else:
                st.warning(f"Could not geocode: {place}")
        except GeocoderTimedOut:
            st.warning(f"Geocoding timed out for {place}. Skipping.")
    return pd.DataFrame(geocoded_data)

# Initialize session state for navigation and interests
if "active_branch" not in st.session_state:
    st.session_state.active_branch = None
if "interests" not in st.session_state:
    st.session_state.interests = []

# Navigation
st.header("Travel Planning Assistant 🛫")
st.subheader("Choose an option to get started:")

if st.session_state.active_branch is None:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Pre-travel", key="pre_travel_btn"):
            st.session_state.active_branch = "Pre-travel"
    with col2:
        if st.button("Post-travel", key="post_travel_btn"):
            st.session_state.active_branch = "Post-travel"

# Pre-travel Branch
if st.session_state.active_branch == "Pre-travel":
    st.header("Plan Your Travel 🗺️")
    origin = st.text_input("Flying From (Origin Airport/City)")
    destination = st.text_input("Flying To (Destination Airport/City)")
    travel_dates = st.date_input("Select your travel dates", [])
    budget = st.selectbox("Select your budget level", ["Low (up to $5,000)", "Medium ($5,000 to $10,000)", "High ($10,000+)"])

    # Dynamic interest suggestions
    if destination and st.button("Set Interests"):
        st.session_state.destination_interests = fetch_interests_with_chatgpt(destination)
        st.session_state.interests = st.multiselect(
            "Select your interests",
            st.session_state.destination_interests + ["Other"],
            default=st.session_state.interests
        )

    # Generate itinerary
    if st.session_state.interests and st.button("Generate Travel Itinerary"):
        itinerary = generate_itinerary_with_chatgpt(
            origin, destination, travel_dates, st.session_state.interests, budget
        )
        st.subheader("Generated Itinerary:")
        st.write(itinerary)

        # Geocode and map visualization
        activity_df = extract_activities_with_coordinates(itinerary)
        if not activity_df.empty:
            st.subheader("Map of Activities:")
            st.map(activity_df[['lat', 'lon']])
        else:
            st.warning("No coordinates found. Attempting to geocode activities.")
            geocoded_df = geocode_places([f"{place}, {city}" for place, city in activity_df[["Place", "City"]].values])
            if not geocoded_df.empty:
                st.map(geocoded_df[['lat', 'lon']])

# Post-travel Branch
elif st.session_state.active_branch == "Post-travel":
    st.header("Post-travel: Data Classification and Summary")
    uploaded_file = st.file_uploader("Upload your travel data (Excel file)", type=["xlsx"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        st.subheader("Data Preview:")
        st.write(df.head())

# Back Button
if st.session_state.active_branch:
    if st.button("Back to Home"):
        st.session_state.active_branch = None
