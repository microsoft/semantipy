import os
import warnings
from typing import Literal

import dotenv
import pytest
from langchain_openai import AzureChatOpenAI, ChatOpenAI, AzureOpenAI, OpenAI

def load_env():
    # In case of a local environment, load the .env file
    if os.path.exists("tests/.env"):
        dotenv.load_dotenv("tests/.env")
    elif os.path.exists(".env"):
        dotenv.load_dotenv(".env")
    # The necessary environment variables should be already set on CI


@pytest.fixture(scope="session")
def llm():
    load_env()

    return AzureChatOpenAI(
        temperature=0.0,
        azure_deployment=os.environ["AZURE_DEPLOYMENT"],
        azure_endpoint=os.environ["AZURE_ENDPOINT"],
        api_version="2024-08-01-preview",
        api_key=os.environ["AZURE_API_KEY"],
        max_retries=10,
    )
