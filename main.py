import streamlit as st
import os
import runpy
import json
import uuid
import time

logo_path = "t.png"
icon_path = "newshopofficial_cover.jpeg"

# Setting the page configuration
if os.path.exists(logo_path):
    st.set_page_config(page_title="TNS Unified Analysis Dashboard", layout="wide", page_icon=logo_path)
else:
    st.set_page_config(page_title="TNS Unified Analysis Dashboard", layout="wide")

st.markdown(
    """
    <style>
    .main .block-container {
        max-width: 90% !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

SESSION_FILE = "active_sessions.json"

def load_credentials():
    credentials_path = os.getenv("CREDENTIALS_PATH", "./credentials/credentials.json")
    
    if os.path.exists(credentials_path):
        with open(credentials_path, "r") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                st.error("Error: Credentials file is not a valid JSON.")
                return {}
    else:
        st.error(f"Error: {credentials_path} not found!")
        return {}

def save_active_session(session_id, username, role):
    """Save the active session to a file."""
    active_sessions = {}
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            active_sessions = json.load(f)

    active_sessions[session_id] = {
        "username": username,
        "role": role,
        "expires_at": time.time() + (24 * 3600)
    }

    with open(SESSION_FILE, "w") as f:
        json.dump(active_sessions, f)

def remove_active_session(session_id):
    """Remove the active session from the file."""
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            active_sessions = json.load(f)

        if session_id in active_sessions:
            del active_sessions[session_id]

        with open(SESSION_FILE, "w") as f:
            json.dump(active_sessions, f)

def validate_session(session_id):
    """Validate if a session ID is active and not expired."""
    if not session_id:
        return None, None
        
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            active_sessions = json.load(f)

        session_info = active_sessions.get(session_id)
        if session_info and session_info["expires_at"] > time.time():
            session_info["expires_at"] = time.time() + (24 * 3600)
            with open(SESSION_FILE, "w") as f:
                json.dump(active_sessions, f)
            # Ensure role and username are returned
            username = session_info.get("username")
            role = session_info.get("role", "guest")  # default to "guest" if role is missing
            return username, role
    return None, None

def login(username, password):
    """Validate login credentials and return role."""
    credentials = load_credentials()
    if not credentials:
        return None
        
    if username not in credentials:
        return None
        
    user_info = credentials[username]
    if user_info and user_info.get('password') == password:
        return user_info.get('role', 'guest') 
    return None

if "session_id" not in st.session_state:
    params = st.query_params
    session_id = params.get("session_id", None)
    st.session_state.session_id = session_id

if "username" not in st.session_state:
    st.session_state.username = None
    st.session_state.role = None

if st.session_state.session_id:
    username, role = validate_session(st.session_state.session_id)
    if username:
        st.session_state.username = username
        st.session_state.role = role
        st.query_params.update({"session_id": st.session_state.session_id})
    else:
        st.session_state.session_id = None
        st.session_state.username = None
        st.session_state.role = None
        st.query_params.clear()

if not st.session_state.username:
    # Centered login form (not full screen)
    col1, col2, col3 = st.columns([1, 2, 1])  
    with col2:
        # Center-align the logo and title
        if os.path.exists(icon_path):  # Check if the image exists
            st.image(icon_path, use_container_width=True, width=200)
        st.markdown("<h1 style='text-align: center;'>Login to Dashboard</h1>", unsafe_allow_html=True)

        username_input = st.text_input("Username", placeholder="Enter your username")
        password_input = st.text_input("Password", placeholder="Enter your password", type="password")

        if st.button("Login"):
            if username_input and password_input:
                role = login(username_input, password_input)
                if role:
                    session_id = str(uuid.uuid4())
                    st.session_state.session_id = session_id
                    save_active_session(session_id, username_input, role)
                    st.session_state.username = username_input
                    st.session_state.role = role
                    st.query_params.update({"session_id": session_id})
                    
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password!")
            else:
                st.warning("Enter both username and password.")
else:
    username = st.session_state.username
    role = st.session_state.role
    if username:
        st.markdown(f"<h1 style='text-align: center;'>User: {username} ({role})</h1>", unsafe_allow_html=True)

        with st.sidebar:
            if st.button("Logout"):
                remove_active_session(st.session_state.session_id)
                st.session_state.session_id = None
                st.session_state.username = None
                st.session_state.role = None
                st.query_params.clear()
                st.success("You have logged out.")
                st.rerun()

        # Define analysis options based on user role
        if role == "admin":
            analysis_options = ["Product Analysis", "Category Analysis", "Store Analysis", "Brand Analysis", "Reports"]
        elif role == "category":
            analysis_options = ["Product Analysis", "Category Analysis", "Store Analysis", "Brand Analysis"]
        elif role == "reports":
            analysis_options = ["Reports"]
        else:
            analysis_options = []

        analysis_type = st.selectbox(
            "Choose an analysis type",
            analysis_options
        )

        def run_analysis(script_name):
            try:
                script_path = os.path.join(script_name, "main.py")

                if script_name == "reports":
                    try:
                        runpy.run_path(script_path)
                    except Exception as e:
                        if "Invalid comparison between dtype=datetime64[ns, UTC] and Timestamp" in str(e):
                            st.error("Upload your data to analyze")
                        else:
                            st.error(f"An error occurred while running {script_name} analysis: {e}")
                else:
                    runpy.run_path(script_path)
            except Exception as e:
                st.error(f"An error occurred while running {script_name} analysis: {e}")

        if analysis_type == "Product Analysis":
            run_analysis("product_analysis")
        elif analysis_type == "Category Analysis":
            run_analysis("category_analysis")
        elif analysis_type == "Store Analysis":
            run_analysis("store_analysis")
        elif analysis_type == "Brand Analysis":
            run_analysis("brand_analysis")
        elif analysis_type == "Reports":
            run_analysis("reports")
        else:
            st.warning("Select an analysis type to proceed.")
    else:
        st.error("Session expired. Please log in again.")
        st.session_state.session_id = None
        st.rerun()

st.markdown(
    """
    <style>
    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #f1f1f1;
        text-align: center;
        padding: 10px;
        font-size: 12px;
        color: #555;
    }
    </style>
    <div class="footer">
        The New Shop &copy; 2025. All rights reserved.
    </div>
    """,
    unsafe_allow_html=True
)