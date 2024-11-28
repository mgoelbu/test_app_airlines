import os
from langchain_core.tools import Tool
from langchain_community.utilities import GoogleSerperAPIWrapper
import openai
import streamlit as st

# Load API keys
os.environ["OPENAI_API_KEY"] = st.secrets["MyOpenAIKey"]
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
        # Prompt engineering for clean, readable output
        prompt = f"""
        You are a helpful assistant. I received the following raw flight information for a query:
        'Flights from {origin} to {destination} on {departure_date}':
        {raw_response}

        Please clean and reformat this information into a professional, readable format. Use bullet points,
        categories, or a table wherever appropriate to make it easy to understand. Also include key highlights
        like the cheapest fare, airlines, and travel dates. Ensure that any missing or irrelevant text is ignored.
        """
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message["content"]
    except Exception as e:
        return f"An error occurred while formatting the response: {e}"

# Function to fetch flight prices and format them with ChatGPT
def fetch_flight_prices(origin, destination, departure_date):
    try:
        # Query flight prices using Google Serper
        query = f"flights from {origin} to {destination} on {departure_date}"
        raw_response = serper_tool.func(query)  # Get raw output from Serper tool

        # Pass raw output to ChatGPT for formatting
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
            model="gpt-4",
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

# Sidebar Navigation
st.sidebar.title("Navigation")
branch = st.sidebar.radio("Select a branch", ["Plan Your Travel", "Post-travel", "OCR Receipts"])

# Plan Your Travel Branch
if branch == "Plan Your Travel":
    st.header("Plan Your Travel 🗺️")

    # Step 1: Collect basic trip details
    origin = st.text_input("Flying From (Origin Airport/City)")
    destination = st.text_input("Flying To (Destination Airport/City)")
    travel_dates = st.date_input("Select your travel dates", [])
    budget = st.selectbox(
        "Select your budget level",
        ["Low (up to $5,000)", "Medium ($5,000 to $10,000)", "High ($10,000+)"]
    )

    if st.button("Set Interests"):
        # Validate that required inputs are provided before proceeding
        if not origin or not destination or not travel_dates:
            st.error("Please fill in all required fields (origin, destination, and travel dates) to proceed.")
        else:
            # Generate dynamic interests list based on destination
            destination_interests = {
                "New York": ["Statue of Liberty", "Central Park", "Broadway Shows", "Times Square", "Brooklyn Bridge",
                             "Museum of Modern Art", "Empire State Building", "High Line", "Fifth Avenue", "Rockefeller Center"],
                "Paris": ["Eiffel Tower", "Louvre Museum", "Notre-Dame Cathedral", "Champs-Élysées", "Montmartre",
                          "Versailles", "Seine River Cruise", "Disneyland Paris", "Arc de Triomphe", "Latin Quarter"],
                "Tokyo": ["Shinjuku Gyoen", "Tokyo Tower", "Akihabara", "Meiji Shrine", "Senso-ji Temple",
                          "Odaiba", "Ginza", "Tsukiji Market", "Harajuku", "Roppongi"],
            }
            top_interests = destination_interests.get(destination.title(), ["Beach", "Hiking", "Museums", "Local Food",
                                                                            "Shopping", "Parks", "Cultural Sites", 
                                                                            "Water Sports", "Music Events", "Nightlife"])
            
            # Dynamic interest selection
            st.session_state.interests = st.multiselect(
                "Select your interests",
                top_interests + ["Other"],  # Include "Other" option
                default=None
            )

    # Step 2: Final button to generate itinerary
    if "interests" in st.session_state and st.button("Generate Travel Itinerary"):
        interests = st.session_state.get("interests", [])
        if "Other" in interests:
            custom_interest = st.text_input("Enter your custom interest(s)")
            if custom_interest:
                interests.append(custom_interest)

        # Fetch flight prices
        flight_prices = fetch_flight_prices(origin, destination, travel_dates[0].strftime("%Y-%m-%d"))

        # Generate itinerary
        itinerary = generate_itinerary_with_chatgpt(
            origin, destination, travel_dates, interests, budget
        )

        # Display results
        st.subheader("Estimated Flight Prices:")
        st.write(flight_prices)

        st.subheader("Generated Itinerary:")
        st.write(itinerary)

# Post-travel Branch
elif branch == "Post-travel":
    st.header("Post-travel: Data Classification and Summary")
    uploaded_file = st.file_uploader("Upload your travel data (Excel file)", type=["xlsx"])
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        st.subheader("Data Preview:")
        st.write(df.head())

# OCR Receipts Branch
elif branch == "OCR Receipts":
    st.header("OCR Receipts: Extract Data from Receipts")
    uploaded_receipt = st.file_uploader("Upload your receipt image (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])
    if uploaded_receipt:
        receipt_image = Image.open(uploaded_receipt)
        receipt_data = preprocess_and_extract(receipt_image)
        if receipt_data:
            st.subheader("Extracted Data:")
            st.write(receipt_data)
