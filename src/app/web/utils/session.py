"""
Session state management utilities for the Streamlit app.
"""

import streamlit as st


def initialize_session_state():
    """
    Initialize all required session state variables.

    This ensures that all necessary session state variables exist with default values
    before they are accessed elsewhere in the application.
    """
    # User authentication state
    if "user" not in st.session_state:
        st.session_state.user = None

    # Follow-up question functionality
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []

    if "follow_up_submitted" not in st.session_state:
        st.session_state.follow_up_submitted = False

    if "follow_up_question" not in st.session_state:
        st.session_state.follow_up_question = None

    if "follow_up_answer" not in st.session_state:
        st.session_state.follow_up_answer = None

    # Reading state management
    if "reading_id" not in st.session_state:
        st.session_state.reading_id = None

    # UI state management
    if "query_submitted" not in st.session_state:
        st.session_state.query_submitted = False

    if "view_history" not in st.session_state:
        st.session_state.view_history = False

    # Token storage
    if "access_token" not in st.session_state:
        st.session_state.access_token = None

    # Flag to prevent duplicate API calls
    if "processing_follow_up" not in st.session_state:
        st.session_state.processing_follow_up = False

    # Flag to track if Oracle API call has already been made
    if "oracle_call_completed" not in st.session_state:
        st.session_state.oracle_call_completed = False

    # Flag to track if the current reading has been saved to the database
    if "reading_saved" not in st.session_state:
        st.session_state.reading_saved = False

    # Flag to track if the profile page is being viewed
    if "view_profile" not in st.session_state:
        st.session_state.view_profile = False
