import streamlit as st
import sqlite3

st.set_page_config(page_title="Mutual Fund Tracker", layout="wide")

st.title("🏠 Home")
st.write("Welcome to your Mutual Fund Tracker!")

import streamlit as st

# Dummy user database (replace with your DB or auth system)
#USER_DB = {
 #   "sankar": "password123",
  #  "admin": "adminpass"
#}

def login_screen():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.title("Login")

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        row = get_user(username, password)
        
        if st.button("Login"):            
            if row:
                user_id, username = row
                st.session_state.logged_in = True
                st.session_state.user_id = user_id
                st.success(f"Welcome, {username}!")
            else:
                st.error("Invalid username or password")
    else:
        st.success(f"Logged in as {st.session_state.user_id}")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.user_id = None
# --- Database setup ---
def init_db():
    conn = sqlite3.connect("SQLite/mf.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
           user_id INTEGER PRIMARY KEY AUTOINCREMENT,
           username TEXT NOT NULL UNIQUE,
           password TEXT NOT NULL,
           email TEXT UNIQUE,
           created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
    """)
    conn.commit()
    conn.close()

def get_user(username, password):
    conn = sqlite3.connect("SQLite/mf.db")
    cursor = conn.cursor()
    cursor.execute(
    "SELECT user_id, username FROM users WHERE username=? AND password=?", (username, password,))
    rows = cursor.fetchone()
    conn.close()
    return rows

# --- Initialize DB ---
init_db()

# Usage in your app
login_screen()

if st.session_state.get("logged_in", False):
    st.write("✅ Show investments here for:", st.session_state.user_id)
    # call your fetch_investments(st.session_state.user_id) here
