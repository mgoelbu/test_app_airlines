import os
from langchain_core.tools import Tool
from langchain_community.utilities import GoogleSerperAPIWrapper
import openai
import streamlit as st

# Load API keys
my_secret_key = st.secrets['MyOpenAIKey']
openai.api_key = my_secret_key
os.environ["SERPER_API_KEY"] = st.secrets["SerperAPIKey"]

# Initialize the Google Serper API Wrapper
search = GoogleSerperAPIWrapper()
serper_tool = Tool(
    name="GoogleSerper",
    func=search.run,
    description="Useful for when you need to look up some information on the internet.",
)

# Function to query ChatGPT for better formatting
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

# Function to fetch flight prices and format them with ChatGPT
def fetch_flight_prices(origin, destination, departure_date):
    try:
        query = f"flights from {origin} to {destination} on {departure_date}"
        raw_response = serper_tool.func(query)
        formatted_response = format_flight_prices_with_chatgpt(
            raw_response, origin, destination, departure_date
        )
        return formatted_response
    except Exception as e:
        return f"An error occurred while fetching or formatting flight prices: {e}"

# Function to generate a detailed itinerary using ChatGPT
def generate_itinerary_with_chatgpt(origin, destination, travel_dates, interests, budget):
    try:
        prompt_template = """
        You are a travel assistant. Create a detailed itinerary for a trip from {origin} to {destination}. 
        The user is interested in {interests}. The budget level is {budget}. 
        The travel dates are {travel_dates}. For each activity, include the expected expense in both local currency 
        and USD. Provide a total expense at the end.
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

# Streamlit UI configuration
st.set_page_config(
    page_title="Travel Planning Assistant",
    page_icon="🛫",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.header("Travel Planning Assistant 🛫")

# Initialize session state variables
if "branch" not in st.session_state:
    st.session_state.branch = None
if "origin" not in st.session_state:
    st.session_state.origin = ""
if "destination" not in st.session_state:
    st.session_state.destination = ""
if "travel_dates" not in st.session_state:
    st.session_state.travel_dates = []
if "budget" not in st.session_state:
    st.session_state.budget = ""
if "interests" not in st.session_state:
    st.session_state.interests = []

# Homepage Navigation
if st.session_state.branch is None:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Pre-travel"):
            st.session_state.branch = "Pre-travel"
    with col2:
        if st.button("Post-travel"):
            st.session_state.branch = "Post-travel"

# Pre-travel Branch
if st.session_state.branch == "Pre-travel":
    st.header("Plan Your Travel 🗺️")
    st.session_state.origin = st.text_input("Flying From (Origin Airport/City)", value=st.session_state.origin)
    st.session_state.destination = st.text_input("Flying To (Destination Airport/City)", value=st.session_state.destination)
    st.session_state.travel_dates = st.date_input("Select your travel dates", value=st.session_state.travel_dates)
    st.session_state.budget = st.selectbox(
        "Select your budget level",
        ["Low (up to $5,000)", "Medium ($5,000 to $10,000)", "High ($10,000+)"],
        index=["Low (up to $5,000)", "Medium ($5,000 to $10,000)", "High ($10,000+)"].index(st.session_state.budget)
        if st.session_state.budget else 0
    )

    interests = st.multiselect(
        "Select your interests",
        ["Beach", "Hiking", "Museums", "Local Food", "Shopping", "Parks", "Cultural Sites", "Nightlife"],
        default=st.session_state.interests
    )
    st.session_state.interests = interests

    if st.button("Generate Travel Itinerary"):
        if not st.session_state.origin or not st.session_state.destination or not st.session_state.travel_dates:
            st.error("Please fill in all required fields (origin, destination, and travel dates).")
        else:
            flight_prices = fetch_flight_prices(
                st.session_state.origin,
                st.session_state.destination,
                st.session_state.travel_dates[0].strftime("%Y-%m-%d")
            )
            itinerary = generate_itinerary_with_chatgpt(
                st.session_state.origin,
                st.session_state.destination,
                st.session_state.travel_dates,
                st.session_state.interests,
                st.session_state.budget
            )

            with st.expander("Flight Prices", expanded=True):
                st.write(flight_prices)
            with st.expander("Itinerary", expanded=True):
                st.write(itinerary)

# Post-travel Branch
if st.session_state.branch == "Post-travel":
    st.header("Post-travel: Data Classification and Summary")
    uploaded_file = st.file_uploader("Upload your travel data (Excel file)", type=["xlsx"])
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        st.subheader("Data Preview:")
        st.write(df.head())
