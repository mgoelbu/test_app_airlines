#os.environ["OPENAI_API_KEY"] = st.secrets['IS883-OpenAIKey-RV']
#os.environ["SERPER_API_KEY"] = st.secrets["SerperAPIKey"]

#my_secret_key = st.secrets['MyOpenAIKey']
#os.environ["OPENAI_API_KEY"] = my_secret_key

#my_secret_key = st.secrets['IS883-OpenAIKey-RV']
#os.environ["OPENAI_API_KEY"] = my_secret_key

#my_secret_key = st.secrets['IS883-OpenAIKey-RV']
#openai.api_key = my_secret_key


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
my_secret_key = st.secrets['MyOpenAIKey']
openai.api_key = my_secret_key
#os.environ["OPENAI_API_KEY"] = st.secrets['MyOpenAIKey']
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
        return response.choices[0].message["content"]
    except Exception as e:
        return f"An error occurred while generating the itinerary: {e}"

# Function to create a PDF from itinerary and flight prices
def create_pdf(itinerary, flight_prices):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    # Styles for the document
    styles = getSampleStyleSheet()
    title_style = styles["Heading1"]
    section_style = styles["Heading2"]
    text_style = styles["BodyText"]

    elements = []

    # Add title
    elements.append(Paragraph("Travel Itinerary", title_style))
    elements.append(Spacer(1, 20))  # Add space

    # Add itinerary section
    elements.append(Paragraph("Itinerary:", section_style))
    for line in itinerary.splitlines():
        elements.append(Paragraph(line, text_style))
    elements.append(Spacer(1, 20))  # Add space

    # Add flight prices section
    elements.append(Paragraph("Flight Prices:", section_style))
    for line in flight_prices.splitlines():
        elements.append(Paragraph(line, text_style))
    elements.append(Spacer(1, 20))  # Add space

    # Build the PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

# Streamlit UI configuration
st.set_page_config(
    page_title="Travel Planning Assistant",
    page_icon="🛫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS for sky blue background
st.markdown(
    """
    <style>
    body {
        background-color: #e3f2fd;
    }
    h1, h2, h3 {
        color: #2c3e50;
        font-family: 'Arial', sans-serif;
    }
    .st-expander {
        background-color: #f9f9f9;
        border-radius: 10px;
        border: 1px solid #ddd;
        padding: 10px;
    }
    .st-expander-header {
        font-weight: bold;
        color: #2980b9;
    }
    .stButton>button {
        background-color: #2980b9;
        color: white;
        font-size: 16px;
        border-radius: 5px;
        padding: 10px 15px;
    }
    .stButton>button:hover {
        background-color: #1c598a;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Function to display content in cards
def display_card(title, content):
    return f"""
    <div style="background-color:#f9f9f9; padding:10px; border-radius:10px; margin-bottom:10px; border:1px solid #ddd;">
        <h4 style="color:#2980b9;">{title}</h4>
        <p>{content}</p>
    </div>
    """

# App Title
st.title("🌍 Travel Planning Assistant")
st.write("Plan your perfect trip with personalized itineraries and flight suggestions!")

# Sidebar Inputs
with st.sidebar:
    st.header("🛠️ Trip Details")
    origin = st.text_input("Flying From (Origin Airport/City)", placeholder="Enter your departure city/airport")
    destination = st.text_input("Flying To (Destination Airport/City)", placeholder="Enter your destination city/airport")
    travel_dates = st.date_input("📅 Travel Dates", [], help="Select your trip's start and end dates.")
    budget = st.selectbox("💰 Select your budget level", ["Low (up to $5,000)", "Medium ($5,000 to $10,000)", "High ($10,000+)"])
    interests = st.multiselect("🎯 Select your interests", ["Beach", "Hiking", "Museums", "Local Food", "Shopping", "Parks", "Cultural Sites", "Nightlife"])

# Store results in session state
if "itinerary" not in st.session_state:
    st.session_state.itinerary = None
if "flight_prices" not in st.session_state:
    st.session_state.flight_prices = None

# Main Content Section
if st.button("📝 Generate Travel Itinerary"):
    if not origin or not destination or len(travel_dates) != 2:
        st.error("⚠️ Please provide all required details: origin, destination, and a valid travel date range.")
    else:
        progress = st.progress(0)
        for i in range(100):
            time.sleep(0.01)  # Simulate loading time
            progress.progress(i + 1)

        with st.spinner("Fetching details..."):
            st.session_state.flight_prices = fetch_flight_prices(origin, destination, travel_dates[0].strftime("%Y-%m-%d"))
            st.session_state.itinerary = generate_itinerary_with_chatgpt(origin, destination, travel_dates, interests, budget)

# Display results only if available
if st.session_state.itinerary and st.session_state.flight_prices:
    st.success("✅ Your travel details are ready!")

    # Create two columns
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(display_card("Itinerary", st.session_state.itinerary), unsafe_allow_html=True)

    with col2:
        st.markdown(display_card("Flight Prices", st.session_state.flight_prices), unsafe_allow_html=True)

    # Display map links directly on the main page
    st.subheader("📍 Places to Visit with Map Links")
    activities = [
        line.split(":")[1].strip() 
        for line in st.session_state.itinerary.split("\n") 
        if ":" in line and "Activity" in line
    ]
    if activities:
        for activity in activities:
            place_name = extract_place_name(activity)
            if place_name:
                maps_link = generate_maps_link(place_name, destination)
                st.markdown(f"- **{place_name}**: [View on Google Maps]({maps_link})")
    else:
        st.write("No activities could be identified.")

    # Generate and provide download link for PDF
    pdf_buffer = create_pdf(st.session_state.itinerary, st.session_state.flight_prices)
    st.download_button(
        label="📥 Download Itinerary as PDF",
        data=pdf_buffer,
        file_name="travel_itinerary.pdf",
        mime="application/pdf",
    )



import time

# Add a section at the bottom for evaluation metrics
st.markdown("## 📊 Evaluation Metrics")

# Initialize variables to store metrics
execution_times = {}
#api_costs = {}

# Measure the execution time for fetching flight prices
start_time = time.time()
if "flight_prices" in st.session_state and st.session_state.flight_prices:
    fetch_flight_prices(origin, destination, travel_dates[0].strftime("%Y-%m-%d"))
end_time = time.time()
execution_times["Fetch Flight Prices"] = end_time - start_time

# Measure the execution time for generating an itinerary
start_time = time.time()
if "itinerary" in st.session_state and st.session_state.itinerary:
    generate_itinerary_with_chatgpt(origin, destination, travel_dates, interests, budget)
end_time = time.time()
execution_times["Generate Itinerary"] = end_time - start_time

# Calculate approximate costs (replace these rates with your actual API cost structures)
#OPENAI_COST_PER_1K_TOKENS = 0.002  # Example: $0.002 per 1k tokens
#SERPER_COST_PER_QUERY = 0.01       # Example: $0.01 per query

# Estimating token usage for OpenAI API calls
#openai_token_usage = 1500  # Adjust based on your actual token usage per call
#api_costs["OpenAI API"] = (openai_token_usage / 1000) * OPENAI_COST_PER_1K_TOKENS

# Estimating query usage for Serper API calls
#serper_query_count = 1  # Assume 1 query per flight search
#api_costs["Serper API"] = serper_query_count * SERPER_COST_PER_QUERY

# Display the metrics in the app
st.subheader("Execution Times (in seconds)")
for task, exec_time in execution_times.items():
    st.write(f"- **{task}**: {exec_time:.2f} seconds")

#st.subheader("Estimated API Costs (in USD)")
#for api, cost in api_costs.items():
    #st.write(f"- **{api}**: ${cost:.4f}")

# Add an overall summary
st.markdown(
    """
    ### Summary
    - **Total Execution Time**: {:.2f} seconds
    """.format(sum(execution_times.values()))
)


from rouge_score import rouge_scorer
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction

# Reference Itinerary for Evaluation (manually curated or from trusted sources)
reference_itinerary = """
Trip Itinerary: Boston to Sydney
Travel Dates: December 29, 2024 - January 3, 2025
Day 1: Departure from Boston
  - Depart from Boston (BOS) to Sydney (SYD)
  - Estimated Cost: $1,200 USD
Day 2: Arrival in Sydney
  - Activity 1: Sydney Opera House
  - Activity 2: Royal Botanic Garden
Day 3: Australian Museum and Explore The Rocks
Day 4: Art Gallery of New South Wales
Day 5: Taronga Zoo
Day 6: Departure from Sydney
"""

# Generated Itinerary (Replace with the output from the app)
generated_itinerary = st.session_state.itinerary if "itinerary" in st.session_state else ""

# ROUGE Evaluation
def evaluate_rouge(reference, generated):
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
    scores = scorer.score(reference, generated)
    return scores

# BLEU Evaluation
def evaluate_bleu(reference, generated):
    # Tokenize and split sentences into lists of words
    reference_sentences = [reference.split()]  # BLEU expects a list of references
    generated_sentences = generated.split()  # Tokenize generated text
    smoothing = SmoothingFunction().method1  # Add smoothing to avoid zero scores
    bleu_score = sentence_bleu(reference_sentences, generated_sentences, smoothing_function=smoothing)
    return bleu_score

# Perform Evaluations if Both Reference and Generated Itineraries are Available
if generated_itinerary:
    rouge_scores = evaluate_rouge(reference_itinerary, generated_itinerary)
    bleu_score = evaluate_bleu(reference_itinerary, generated_itinerary)

    # Display ROUGE Scores
    st.subheader("ROUGE Evaluation Metrics")
    st.write(f"ROUGE-1 (Unigram Overlap): {rouge_scores['rouge1'].fmeasure:.4f}")
    st.write(f"ROUGE-2 (Bigram Overlap): {rouge_scores['rouge2'].fmeasure:.4f}")
    st.write(f"ROUGE-L (Longest Common Subsequence): {rouge_scores['rougeL'].fmeasure:.4f}")

    # Display BLEU Score
    st.subheader("BLEU Evaluation Metric")
    st.write(f"BLEU Score: {bleu_score:.4f}")
else:
    st.error("No generated itinerary available for evaluation.")

