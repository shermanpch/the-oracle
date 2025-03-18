"""
Streamlit application for the Oracle I Ching Interpreter.

This module provides a web interface for the Oracle I Ching Interpreter using Streamlit.
"""

import logging
import os
import sys
import time

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

import streamlit as st

from src.app.web.utils.api import make_api_request
from src.app.web.utils.components import (
    display_auth_section,
    display_clarifying_qa,
    display_prediction_markdown,
    display_sidebar_welcome,
    display_welcome_message,
)
from src.app.web.utils.page_config import setup_page_config
from src.app.web.utils.session import initialize_session_state
from src.app.web.utils.styles import load_css

# Import centralized quota settings
from src.config.quotas import FREE_PLAN_QUOTA, LOW_QUOTA_THRESHOLD, PREMIUM_PLAN_QUOTA
from src.utils.supabase_client import get_supabase_client


def main():
    """
    Main function to run the Streamlit application for 'The Oracle - I Ching Interpreter'.
    """
    # Initialize Supabase client
    supabase = get_supabase_client()

    # Set up page configuration
    setup_page_config()

    # Load CSS styles from the static file
    load_css()

    # Initialize session state variables
    initialize_session_state()

    st.markdown(
        '<h1 class="main-header">🔮 The Oracle - I Ching Interpreter</h1>',
        unsafe_allow_html=True,
    )

    if not st.session_state.query_submitted and not st.session_state.user:
        display_welcome_message()

    # Authentication section
    if not st.session_state.user:
        display_auth_section(supabase)

    with st.sidebar:
        if not st.session_state.user:
            display_sidebar_welcome()
        else:
            if st.button("👤 View Profile"):
                st.session_state.view_profile = True
                st.session_state.view_history = False
                st.session_state.query_submitted = False
                st.session_state.follow_up_submitted = False
            if st.button("📚 View Reading History"):
                st.session_state.view_history = True
                st.session_state.view_profile = False
                st.session_state.query_submitted = False
                st.session_state.follow_up_submitted = False

            with st.expander("🔍 Query Parameters", expanded=True):
                col1, col2 = st.columns([2, 1])
                with col1:
                    user_query = st.text_area(
                        "📜 Enter your question:",
                        height=150,
                        placeholder="Type your detailed question here...",
                    )
                with col2:
                    languages = ["English", "Chinese"]
                    languages_data = make_api_request("languages")
                    if languages_data:
                        languages = languages_data.get("languages", languages)

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

                if st.button("🔮 Submit Query"):
                    st.session_state.query_submitted = True
                    st.session_state.view_history = False
                    st.session_state.follow_up_submitted = False
                    st.session_state.follow_up_question = None
                    st.session_state.follow_up_answer = None
                    st.session_state.oracle_call_completed = False
                    st.session_state.reading_saved = False
                    if "last_oracle_response" in st.session_state:
                        del st.session_state.last_oracle_response

            # Add many line breaks to push content to bottom
            st.markdown("<br>" * 27, unsafe_allow_html=True)

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
                st.session_state.query_submitted = False
                st.session_state.view_history = False
                st.session_state.follow_up_submitted = False
                st.rerun()

    # Create main content area
    main_content = st.container()

    with main_content:
        # SCENARIO 1: Follow-up question has been submitted
        if st.session_state.follow_up_submitted and st.session_state.reading_id:
            logger.info(
                f"RUNNING SCENARIO 1: Follow-up question for reading ID {st.session_state.reading_id}"
            )

            # Reset the processing_follow_up flag for future queries
            st.session_state.processing_follow_up = False

            # Fetch the specific reading by ID using the new API endpoint
            headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
            reading = make_api_request(
                f"user/readings/{st.session_state.reading_id}", headers=headers
            )

            if reading:
                # Display the original prediction
                st.markdown(
                    '<div class="prediction-header"><h2 style="color: #A855F7;">📜 Oracle\'s Response</h2></div>',
                    unsafe_allow_html=True,
                )
                display_prediction_markdown(reading["prediction"])

                # Get the follow-up question
                follow_up_question = st.session_state.follow_up_question

                # Only process the follow-up question if we haven't already done so
                if st.session_state.follow_up_answer is None:
                    # Process the follow-up question through the API
                    with st.spinner("🔮 The Oracle is considering your question..."):
                        followup_payload = {
                            "question": follow_up_question,
                            "conversation_history": st.session_state.conversation_history,
                        }

                        headers = {
                            "Authorization": f"Bearer {st.session_state.access_token}"
                        }

                        response_data = make_api_request(
                            "oracle/followup",
                            method="POST",
                            payload=followup_payload,
                            headers=headers,
                        )

                        if response_data:
                            follow_up_response = response_data.get("response")

                            # Store the follow-up answer in session state
                            st.session_state.follow_up_answer = follow_up_response

                            # Update the reading in the database
                            update_payload = {
                                "reading_id": st.session_state.reading_id,
                                "clarifying_question": follow_up_question,
                                "clarifying_answer": follow_up_response,
                            }

                            update_result = make_api_request(
                                "user/readings/update",
                                method="POST",
                                payload=update_payload,
                                headers=headers,
                            )

                            if not update_result:
                                st.error(
                                    "Failed to save your follow-up question to the database."
                                )
                        else:
                            st.error("Error getting clarification from the Oracle.")

                # Display the follow-up Q&A
                if st.session_state.follow_up_answer:
                    display_clarifying_qa(
                        follow_up_question, st.session_state.follow_up_answer
                    )
            else:
                st.error("Unable to retrieve your reading. Please try again.")

        # SCENARIO 2: Initial query submission
        elif (
            st.session_state.query_submitted
            and st.session_state.user
            and not st.session_state.follow_up_submitted
            and not st.session_state.processing_follow_up
        ):
            logger.info(f"User {st.session_state.user.email} submitting initial query")

            # Check if we have already completed this Oracle call
            structured_output = None
            if st.session_state.oracle_call_completed and st.session_state.reading_id:
                # Use the stored response from the previous API call
                structured_output = st.session_state.last_oracle_response
            else:
                # Check remaining queries before making API call
                headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
                user_quota = make_api_request("user/quota", headers=headers)

                if user_quota and user_quota.get("remaining_queries", 0) > 0:
                    # Only make the API call if we haven't already done so and user has queries left
                    with st.spinner("🔮 Consulting the Oracle..."):
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
                        structured_output = make_api_request(
                            "oracle", method="POST", payload=payload, headers=headers
                        )

                        if structured_output:
                            # Decrement the user's quota
                            make_api_request(
                                "user/quota/decrement", method="POST", headers=headers
                            )

                            # Mark that we've completed this Oracle call to prevent duplicates
                            st.session_state.oracle_call_completed = True
                            st.session_state.last_oracle_response = structured_output
                        else:
                            # Reset flags if the API call failed
                            st.session_state.oracle_call_completed = False
                            if "last_oracle_response" in st.session_state:
                                del st.session_state.last_oracle_response
                else:
                    # Handle case where user has no queries left
                    st.error(
                        "You have no queries remaining. Please upgrade your membership to continue using the Oracle."
                    )
                    # Show a button to view profile
                    if st.button("View My Profile"):
                        st.session_state.view_profile = True
                        st.session_state.query_submitted = False
                        st.rerun()
                    return

            if structured_output:
                st.session_state.conversation_history.extend(
                    [
                        {"role": "user", "content": user_query},
                        {
                            "role": "assistant",
                            "content": str(structured_output),
                        },
                    ]
                )

                # Display the prediction
                st.markdown(
                    '<div class="prediction-header"><h2 style="color: #A855F7;">📜 Oracle\'s Response</h2></div>',
                    unsafe_allow_html=True,
                )

                display_prediction_markdown(structured_output)

                # Save reading to database
                reading_data = {
                    "user_id": st.session_state.user.id,
                    "question": user_query,
                    "first_number": first,
                    "second_number": second,
                    "third_number": third,
                    "language": language,
                    "prediction": structured_output,
                    "clarifying_question": None,
                    "clarifying_answer": None,
                }

                # Only save the reading if it hasn't been saved already in this session
                if st.session_state.user and not st.session_state.reading_saved:
                    headers = {
                        "Authorization": f"Bearer {st.session_state.access_token}"
                    }
                    save_response = make_api_request(
                        "user/readings",
                        method="POST",
                        payload=reading_data,
                        headers=headers,
                    )

                    if save_response and save_response.get("data"):
                        st.session_state.reading_id = save_response["data"][0]["id"]
                        st.session_state.reading_saved = True

                # Display form for follow-up question
                st.markdown(
                    '<h3 style="color: #A855F7;">❓ Ask a Clarifying Question</h3>',
                    unsafe_allow_html=True,
                )

                # Create a form with a callback approach
                st.text_area(
                    "Ask one clarifying question about your reading:",
                    key="follow_up_input",
                    height=100,
                    placeholder="Example: Can you explain more about the advice given?",
                )

                if st.button("Ask for Clarification", key="follow_up_button"):
                    follow_up_question = st.session_state.follow_up_input
                    if follow_up_question:
                        # Set up state variables for the follow-up
                        st.session_state.follow_up_question = follow_up_question
                        st.session_state.follow_up_submitted = True
                        st.session_state.query_submitted = False
                        st.session_state.processing_follow_up = True

                        # Process the follow-up question
                        with st.spinner(
                            "🔮 The Oracle is considering your question..."
                        ):
                            # Create the payload for the follow-up API call
                            followup_payload = {
                                "question": follow_up_question,
                                "conversation_history": st.session_state.conversation_history,
                            }

                            # Make the API call
                            headers = {
                                "Authorization": f"Bearer {st.session_state.access_token}"
                            }

                            response_data = make_api_request(
                                "oracle/followup",
                                method="POST",
                                payload=followup_payload,
                                headers=headers,
                            )

                            if response_data:
                                follow_up_response = response_data.get("response")
                                st.session_state.follow_up_answer = follow_up_response

                                # Update the reading in the database
                                update_payload = {
                                    "reading_id": st.session_state.reading_id,
                                    "clarifying_question": follow_up_question,
                                    "clarifying_answer": follow_up_response,
                                }

                                update_result = make_api_request(
                                    "user/readings/update",
                                    method="POST",
                                    payload=update_payload,
                                    headers=headers,
                                )

                                # Show the follow-up screen
                                st.rerun()
                            else:
                                st.error("Error getting clarification from the Oracle.")
                    else:
                        st.error("Please enter a follow-up question.")

            else:
                st.error("Error consulting the Oracle. Please try again.")

        # SCENARIO 3: View reading history
        elif st.session_state.view_history and st.session_state.user:
            logger.info(f"User {st.session_state.user.email} viewing reading history")
            headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
            readings = make_api_request("user/readings", headers=headers)

            if (
                readings is not None
            ):  # Check if API call was successful, even if empty list
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

                            display_prediction_markdown(reading["prediction"])

                            # Display clarifying Q&A if available
                            if reading.get("clarifying_question") and reading.get(
                                "clarifying_answer"
                            ):
                                display_clarifying_qa(
                                    reading["clarifying_question"],
                                    reading["clarifying_answer"],
                                    use_header=True,
                                )
            else:
                st.error("Error fetching reading history. Please try again.")

        # SCENARIO 4: View profile
        elif st.session_state.view_profile and st.session_state.user:
            logger.info(f"User {st.session_state.user.email} viewing profile")

            headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
            user_quota = make_api_request("user/quota", headers=headers)

            if user_quota:
                st.markdown(
                    '<h2 class="sub-header" style="color: #A855F7; border-bottom: 2px solid rgba(168, 85, 247, 0.4);">👤 Your Profile</h2>',
                    unsafe_allow_html=True,
                )

                # Calculate quota percentage for progress bar
                max_queries = (
                    PREMIUM_PLAN_QUOTA
                    if user_quota.get("membership_type") == "premium"
                    else FREE_PLAN_QUOTA
                )
                remaining = user_quota.get("remaining_queries", 0)
                used = max_queries - remaining
                quota_percentage = remaining / max_queries

                # Format the membership type with a badge
                membership_badge = (
                    "🌟 Premium"
                    if user_quota.get("membership_type") == "premium"
                    else "⭐ Free"
                )

                # Display profile info
                st.markdown(
                    f"""
                    <div class="light-purple-box">
                    <p><strong>Email:</strong> {st.session_state.user.email}</p>
                    <p><strong>Membership:</strong> {membership_badge}</p>
                    <p><strong>Queries Remaining:</strong> {remaining} of {max_queries}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Add a progress bar for remaining queries
                st.progress(quota_percentage)

                if (
                    0 < remaining <= LOW_QUOTA_THRESHOLD
                    and user_quota.get("membership_type") == "free"
                ):
                    st.warning(
                        "⚠️ You're running low on available queries. Consider upgrading to Premium!"
                    )

                if remaining <= 0:
                    st.error(
                        "❌ You have no queries remaining. Please upgrade your membership to continue using the Oracle."
                    )

                # Add upgrade button for free users
                if user_quota.get("membership_type") == "free":
                    if st.button("🌟 Upgrade to Premium"):
                        spinner_container = st.empty()
                        with spinner_container.container():
                            st.spinner("Processing upgrade to Premium...")

                            upgrade_payload = {"membership_type": "premium"}
                            headers = {
                                "Authorization": f"Bearer {st.session_state.access_token}"
                            }
                            upgrade_result = make_api_request(
                                "user/quota/update",
                                method="POST",
                                payload=upgrade_payload,
                                headers=headers,
                            )

                        spinner_container.empty()

                        if upgrade_result and upgrade_result.get("status") == "success":
                            time.sleep(2.5)
                            st.success(
                                "✅ Successfully upgraded to Premium! You now have more queries available."
                            )
                            time.sleep(2.5)
                            st.rerun()
                        else:
                            st.error(
                                "Failed to upgrade your account. Please try again later."
                            )
            else:
                st.error(
                    "Unable to retrieve your profile information. Please try again."
                )

        # No specific scenario running - likely initial app load or after logout
        else:
            logger.info("Initial state or reset - no specific scenario active")


if __name__ == "__main__":
    main()
