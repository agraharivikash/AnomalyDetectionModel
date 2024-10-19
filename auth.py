# auth.py
import streamlit as st
import json
import os

# Path to the JSON file for user credentials
USERS_FILE = "users.json"

def load_users():
    """Load user credentials from the JSON file."""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_user(name, email, password):
    """Save a new user to the JSON file."""
    users = load_users()
    users[email] = {"name": name, "password": password}
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def login(email, password):
    """Validate user credentials."""
    users = load_users()
    if email in users and users[email]["password"] == password:
        st.session_state["authenticated"] = True
        st.session_state["email"] = email
        st.session_state["name"] = users[email]["name"]
        return True
    else:
        st.error("Invalid email or password")
        return False

def logout():
    """Clear the session state to log out the user."""
    st.session_state["authenticated"] = False
    st.session_state["email"] = None
    st.session_state["name"] = None
    st.experimental_rerun()

def is_authenticated():
    """Check if the user is authenticated."""
    return st.session_state.get("authenticated", False)

def login_screen():
    """Display the login screen."""
    st.title("🔒 Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if login(email, password):
            st.success(f"Welcome back, {st.session_state['name']}!")
            return True
    return False

def signup_screen():
    """Display the signup screen."""
    st.title("📝 Sign Up")
    name = st.text_input("Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Sign Up"):
        if name and email and password:
            users = load_users()
            if email in users:
                st.error("Email already exists. Choose a different email.")
            else:
                save_user(name, email, password)
                st.success("Account created successfully! You can now log in.")
        else:
            st.error("Please fill in all fields.")
