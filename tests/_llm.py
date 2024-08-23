import os
import warnings
from typing import Literal

import dotenv
import pytest
from langchain_openai import AzureChatOpenAI, ChatOpenAI, AzureOpenAI, OpenAI

# Chat model
model_chat: Literal["gpt-35-turbo", "gpt-4"] = "gpt-35-turbo"
endpoint_chat: Literal["aoai", "openai", "aiyyds", "gptapius"] = "gptapius"

# Text completion model
model_text: Literal["babbage-002", "davinci-002"] = "davinci-002"
endpoint_text: Literal["aoai", "openai", "aiyyds", "gptapius"] = "gptapius"


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

    if endpoint_chat == "aoai":
        if "OPENAI_API_BASE" in os.environ:
            # Misconfigured OPENAI_API_BASE can cause tests to fail
            del os.environ["OPENAI_API_BASE"]
        endpoint_key = os.environ["AOAI_ENDPOINT_KEY"]
        endpoint_base = os.environ["AOAI_ENDPOINT_BASE"]
        return AzureChatOpenAI(
            temperature=0.0,
            azure_deployment=model_chat,
            azure_endpoint=endpoint_base,
            api_version="2023-12-01-preview",
            api_key=endpoint_key,
            max_retries=30,
        )
    elif endpoint_chat in ("openai", "aiyyds", "gptapius"):
        if model_chat == "gpt-35-turbo":
            _model = "gpt-3.5-turbo"
        elif model_chat == "gpt-4":
            _model = "gpt-4o"
        else:
            warnings.warn(
                f"Unknown model '{model_chat}'. Please make sure you have the correct model name."
            )
            _model = model_chat
        return ChatOpenAI(
            temperature=0.0,
            model=_model,
            max_retries=10,
            timeout=60,
            max_tokens=1000,
        )
    else:
        raise ValueError(f"Invalid endpoint {endpoint_chat}")


@pytest.fixture(scope="session")
def gpt4():
    load_env()

    if endpoint_chat == "aoai":
        if "OPENAI_API_BASE" in os.environ:
            # Misconfigured OPENAI_API_BASE can cause tests to fail
            del os.environ["OPENAI_API_BASE"]
        endpoint_key = os.environ["AOAI_ENDPOINT_KEY"]
        endpoint_base = os.environ["AOAI_ENDPOINT_BASE"]
        return AzureChatOpenAI(
            temperature=0.0,
            azure_deployment="gpt-4",
            azure_endpoint=endpoint_base,
            api_version="2023-12-01-preview",
            api_key=endpoint_key,
            max_retries=30,
        )
    elif endpoint_chat in ("openai", "aiyyds"):
        return ChatOpenAI(
            temperature=0.0,
            model="gpt-4-turbo",
            max_retries=5,
            timeout=60,
            max_tokens=1000,
        )
    elif endpoint_chat == "gptapius":
        return ChatOpenAI(
            temperature=0.0,
            model="gpt-4o",
            max_retries=0,
            timeout=60,
        )
    else:
        raise ValueError(f"Invalid endpoint {endpoint_chat}")



@pytest.fixture(scope="session")
def llm_text():
    load_env()

    if endpoint_text == "aoai":
        if "OPENAI_API_BASE" in os.environ:
            # Misconfigured OPENAI_API_BASE can cause tests to fail
            del os.environ["OPENAI_API_BASE"]
        endpoint_key = os.environ["AOAI_ENDPOINT_KEY"]
        endpoint_base = os.environ["AOAI_ENDPOINT_BASE"]
        return AzureOpenAI(
            temperature=0.0,
            azure_deployment=model_text,
            azure_endpoint=endpoint_base,
            api_version="2023-12-01-preview",
            api_key=endpoint_key,
            max_retries=30,
        )
    elif endpoint_text in ("openai", "aiyyds"):
        return OpenAI(
            temperature=0.0,
            model=model_text,
            max_retries=10,
            timeout=60,
            max_tokens=1000,
        )
    else:
        raise ValueError(f"Invalid endpoint {endpoint_text}")
