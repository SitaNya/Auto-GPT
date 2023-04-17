"""Google search command for Autogpt."""
from __future__ import annotations

import json
from typing import List, Union

from duckduckgo_search import ddg

from autogpt.config import Config
from googleapiclient.errors import HttpError

CFG = Config()


def google_search(query: str, num_results: int = 8) -> str:
    """Return the results of a google search

    Args:
        query (str): The search query.
        num_results (int): The number of results to return.

    Returns:
        str: The results of the search.
    """
    search_results = []
    if not query:
        return json.dumps(search_results)

    results = ddg(query, max_results=num_results)
    if not results:
        return json.dumps(search_results)

    for j in results:
        search_results.append(j)

    return json.dumps(search_results, ensure_ascii=False, indent=4)


def google_official_search(query: str, num_results: int = 8) -> str | list[str]:
    """Return the results of a google search using the official Google API

    Args:
        query (str): The search query.
        num_results (int): The number of results to return.

    Returns:
        str: The results of the search.
    """

    from googleapiclient.discovery import build
    import json
    import os
    import pickle

    os.environ["http_proxy"] = "http://127.0.0.1:1431"
    os.environ["https_proxy"] = "http://127.0.0.1:1431"

    # Define a function to get and save access token
    def get_credentials(client_secrets_file):
        creds = None
        token_file = 'token.pickle'

        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                try:
                    creds = google.oauth2.credentials.Credentials.from_authorized_user_file(client_secrets_file)
                except ValueError as e: # first run with new secret.json (no refresh_token yet)
                    flow = InstalledAppFlow.from_client_secrets_file(
                        client_secrets_file=client_secrets_file,
                        scopes=['https://www.googleapis.com/auth/cse']
                    )
                    creds = flow.run_local_server(port=0)

            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)

        return creds
    try:
        # Get access token
        client_secrets_file = 'client_secrets.json'
        credentials = get_credentials(client_secrets_file)


        # Get the Custom Search Engine ID from the config file
        custom_search_engine_id = 'e2ef88cb25af145ff'

        # Initialize the Custom Search API service
        service = build("customsearch", "v1",credentials=credentials)

        # Send the search query and retrieve the results
        result = (
            service.cse()
            .list(q=query, cx=custom_search_engine_id, num=num_results)
            .execute()
        )

        # Extract the search result items from the response
        search_results = result.get("items", [])

        # Create a list of only the URLs from the search results
        search_results_links = [item["link"] for item in search_results]

    except HttpError as e:
        # Handle errors in the API call
        error_details = json.loads(e.content.decode())

        # Check if the error is related to an invalid or missing API key
        if error_details.get("error", {}).get(
            "code"
        ) == 403 and "invalid API key" in error_details.get("error", {}).get(
            "message", ""
        ):
            return "Error: The provided Google API key is invalid or missing."
        else:
            return f"Error: {e}"

    # Return the list of search result URLs
    return search_results_links
