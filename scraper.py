import requests
from bs4 import BeautifulSoup
import pandas as pd

def scrape_quotes(tag):
    base_url = "https://quotes.toscrape.com"
    quotes_data = []
    page = 1
    
    while True:
        response = requests.get(f"{base_url}/tag/{tag}/page/{page}")
        if response.status_code != 200:
            break
        
        soup = BeautifulSoup(response.text, 'html.parser')
        quotes = soup.select('.quote')
        
        if not quotes:
            break

        for quote in quotes:
            text = quote.select_one('.text').get_text(strip=True)
            author = quote.select_one('.author').get_text(strip=True)
            quotes_data.append({"Quote": text, "Author": author})
        
        page += 1

    return quotes_data
import streamlit as st
import pandas as pd

# Import the scraper function
from scraper import scrape_quotes  # Assuming scraper function is in 'scraper.py'

# App Title
st.title("Quotes Scraper")

# Input Field
tag = st.text_input("Enter a tag to search for quotes (e.g., 'love', 'life')")

# Submit Button
if st.button("Submit"):
    with st.spinner("Fetching quotes..."):
        results = scrape_quotes(tag)
        
    if results:
        # Display Results
        st.success(f"Found {len(results)} quotes!")
        for result in results:
            st.write(f"- {result['Quote']} — **{result['Author']}**")

        # Convert results to DataFrame
        df = pd.DataFrame(results)

        # CSV Download Button
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"quotes_{tag}.csv",
            mime="text/csv"
        )
    else:
        st.error("No quotes found for the given tag.")
