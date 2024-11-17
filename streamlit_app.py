import streamlit as st
import openai
import pandas as pd
from langchain.llms import OpenAI
import pytesseract
from PIL import Image, ImageFilter
import re
import os

### Load your API Key
my_secret_key = st.secrets['MyOpenAIKey']
os.environ["OPENAI_API_KEY"] = my_secret_key

llm = OpenAI(
    model_name="gpt-4o-mini",  # Replace with a valid OpenAI model
    temperature=0.7,
    openai_api_key=my_secret_key
)

# Function to get response from GPT-4
def get_gpt4_response(input_text, no_words, blog_style):
    try:
        # Construct the prompt
        prompt = f"Write a blog for a {blog_style} job profile on the topic '{input_text}'. Limit the content to approximately {no_words} words."
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # Ensure this is a valid model
            messages=[{"role": "user", "content": prompt}]
        )

        # Extract and return the response content
        return response.choices[0].message["content"]
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

# Function for OCR extraction
def preprocess_and_extract(image):
    try:
        # Convert image to grayscale and sharpen
        image = image.convert("L")  # Convert to grayscale
        image = image.filter(ImageFilter.SHARPEN)  # Sharpen the image
        
        # OCR with custom configuration
        custom_config = r'--psm 6'  # Assume a block of text
        raw_text = pytesseract.image_to_string(image, config=custom_config)
        
        # Extract details using regex
        amount = re.search(r'(\d+\.\d{2})', raw_text)  # Match amounts like 19.70
        date = re.search(r'\d{2}/\d{2}/\d{4}', raw_text)  # Match dates like MM/DD/YYYY
        type_keywords = ["food", "transport", "accommodation", "entertainment", "miscellaneous"]
        category = next((kw for kw in type_keywords if kw.lower() in raw_text.lower()), "Unknown")
        
        return {
            "Raw Text": raw_text,
            "Amount": float(amount.group(1)) if amount else None,
            "Date": date.group(0) if date else None,
            "Type": category
        }
    except Exception as e:
        st.error(f"Error during OCR processing: {e}")
        return None

# Streamlit UI configuration
st.set_page_config(
    page_title="Generate Blogs",
    page_icon="🛫",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.header("Generate Blogs 🛫")

# Sidebar Navigation
st.sidebar.title("Navigation")
branch = st.sidebar.radio("Select a branch", ["Generate Blogs", "Pre-travel", "Post-travel", "OCR Receipts"])

if branch == "Generate Blogs":
    st.header("Generate Blogs 🛫")

    # User inputs
    input_text = st.text_input("Enter the Blog Topic")
    col1, col2 = st.columns([5, 5])

    with col1:
        no_words = st.text_input("No of Words")
    with col2:
        blog_style = st.selectbox("Writing the blog for", ("Researchers", "Data Scientist", "Common People"), index=0)

    # Generate blog button
    submit = st.button("Generate")

    # Display the generated blog content
    if submit:
        blog_content = get_gpt4_response(input_text, no_words, blog_style)
        if blog_content:
            st.write(blog_content)

# Pre-travel Branch
elif branch == "Pre-travel":
    st.header("Pre-travel: Itinerary Generation")

    # User inputs
    destination = st.text_input("Enter Destination")

    # Dynamic interests dropdown based on the destination
    if destination:
        # Example: Replace with an API call or database lookup for top interests
        # Currently hardcoded for demonstration purposes
        destination_interests = {
            "New York": ["Statue of Liberty", "Central Park", "Broadway Shows", "Times Square", "Brooklyn Bridge",
                         "Museum of Modern Art", "Empire State Building", "High Line", "Fifth Avenue", "Rockefeller Center"],
            "Paris": ["Eiffel Tower", "Louvre Museum", "Notre-Dame Cathedral", "Champs-Élysées", "Montmartre",
                      "Versailles", "Seine River Cruise", "Disneyland Paris", "Arc de Triomphe", "Latin Quarter"],
            "Tokyo": ["Shinjuku Gyoen", "Tokyo Tower", "Akihabara", "Meiji Shrine", "Senso-ji Temple",
                      "Odaiba", "Ginza", "Tsukiji Market", "Harajuku", "Roppongi"],
        }

        # Default interests if destination is not found in hardcoded list
        top_interests = destination_interests.get(destination.title(), ["Beach", "Hiking", "Museums", "Local Food",
                                                                        "Shopping", "Parks", "Cultural Sites", 
                                                                        "Water Sports", "Music Events", "Nightlife"])
        
        interests = st.multiselect(
            "Select your interests",
            top_interests + ["Other"],  # Include "Other" option
            default=None
        )

        # If user selects "Other", allow them to input custom interests
        if "Other" in interests:
            custom_interest = st.text_input("Enter your custom interest(s)")
            if custom_interest:
                interests.append(custom_interest)

    else:
        st.write("Enter a destination to see the top activities.")

    # Calendar for travel dates
    travel_dates = st.date_input("Select your travel dates", [])

    # Budget categories
    budget = st.selectbox(
        "Select your budget level",
        ["Low (up to $5,000)", "Medium ($5,000 to $10,000)", "High ($10,000+)"]
    )

    # Cuisine requirements
    cuisine = st.radio("Cuisine Requirements?", ["Veg", "Non-Veg", "Vegan"])

    # Accessibility requirements
    accessibility = st.radio("Accessibility Requirements?", ["Yes", "No"])

    # Generate itinerary button
    generate_itinerary = st.button("Generate Itinerary")

    if generate_itinerary:
        # Create a prompt template
        prompt_template = """
        You are a travel assistant. Create a detailed itinerary for a trip to {destination}. 
        The user is interested in {interests}. The budget level is {budget}. 
        The travel dates are {travel_dates}. The user prefers {cuisine} food and 
        has accessibility requirements: {accessibility}. For each activity, include 
        the expected expense in both local currency and USD. Provide a total expense 
        at the end and ensure it aligns with the budget range.
        """

        # Initialize the prompt with the user's inputs
        prompt = prompt_template.format(
            destination=destination,
            interests=", ".join(interests) if interests else "general activities",
            budget=budget,
            travel_dates=travel_dates,
            cuisine=cuisine,
            accessibility=accessibility
        )

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )

            # Extract the itinerary from the response
            itinerary = response.choices[0].message["content"]

            # Example: Add mock total expense calculation based on budget
            if "Low" in budget:
                total_expense = "$4,800 (approx)"
            elif "Medium" in budget:
                total_expense = "$9,000 (approx)"
            else:
                total_expense = "$12,500 (approx)"

            # Display the itinerary
            st.subheader("Generated Itinerary:")
            st.write(itinerary)
            st.write(f"**Total Expected Expense:** {total_expense}")
        except Exception as e:
            st.error(f"An error occurred while generating the itinerary: {e}")

# Post-travel Branch
elif branch == "Post-travel":
    st.header("Post-travel: Data Classification and Summary")

    # Allow user to upload an Excel file
    uploaded_file = st.file_uploader("Upload your travel data (Excel file)", type=["xlsx"])

    if uploaded_file is not None:
        # Read the Excel file
        df = pd.read_excel(uploaded_file)

        st.subheader("Data Preview:")
        st.write(df.head())

        # Check if required columns exist
        if 'Description' in df.columns and 'Amount' in df.columns:
            # Function to classify each expense
            def classify_expense(description):
                try:
                    prompt = f"Classify the following expense description into categories like 'Food', 'Transport', 'Accommodation', 'Entertainment', 'Miscellaneous':\n\n'{description}'\n\nCategory:"
                    response = openai.ChatCompletion.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}]
                    )
                    return response.choices[0].message["content"].strip()
                except Exception as e:
                    st.error(f"Error in classifying expense: {e}")
                    return "Unknown"

            # Apply the classification function to each description
            df['Category'] = df['Description'].apply(classify_expense)

            st.subheader("Classified Data:")
            st.write(df)

            # Generate a summary of expenses
            try:
                total_spent = df['Amount'].sum()
                summary_prompt = f"Provide a quick summary of the travel expenses based on the following data:\n\n{df.to_string()}\n\nSummary:"

                response = openai.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": summary_prompt}]
                )
                summary = response.choices[0].message["content"].strip()

                st.subheader("Summary:")
                st.write(summary)

                st.subheader(f"Total Spent: ${total_spent:.2f}")
            except Exception as e:
                st.error(f"Error in generating summary: {e}")
        else:
            st.error("The uploaded Excel file must contain 'Description' and 'Amount' columns.")

# OCR Receipts Branch
elif branch == "OCR Receipts":
    st.header("OCR Receipts: Extract Data from Receipts")

    # Allow user to upload receipt image
    uploaded_receipt = st.file_uploader("Upload your receipt image (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])

    if uploaded_receipt is not None:
        # Process the uploaded image
        receipt_image = Image.open(uploaded_receipt)
        st.image(receipt_image, caption="Uploaded Receipt", use_column_width=True)

        with st.spinner("Processing and extracting data..."):
            receipt_data = preprocess_and_extract(receipt_image)
            if receipt_data:
                st.subheader("Extracted Data:")
                st.write(f"**Raw Text:** {receipt_data['Raw Text']}")
                st.write(f"**Amount:** {receipt_data['Amount'] if receipt_data['Amount'] else 'Not Found'}")
                st.write(f"**Date:** {receipt_data['Date'] if receipt_data['Date'] else 'Not Found'}")
                st.write(f"**Type:** {receipt_data['Type']}")
