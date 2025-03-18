"""
Page configuration utilities for the Streamlit app.
"""

import streamlit as st


def setup_page_config():
    """
    Set up the Streamlit page configuration with standard settings.

    This configures the page title, layout, initial sidebar state, and menu items.
    """
    st.set_page_config(
        page_title="The Oracle",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={"About": "The Oracle - I Ching Interpreter"},
    )
