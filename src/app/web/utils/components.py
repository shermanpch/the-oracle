"""
UI component utilities for the Streamlit app.
"""

import streamlit as st


def display_welcome_message():
    """
    Display the main welcome message for the I Ching Oracle.
    """
    st.markdown(
        """
        <div class="welcome-message">
            <h2 style="color: #A855F7;">🧘 Welcome to the I Ching Oracle</h2>
            <div class="purple-box">
                <p>Ask the Oracle a question and receive guidance from ancient wisdom</p>
                <p>The I Ching, or "Book of Changes," is an ancient Chinese divination system 
                used for over 3,000 years to provide guidance and wisdom.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def display_auth_section(supabase):
    """
    Display the authentication section with login and signup forms.

    Args:
        supabase: Initialized Supabase client for authentication operations.
    """
    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
    with st.expander("📝 Sign in to continue", expanded=True):
        st.markdown(
            "<p>Please login or create an account to use the Oracle</p>",
            unsafe_allow_html=True,
        )
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
                        st.session_state.access_token = response.session.access_token
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


def display_sidebar_welcome():
    """
    Display the welcome message in the sidebar for non-logged in users.

    Returns:
        tuple: (view_history, submit_query) both set to False
    """
    st.markdown("#### 👋 Welcome")
    st.markdown("Please sign in above to use the Oracle.")


def display_prediction_markdown(prediction: dict) -> None:
    """
    Display the prediction in a specific order with proper markdown formatting.

    This function assumes all keys are present in the prediction dictionary.

    Parameters:
        prediction (dict): The prediction data to display

    Order:
    1. Hexagram name
    2. Summary
    3. Interpretation
    4. Line change (line, interpretation)
    5. Result (name, interpretation)
    6. Advice
    """
    # Main hexagram section
    st.markdown('<h3 class="hexagram-title">🔯 Hexagram</h3>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="purple-box"><span style="color: #A855F7; font-weight: 600;">Hexagram:</span> {prediction["hexagram_name"]}</div>',
        unsafe_allow_html=True,
    )

    # Summary in a custom purple box
    st.markdown('<h3 class="summary-text">📝 Summary</h3>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="light-purple-box"><span style="color: #A855F7; font-weight: 600;">Summary:</span> {prediction["summary"]}</div>',
        unsafe_allow_html=True,
    )

    # Interpretation with purple box
    st.markdown(
        '<h3 class="interpretation-text">📖 Interpretation</h3>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="purple-box"><span style="color: #A855F7; font-weight: 600;">Interpretation:</span> {prediction["interpretation"]}</div>',
        unsafe_allow_html=True,
    )

    # Line change section with columns
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
        line = line_change.get("line", "")
        interpretation = line_change.get("interpretation", "")

        line_html = '<div class="light-purple-box">'

        if line:
            line_html += f'<div style="margin-bottom: 12px;"><span style="color: #A855F7; font-weight: 600;">Line:</span> {line}</div>'

        if interpretation:
            line_html += f'<div><span style="color: #A855F7; font-weight: 600;">Interpretation:</span> {interpretation}</div>'

        line_html += "</div>"
        st.markdown(line_html, unsafe_allow_html=True)

    # Result section with purple box
    st.markdown('<h3 class="hexagram-title">🏁 Result</h3>', unsafe_allow_html=True)
    result = prediction["result"]
    name = result.get("name", "")
    interpretation = result.get("interpretation", "")

    # Create formatted result content with enhanced styling
    result_html = '<div class="purple-box">'

    if name:
        result_html += f'<div style="margin-bottom: 12px;"><span style="color: #A855F7; font-weight: 600;">Name:</span> {name}</div>'

    if interpretation:
        result_html += f'<div><span style="color: #A855F7; font-weight: 600;">Interpretation:</span> {interpretation}</div>'

    result_html += "</div>"

    # Display with custom purple box
    st.markdown(result_html, unsafe_allow_html=True)

    # Advice in a custom purple box
    st.markdown('<h3 class="summary-text">🧙‍♂️ Advice</h3>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="light-purple-box"><span style="color: #A855F7; font-weight: 600;">Advice:</span> {prediction["advice"]}</div>',
        unsafe_allow_html=True,
    )

    # Add a separator after the prediction
    st.markdown(
        '<hr style="border-color: rgba(168, 85, 247, 0.4); margin: 2rem 0 1rem 0;">',
        unsafe_allow_html=True,
    )


def display_clarifying_qa(question: str, answer: str, use_header: bool = True) -> None:
    """
    Display a clarifying question and answer with consistent styling.

    Parameters:
        question (str): The clarifying question
        answer (str): The Oracle's answer to the clarifying question
        use_header (bool): Whether to display the section header (default: True)
    """
    if use_header:
        st.markdown(
            '<h3 class="summary-text">❓ Your Clarifying Question</h3>',
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
        <div class="light-purple-box">
        <div style="margin-bottom: 12px;"><span style="color: #A855F7; font-weight: 600;">Question:</span> {question}</div>
        <div><span style="color: #A855F7; font-weight: 600;">Answer:</span> {answer}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Add a separator after the Q&A
    st.markdown(
        '<hr style="border-color: rgba(168, 85, 247, 0.4); margin: 2rem 0 1rem 0;">',
        unsafe_allow_html=True,
    )
