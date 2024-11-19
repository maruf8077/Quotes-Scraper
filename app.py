import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
import sqlite3
import bcrypt
import asyncio
import aiohttp
from streamlit_option_menu import option_menu
from datetime import datetime


# --- DATABASE FUNCTIONS ---
# Database connection function
def get_db_connection():
    conn = sqlite3.connect("users.db")
    return conn

# Database initialization function
def initialize_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    conn.commit()
    conn.close()

# Function to create a new user
def create_user(username, plain_password):
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed_password = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt())
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

# Function to authenticate users
def authenticate(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()

    if row:
        stored_password = row[0]  # Retrieve the stored (hashed) password
        if bcrypt.checkpw(password.encode('utf-8'), stored_password):
            return True
    return False

# Call the database initialization function
initialize_database()

# --- SCRAPING FUNCTIONS ---
async def scrape_quotes_async(tag):
    base_url = "https://quotes.toscrape.com"
    quotes_data = []
    page = 1

    async with aiohttp.ClientSession() as session:
        while True:
            async with session.get(f"{base_url}/tag/{tag}/page/{page}") as response:
                if response.status != 200:
                    break
                soup = BeautifulSoup(await response.text(), 'html.parser')
                quotes = soup.select('.quote')
                if not quotes:
                    break
                for quote in quotes:
                    text = quote.select_one('.text').get_text(strip=True)
                    author = quote.select_one('.author').get_text(strip=True)
                    quotes_data.append({"Quote": text, "Author": author})
                page += 1
    return quotes_data

def scrape_quotes(tag):
    return asyncio.run(scrape_quotes_async(tag))

# --- STREAMLIT APP FUNCTIONS ---
def apply_styles():
    st.markdown(
        """
        <style>
        body { background-color: #f8f9fa; }
        .stApp { max-width: 800px; margin: auto; }
        .sidebar { background-color: #343a40; color: white; }
        .quote-card {
            padding: 15px;
            margin: 10px;
            background: #222831; /* Dark background for better contrast */
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            color: #eeeeee; /* Light text color for better readability */
            font-family: Arial, sans-serif;
        }
        .quote-card p {
            margin: 0;
            padding: 5px 0;
        }
        .quote-card strong {
            font-size: 1.2em;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def main():
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = None

    # Sidebar Menu
    selected = option_menu(
        menu_title=None,
        options=["Home", "Scraper", "Login", "Signup"],
        icons=["house", "search", "person", "person-plus"],
        menu_icon="menu-button",
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "5px"},
            "nav-link": {"font-size": "15px", "text-align": "center"},
        },
    )

    if selected == "Home":
        st.title("Welcome to the Quotes Scraper App")
         # Get the current date and time
        now = datetime.now()
        formatted_time = now.strftime("%A, %B %d, %Y %H:%M:%S")
    
       # Add date and time to the top-right corner
        st.markdown(
        f"""
        <div style="text-align: right; font-size: 14px; color: #EEEEEE;">
            {formatted_time}
        </div>
        """, 
        unsafe_allow_html=True
    )
        st.markdown("Use this app to scrape quotes from [Quotes to Scrape](https://quotes.toscrape.com).")
        st.image("ne.jpg", use_container_width=True)

    

    elif selected == "Scraper":
        if not st.session_state.authenticated:
            st.error("Please login to access the scraper.")
        else:
            st.title("Scrape Quotes")
            tag = st.text_input("Enter a tag to search for quotes (e.g., 'love', 'life')")
            if st.button("Submit"):
                with st.spinner("Fetching quotes..."):
                    results = scrape_quotes(tag)
                if results:
                    st.success(f"Found {len(results)} quotes!")
                    for result in results[:10]:  # Show first 10 quotes
                        st.markdown(
                            f"""<div class="quote-card">
                                <p><strong>{result['Quote']}</strong></p>
                                <p>- {result['Author']}</p>
                            </div>""",
                            unsafe_allow_html=True,
                        )
                    # DataFrame and Download
                    df = pd.DataFrame(results)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"quotes_{tag}.csv",
                        mime="text/csv"
                    )
                else:
                    st.error("No quotes found for the given tag.")

    elif selected == "Login":
        if not st.session_state.authenticated:
            st.title("Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                if authenticate(username, password):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.success(f"Welcome back, {username}!")
                else:
                    st.error("Invalid username or password.")
        else:
            st.success(f"You are logged in as {st.session_state.username}")
            if st.button("Logout"):
                st.session_state.authenticated = False
                st.session_state.username = None
                st.info("You have been logged out.")

    elif selected == "Signup":
        st.title("Sign Up")
        username = st.text_input("Choose a Username")
        password = st.text_input("Choose a Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        if st.button("Sign Up"):
            if not username or not password:
                st.error("Username and Password cannot be empty!")
            elif password != confirm_password:
                st.error("Passwords do not match!")
            else:
                if create_user(username, password):
                    st.success("Account created successfully!")
                else:
                    st.error("Username already exists.")

# --- RUN THE APP ---
apply_styles()
main()
