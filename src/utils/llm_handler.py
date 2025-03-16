import os

from dotenv import load_dotenv
from openai import OpenAI

from src.app.core.output import IChingOutput


def get_api_key(source: str = "env") -> str:
    """
    Retrieve the OpenAI API key from the specified source.

    Parameters:
        source (str): The source from which to load the API key.
                      Use "env" to load from a .env file and environment variables,
                      or "streamlit" to load from Streamlit's secrets.

    Returns:
        str: The OpenAI API key.

    Raises:
        ValueError: If the API key is not found in the specified source.
    """
    if source == "env":
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
    elif source == "streamlit":
        import streamlit as st

        api_key = st.secrets.get("OPENAI_API_KEY")
    else:
        raise ValueError(f"Unknown API key source: {source}")

    if not api_key:
        raise ValueError(
            "OpenAI API Key not found. Set it in your .env file or in Streamlit secrets."
        )
    return api_key


SYSTEM_PROMPT_FILE = os.path.join(os.path.dirname(__file__), "system_prompt.txt")


def load_system_prompt() -> str:
    """
    Load the system prompt from an external file.

    Returns:
        str: The system prompt.
    """
    if not os.path.exists(SYSTEM_PROMPT_FILE):
        raise FileNotFoundError(f"System prompt file '{SYSTEM_PROMPT_FILE}' not found.")

    with open(SYSTEM_PROMPT_FILE, "r") as f:
        return f.read()


def query_llm(
    user_input: str,
    parent_content: str,
    child_content: str,
    language: str,
    api_source: str = "env",
) -> IChingOutput:
    """
    Query the LLM using the provided user input and document context, and return the parsed response.

    This function loads the system prompt, fills in the placeholders with the provided context (language,
    parent_content, child_content), retrieves the API key using the specified source (either from the .env
    file or from Streamlit secrets), initializes the OpenAI client, and sends the query to the LLM.
    The response is parsed into an IChingOutput format.

    Parameters:
        user_input (str): The user's question.
        parent_content (str): Content from the parent document.
        child_content (str): Content from the child document.
        language (str): The language to be used in the query.
        api_source (str): Source to load the API key ("env" or "streamlit"). Defaults to "env".

    Returns:
        IChingOutput: The parsed LLM response.

    Raises:
        Exception: Propagates any exceptions raised during the LLM query or parsing process.
    """
    system_prompt_template = load_system_prompt()

    system_prompt = system_prompt_template.format(
        language=language,
        parent_context=parent_content,
        child_context=child_content,
    )

    OPENAI_API_KEY = get_api_key(source=api_source)
    client = OpenAI(api_key=OPENAI_API_KEY)

    response = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ],
        response_format=IChingOutput,
    )

    event = response.choices[0].message.parsed
    return event
