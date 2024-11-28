    # Initialize session state for interests and destination interests
    if "interests" not in st.session_state:
        st.session_state.interests = []
    if "destination_interests" not in st.session_state:
        st.session_state.destination_interests = []

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
            
            # Update session state with generated interests list
            st.session_state.destination_interests = top_interests

    # Display the dynamic interest selection list
    if st.session_state.destination_interests:
        st.session_state.interests = st.multiselect(
            "Select your interests",
            st.session_state.destination_interests + ["Other"],
            default=st.session_state.interests
        )

    # Step 2: Final button to generate itinerary
    if st.session_state.interests and st.button("Generate Travel Itinerary"):
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
