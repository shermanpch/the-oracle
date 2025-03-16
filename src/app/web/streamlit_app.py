"""
Streamlit application for the Oracle I Ching Interpreter.

This module provides a web interface for the Oracle I Ching Interpreter using Streamlit.
"""

import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Add the project root directory to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import requests
import streamlit as st

from src.utils.supabase_client import get_supabase_client


def add_custom_styles():
    """Add all custom styles directly in the application."""
    st.markdown(
        """
        <style>
            /* Primary theme color */
            :root {
                --primary-color: #A855F7;
                --secondary-color: #8B5CF6;
                --background-color: #1E1E1E;
                --secondary-bg: #2E2E2E;
                --text-color: #EAEAEA;
                --border-color: rgba(168, 85, 247, 0.4);
            }

            /* Main styling */
            .main-header {
                font-size: 2.5rem;
                color: var(--primary-color);
                text-align: center;
                margin-bottom: 2rem;
                font-weight: 700;
                text-shadow: 1px 1px 3px rgba(0,0,0,0.3);
            }

            .sub-header {
                font-size: 1.7rem;
                color: var(--text-color);
                margin-top: 1.5rem;
                margin-bottom: 1.2rem;
                font-weight: 600;
                border-bottom: 2px solid var(--border-color);
                padding-bottom: 0.5rem;
            }

            /* Button styling */
            .stButton>button {
                background-color: var(--primary-color) !important;
                color: white !important;
                border-radius: 6px !important;
                padding: 0.6rem 1.2rem !important;
                font-weight: 600 !important;
                border: none !important;
                width: 100% !important;
                transition: all 0.3s ease !important;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            .stButton>button:hover {
                background-color: var(--secondary-color) !important;
                box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
                transform: translateY(-1px) !important;
            }

            /* Submit button specifically */
            [data-testid="oracle_form"] .stButton>button {
                font-size: 1.1rem !important;
                margin-top: 1rem !important;
                background-color: var(--primary-color) !important;
            }

            /* Input form elements */
            .stTextInput>div>div>input {
                border-radius: 6px;
                border: 1px solid var(--border-color) !important;
                padding: 1rem !important;
            }

            .stSelectbox>div>div>div {
                border-radius: 6px;
                border: 1px solid var(--border-color) !important;
            }

            .stExpander {
                border-radius: 6px !important;
                border: 1px solid var(--border-color) !important;
            }

            .stForm {
                background-color: var(--secondary-bg);
                padding: 1.5rem;
                border-radius: 8px;
                margin-bottom: 1.5rem;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }

            /* CSS that can't be handled by config.toml */

            /* Number input spinner removal - can't be done in config.toml */
            input[type="number"]::-webkit-inner-spin-button, 
            input[type="number"]::-webkit-outer-spin-button { 
                -webkit-appearance: none !important; 
                margin: 0 !important; 
            }

            input[type="number"] {
                -moz-appearance: textfield !important;
            }

            /* Target all possible spinner button selectors */
            .stNumberInput div[data-baseweb] button,
            [data-testid="stNumberInput"] button,
            button[aria-label*="value"],
            div[data-baseweb="input"] ~ div > div > div > button,
            div[data-baseweb="input-spinner"] button,
            .st-bd div[data-testid="stNumberInput"] button,
            div[data-testid="stNumberInput"] div[role="button"],
            [data-testid="InputIncrementDecrementButtons"] {
                display: none !important;
                visibility: hidden !important;
                opacity: 0 !important;
                width: 0 !important;
                height: 0 !important;
                padding: 0 !important;
                margin: 0 !important;
                border: none !important;
            }

            /* Hide the parent container of spinner buttons */
            div[data-baseweb="input-spinner"] {
                display: none !important;
            }

            /* Fixed positioning - can't be done in config.toml */
            .sidebar-footer {
                position: fixed;
                bottom: 55px;
                left: 1rem;
                width: calc(100% - 2rem);
                max-width: 17rem;
                background-color: var(--secondary-bg);
                padding: 1rem;
                border-top: 1px solid var(--border-color);
                text-align: left;
                z-index: 998;
                border-radius: 6px 6px 0 0;
                box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
            }

            .sidebar-footer p {
                font-weight: 600;
                color: var(--text-color);
            }

            .logout-container {
                position: fixed;
                bottom: 15px;
                left: 1rem;
                width: calc(100% - 2rem);
                max-width: 17rem;
                padding: 0.5rem 0;
                z-index: 999;
            }

            /* Custom prediction sections */
            .prediction-section {
                padding: 1.5rem;
                margin-bottom: 1.5rem;
                border-left: 4px solid var(--primary-color);
                background-color: var(--secondary-bg);
                border-radius: 0 8px 8px 0;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                transition: transform 0.2s ease;
            }

            .prediction-section:hover {
                transform: translateX(3px);
            }

            .prediction-title {
                color: var(--primary-color);
                font-size: 1.4rem;
                font-weight: 700;
                margin-bottom: 1rem;
                border-bottom: 1px solid var(--border-color);
                padding-bottom: 0.5rem;
            }

            /* Line Change image sizing */
            .line-change-image {
                max-height: 300px;
                width: auto;
                margin: 0 auto 1rem;
                display: block;
                border-radius: 4px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }

            /* Login/Signup form styling */
            [data-testid="stExpander"] {
                background-color: var(--secondary-bg);
                border-radius: 8px;
                margin-bottom: 2rem;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }

            /* Improved tabs styling */
            .stTabs [data-baseweb="tab-list"] {
                gap: 2px;
            }

            .stTabs [data-baseweb="tab"] {
                background-color: var(--secondary-bg);
                border-radius: 6px 6px 0 0;
                padding: 1rem 1.5rem;
                font-weight: 600;
            }

            .stTabs [aria-selected="true"] {
                background-color: var(--primary-color) !important;
                color: white !important;
            }

            /* Error and success messages styling */
            .stAlert {
                border-radius: 6px;
                padding: 1rem;
                margin: 1rem 0;
            }

            /* Make sure dark mode text is readable */
            p, span, div, label {
                color: var(--text-color);
            }
            
            /* Section styling with different colors */
            .hexagram-title { color: #A5B4FC; }
            .summary-text { color: #A7F3D0; }
            .interpretation-text { color: #F3F4F6; }
            .line-change-text { color: #FCD34D; }
            
            /* Query section styling */
            .query-section {
                background-color: #262626;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
                box-shadow: 2px 2px 8px rgba(0,0,0,0.2);
            }
            
            /* Improved button styling */
            div.stButton > button {
                width: 100%;
                background-color: #8B5CF6 !important;
                color: white !important;
                border-radius: 5px !important;
                padding: 10px !important;
                transition: 0.3s !important;
            }
            div.stButton > button:hover {
                background-color: #6D28D9 !important;
                box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
                transform: translateY(-1px) !important;
            }
            
            /* Profile section styling */
            .profile-section {
                padding: 10px;
                background-color: #2E2E2E;
                border-radius: 5px;
                text-align: center;
                margin-bottom: 15px;
            }
            
            /* Prediction section styling */
            .prediction-header {
                border-left: 4px solid #A855F7;
                padding: 10px;
                margin-bottom: 20px;
            }
            
            /* Welcome message styling */
            .welcome-message {
                text-align: center;
                padding: 40px 20px;
            }
            
            /* Mobile responsiveness */
            @media (max-width: 768px) {
                .main-header { font-size: 1.8rem !important; }
                .sub-header { font-size: 1.4rem !important; }
            }
            
            /* Custom purple theme boxes */
            .purple-box {
                background-color: rgba(168, 85, 247, 0.15);
                border-left: 4px solid #A855F7;
                border-radius: 4px;
                padding: 1rem;
                margin-bottom: 1rem;
            }
            
            .light-purple-box {
                background-color: rgba(139, 92, 246, 0.1);
                border-left: 4px solid #8B5CF6;
                border-radius: 4px;
                padding: 1rem;
                margin-bottom: 1rem;
            }
            
            /* Bottom sidebar elements */
            .sidebar-bottom {
                position: fixed;
                bottom: 0;
                left: 0;
                width: 100%;
                max-width: 17rem; /* Adjust based on Streamlit's sidebar width */
                background-color: #1E1E1E;
                padding: 1rem;
                z-index: 999;
                border-top: 1px solid rgba(168, 85, 247, 0.4);
            }
            
            /* Add padding to the bottom of the sidebar to prevent content overlap */
            section[data-testid="stSidebar"] > div {
                padding-bottom: 120px; /* Adjust based on the height of your bottom elements */
            }
        </style>
    """,
        unsafe_allow_html=True,
    )


def main():
    """
    Main function to run the Streamlit application for 'The Oracle - I Ching Interpreter'.
    """
    # Enhanced page config that includes theme settings that were previously in config.toml
    st.set_page_config(
        page_title="The Oracle",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={"About": "The Oracle - I Ching Interpreter"},
    )

    # Add custom styles directly
    add_custom_styles()

    st.markdown(
        '<h1 class="main-header">🔮 The Oracle - I Ching Interpreter</h1>',
        unsafe_allow_html=True,
    )

    API_URL = os.getenv("API_URL", "https://oracle-api.onrender.com")
    supabase = get_supabase_client()

    if "user" not in st.session_state:
        st.session_state.user = None

    if "query_submitted" not in st.session_state:
        st.session_state.query_submitted = False

    if "prediction_result" not in st.session_state:
        st.session_state.prediction_result = None

    # Authentication section
    if st.session_state.user is None:
        with st.expander("Login or Sign Up", expanded=True):
            tab1, tab2 = st.tabs(["Login", "Sign Up"])

            with tab1:
                with st.form(key="login_form"):
                    email = st.text_input("Email", key="login_email")
                    password = st.text_input(
                        "Password", type="password", key="login_password"
                    )
                    submit_button = st.form_submit_button(label="Login")

                    if submit_button:
                        try:
                            response = supabase.auth.sign_in_with_password(
                                {"email": email, "password": password}
                            )
                            st.session_state.user = response.user
                            st.session_state.access_token = (
                                response.session.access_token
                            )
                            st.success("Login successful!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Login failed: {str(e)}")

            with tab2:
                with st.form(key="signup_form"):
                    email = st.text_input("Email", key="signup_email")
                    password = st.text_input(
                        "Password", type="password", key="signup_password"
                    )
                    submit_button = st.form_submit_button(label="Sign Up")

                    if submit_button:
                        try:
                            response = supabase.auth.sign_up(
                                {"email": email, "password": password}
                            )
                            st.success(
                                "Sign up successful! Please check your email to confirm your account."
                            )
                        except Exception as e:
                            st.error(f"Sign up failed: {str(e)}")

    # Sidebar with profile information
    with st.sidebar:
        if st.session_state.user:
            # Replace dropdown with separate buttons
            view_history = st.button("📚 View Reading History")

            # Query parameters now wrapped in an expander
            with st.expander("🔍 Query Parameters", expanded=True):
                # Arrange question and language side by side
                col1, col2 = st.columns([2, 1])
                with col1:
                    user_query = st.text_area(
                        "📜 Enter your question:",
                        height=150,
                        placeholder="Type your detailed question here...",
                    )
                with col2:
                    try:
                        languages_response = requests.get(f"{API_URL}/languages")
                        languages = languages_response.json().get(
                            "languages", ["English", "Chinese"]
                        )
                    except Exception as e:
                        st.error(f"Error fetching languages: {str(e)}")
                        languages = ["English", "Chinese"]

                    language = st.selectbox("🌍 Language:", options=languages)

                # Arrange number inputs in a single row
                st.markdown("##### 🧮 Enter your numbers:")
                col3, col4, col5 = st.columns(3)
                with col3:
                    first = st.number_input("First number:", value=0, step=1)
                with col4:
                    second = st.number_input("Second number:", value=0, step=1)
                with col5:
                    third = st.number_input("Third number:", value=0, step=1)

                submit_query = st.button("🔮 Submit Query")

            # Add many line breaks to push content to bottom
            st.markdown("<br>" * 20, unsafe_allow_html=True)

            # Add a horizontal divider
            st.markdown(
                "<hr style='border-color: rgba(168, 85, 247, 0.4); margin: 1rem 0;'>",
                unsafe_allow_html=True,
            )

            # Profile section at the bottom
            st.markdown(
                f"""
                <div class="profile-section" style="border-left: 4px solid #A855F7;">
                    <p>👤 Logged in as: <strong>{st.session_state.user.email}</strong></p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Logout button right after profile info
            if st.button("🚪 Logout", key="logout_button"):
                supabase.auth.sign_out()
                st.session_state.user = None
                st.session_state.access_token = None
                st.rerun()
        else:
            st.markdown("#### 👋 Welcome to the Oracle")
            st.markdown("Please sign in to use the full features of the Oracle.")
            view_history = False
            submit_query = False

    # Create main content area
    main_content = st.container()

    with main_content:
        # Handle query submission
        if submit_query:
            if "user" not in st.session_state or st.session_state.user is None:
                st.warning(
                    "⚠️ Please sign in to use the Oracle. Your readings will be saved to your account."
                )
                st.info("Sign in using the login form at the top of the page.")
            else:
                with st.spinner("🔮 Consulting the Oracle..."):
                    try:
                        payload = {
                            "question": user_query,
                            "first_number": first,
                            "second_number": second,
                            "third_number": third,
                            "language": language,
                        }

                        headers = {
                            "Authorization": f"Bearer {st.session_state.access_token}"
                        }

                        response = requests.post(
                            f"{API_URL}/oracle", json=payload, headers=headers
                        )

                        if response.status_code == 200:
                            structured_output = response.json()
                            st.session_state.prediction_result = structured_output
                            st.session_state.query_submitted = True

                            st.markdown(
                                '<div class="prediction-header"><h2 style="color: #A855F7;">📜 Oracle\'s Response</h2></div>',
                                unsafe_allow_html=True,
                            )
                            display_formatted_prediction(structured_output)

                            if st.session_state.user:
                                supabase.table("user_readings").insert(
                                    {
                                        "user_id": st.session_state.user.id,
                                        "question": user_query,
                                        "first_number": first,
                                        "second_number": second,
                                        "third_number": third,
                                        "language": language,
                                        "prediction": structured_output,
                                    }
                                ).execute()
                        else:
                            st.error(f"Error: {response.status_code} - {response.text}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

        # Handle reading history view
        elif view_history and st.session_state.user:
            try:
                headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
                response = requests.get(f"{API_URL}/user/readings", headers=headers)

                if response.status_code == 200:
                    readings = response.json()

                    # Sort readings by created_at in descending order (newest first)
                    readings.sort(key=lambda x: x.get("created_at", ""), reverse=True)

                    st.markdown(
                        '<h2 class="sub-header" style="color: #A855F7; border-bottom: 2px solid rgba(168, 85, 247, 0.4);">📚 Your Reading History</h2>',
                        unsafe_allow_html=True,
                    )

                    if not readings:
                        st.markdown(
                            '<div class="light-purple-box">You don\'t have any readings yet. Submit a query to get started!</div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        for reading in readings:
                            with st.expander(
                                f"📅 {reading['created_at']} - {reading['question']}"
                            ):
                                st.markdown(
                                    f"""<div class="light-purple-box">
                                    <p><strong>Question:</strong> {reading['question']}</p>
                                    <p><strong>Numbers:</strong> {reading['first_number']}, {reading['second_number']}, {reading['third_number']}</p>
                                    <p><strong>Language:</strong> {reading['language']}</p>
                                    </div>""",
                                    unsafe_allow_html=True,
                                )

                                # Directly display the prediction if available
                                if "prediction" in reading and reading["prediction"]:
                                    st.markdown(
                                        '<hr style="border-color: rgba(168, 85, 247, 0.4);">',
                                        unsafe_allow_html=True,
                                    )
                                    st.markdown(
                                        '<h3 style="color: #A855F7;">🔮 Oracle\'s Prediction</h3>',
                                        unsafe_allow_html=True,
                                    )
                                    display_formatted_prediction(reading["prediction"])
                else:
                    st.error(f"Error fetching reading history: {response.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

        # Show welcome message in all other cases
        else:
            # Reset query_submitted if nothing else is being displayed
            if (
                st.session_state.query_submitted
                and not submit_query
                and not view_history
            ):
                st.session_state.query_submitted = False

            # Show welcome message
            st.markdown(
                """
                <div class="welcome-message">
                    <h2 style="color: #A855F7;">🧘 Welcome to the I Ching Oracle</h2>
                    <div class="purple-box">
                        <p>Ask the Oracle a question and receive guidance from ancient wisdom</p>
                        <p>The I Ching, or "Book of Changes," is an ancient Chinese divination system 
                        used for over 3,000 years to provide guidance and wisdom.</p>
                        <br>
                        <p>To begin, enter your question and three numbers in the sidebar, then click "Submit Query".</p>
                    </div>
                </div>
            """,
                unsafe_allow_html=True,
            )

            # Display placeholder image or illustration
            # If you have an image, uncomment this:
            # st.image("path/to/welcome_image.png", use_container_width=True)


def display_formatted_prediction(prediction: dict) -> None:
    """
    Display the prediction in a specific order with proper formatting.

    Order:
    1. Hexagram name
    2. Summary
    3. Interpretation
    4. Line change (line, interpretation)
    5. Result (name, interpretation)
    6. Advice
    """
    if not prediction:
        return

    # Use columns to create a better layout
    col1, col2 = st.columns([1, 2])

    # Main hexagram section
    if "hexagram_name" in prediction:
        st.markdown(
            '<h3 class="hexagram-title">🔯 Hexagram</h3>', unsafe_allow_html=True
        )
        # Use custom purple box for hexagram name
        st.markdown(
            f'<div class="purple-box"><span style="color: #A855F7; font-weight: 600;">Hexagram:</span> {prediction["hexagram_name"]}</div>',
            unsafe_allow_html=True,
        )

    # Summary in a custom purple box
    if "summary" in prediction:
        st.markdown('<h3 class="summary-text">📝 Summary</h3>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="light-purple-box"><span style="color: #A855F7; font-weight: 600;">Summary:</span> {prediction["summary"]}</div>',
            unsafe_allow_html=True,
        )

    # Interpretation with purple box
    if "interpretation" in prediction:
        st.markdown(
            '<h3 class="interpretation-text">📖 Interpretation</h3>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="purple-box"><span style="color: #A855F7; font-weight: 600;">Interpretation:</span> {prediction["interpretation"]}</div>',
            unsafe_allow_html=True,
        )

    # Line change section with columns
    if "line_change" in prediction and isinstance(prediction["line_change"], dict):
        st.markdown(
            '<h3 class="line-change-text">🔄 Line Change</h3>', unsafe_allow_html=True
        )

        # Use columns for image and text
        img_col, text_col = st.columns([1, 1])

        with img_col:
            image_path = prediction.get("image_path")
            if image_path:
                try:
                    st.image(
                        image_path,
                        caption="Line Change",
                        use_container_width=True,
                        output_format="PNG",
                    )
                except Exception as e:
                    st.error(f"Error displaying image: {str(e)}")

        with text_col:
            line_change = prediction["line_change"]

            if "line" in line_change or "interpretation" in line_change:
                line_html = '<div class="light-purple-box">'

                if "line" in line_change:
                    line_html += f'<div style="margin-bottom: 12px;"><span style="color: #A855F7; font-weight: 600;">Line:</span> {line_change["line"]}</div>'

                if "interpretation" in line_change:
                    line_html += f'<div><span style="color: #A855F7; font-weight: 600;">Interpretation:</span> {line_change["interpretation"]}</div>'

                line_html += "</div>"
                st.markdown(line_html, unsafe_allow_html=True)

    # Result section with purple box
    if "result" in prediction and isinstance(prediction["result"], dict):
        st.markdown('<h3 class="hexagram-title">🏁 Result</h3>', unsafe_allow_html=True)
        result = prediction["result"]

        # Create formatted result content with enhanced styling
        result_html = '<div class="purple-box">'

        if "name" in result:
            result_html += f'<div style="margin-bottom: 12px;"><span style="color: #A855F7; font-weight: 600;">Name:</span> {result["name"]}</div>'

        if "interpretation" in result:
            result_html += f'<div><span style="color: #A855F7; font-weight: 600;">Interpretation:</span> {result["interpretation"]}</div>'

        result_html += "</div>"

        # Display with custom purple box
        st.markdown(result_html, unsafe_allow_html=True)

    # Advice in a custom purple box
    if "advice" in prediction:
        st.markdown('<h3 class="summary-text">🧙‍♂️ Advice</h3>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="light-purple-box"><span style="color: #A855F7; font-weight: 600;">Advice:</span> {prediction["advice"]}</div>',
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
