"""Streamlit entry point for the local walking skeleton."""

import streamlit as st

from portfolio_rag.ui import ApiClientError, PortfolioApiClient, UiSettings


def run() -> None:
    """Render the message form and display the backend placeholder."""
    st.set_page_config(page_title="Portfolio Retrieval Lab", page_icon="🔎")
    st.title("Portfolio Retrieval Lab")
    st.caption("Phase 0 walking skeleton — responses are placeholders, not facts.")
    identity_assertion = st.context.headers.get("X-Amzn-Oidc-Data")
    access_token = st.context.headers.get("X-Amzn-Oidc-AccessToken")
    if identity_assertion is not None:
        st.markdown("[Sign out](/auth/logout)")

    message = st.chat_input("Ask about the portfolio")
    if message is None:
        return

    with st.chat_message("user"):
        st.write(message)

    client = PortfolioApiClient(UiSettings())
    with st.chat_message("assistant"):
        try:
            result = client.answer_message(
                message,
                identity_assertion=identity_assertion,
                access_token=access_token,
            )
        except ApiClientError as error:
            st.error(error.user_message)
            return
        st.warning(result.answer)


run()
