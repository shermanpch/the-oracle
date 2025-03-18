"""
Utility functions for handling CSS styles in the Streamlit app.
"""

import os

import streamlit as st


def load_css(file_name="styles.css"):
    """
    Load and apply CSS styles to the Streamlit app.

    Args:
        file_name (str): The CSS file name in the static directory.

    Returns:
        None
    """
    # Get the current file's directory
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    css_path = os.path.join(current_dir, "static", file_name)

    # Check if file exists
    if not os.path.isfile(css_path):
        st.warning(f"CSS file not found: {css_path}")
        return

    # Read the CSS file
    with open(css_path, "r") as f:
        css = f.read()

    # Apply the CSS to the Streamlit app
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
