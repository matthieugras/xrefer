# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from time import time, sleep
from typing import Type, TypeVar
from pydantic import BaseModel as PydanticBaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from xrefer.llm.base import BaseModel, ModelConfig
from xrefer.core.helpers import log

# Type variable for Pydantic models
T = TypeVar("T", bound=PydanticBaseModel)


class GoogleModel(BaseModel):
    """
    Google's LLM (PaLM/Gemini) implementation for XRefer.

    Handles interactions with Google's LLM APIs including rate limiting,
    token management, and response processing.

    Attributes:
        last_request_time (float): Timestamp of last API request
        requests_this_minute (int): Counter for rate limiting
    """

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.last_request_time = 0
        self.requests_this_minute = 0

    def get_max_input_tokens(self, ignore_limit: bool = False) -> int:
        """
        Get maximum allowed input tokens for Google's model.

        Args:
            ignore_limit (bool): If True, returns very large number instead of actual limit

        Returns:
            int: Maximum token limit (8192) or 1000000 if ignoring limits
        """
        if ignore_limit or self.config.ignore_token_limit:
            return 1000000  # gemini context windows are very large, however output tokens are very limited
        return 32768  # limiting input tokens to a small number to allow chunking, since large input sometimes means
        # large output requirements, unless the smaller limit is explicitly ignored

    def get_max_output_tokens(self) -> int:
        """
        Get maximum allowed output tokens for Google's model.

        Returns:
            int: Maximum output token limit (8192)
        """
        return 8192

    def validate_api_key(self) -> bool:
        """
        Validate Google API key by making test request.

        Returns:
            bool: True if API key is valid, False otherwise
        """
        try:
            self.get_client().invoke("Say 'API key is valid'")
            return True
        except Exception:
            return False

    def apply_rate_limit(self) -> None:
        """
        Apply rate limiting for Google API requests.

        Ensures requests don't exceed 10 per minute by tracking
        request times and sleeping if necessary.
        """
        current_time = time()
        if current_time - self.last_request_time >= 60:
            self.requests_this_minute = 0
            self.last_request_time = current_time
        elif self.requests_this_minute >= 10:
            sleep_time = 60 - (current_time - self.last_request_time)
            sleep(sleep_time)
            self.requests_this_minute = 0
            self.last_request_time = time()
        self.requests_this_minute += 1

    def get_client(self) -> ChatGoogleGenerativeAI:
        """
        Get configured Google LLM client.

        Returns:
            ChatGoogleGenerativeAI: Configured client ready for requests
        """
        return ChatGoogleGenerativeAI(
            model=self.config.model_name,
            google_api_key=self.config.api_key,
            max_output_tokens=self.get_max_output_tokens(),
        )

    def query_structured(self, prompt: str, schema: Type[T]) -> T:
        """
        Send query to Google's LLM with structured output.

        Uses LangChain's .with_structured_output() to ensure the response
        conforms to the provided Pydantic schema.

        Args:
            prompt (str): Prompt to send to model
            schema (Type[T]): Pydantic model class defining expected response structure

        Returns:
            T: Structured response conforming to the schema
        """
        log(f"Querying Google with prompt: {prompt}, schema: {schema}")
        self.apply_rate_limit()
        client = self.get_client()
        structured_client = client.with_structured_output(schema)
        return_value = structured_client.invoke(prompt)
        log(f"Google returned: {return_value}")
        return return_value


class OpenAIModel(BaseModel):
    """
    OpenAI's GPT implementation for XRefer.

    Handles interactions with OpenAI's API including token management
    and organization-aware configuration.
    """

    def get_max_input_tokens(self, ignore_limit: bool = False) -> int:
        """
        Get maximum allowed input tokens for OpenAI model.

        Args:
            ignore_limit (bool): If True, returns very large number instead of actual limit

        Returns:
            int: Maximum token limit (4096) or 124000 if ignoring limits
        """
        if ignore_limit or self.config.ignore_token_limit:
            return 124000  # gpt seems to be less restrictive on parallel queries
        return 8192  # output tokens are limited again, same rationale as above for smaller limit
        # that + smaller limit equals parallel queries which equals quicker processing

    def get_max_output_tokens(self) -> int:
        """
        Get maximum allowed output tokens for OpenAI model.

        Returns:
            int: Maximum output token limit (8192)
        """
        return 16384

    def validate_api_key(self) -> bool:
        """
        Validate OpenAI API key by making test request.

        Returns:
            bool: True if API key is valid, False otherwise
        """
        try:
            self.get_client().invoke("Say 'API key is valid'")
            return True
        except Exception as err:
            return False

    def apply_rate_limit(self) -> None:
        """
        Apply rate limiting for OpenAI API requests.

        Currently a no-op as OpenAI handles rate limiting server-side.
        """
        pass

    def get_client(self) -> ChatOpenAI:
        """
        Get configured OpenAI client.

        Creates client with appropriate model, API key and organization settings.

        Returns:
            ChatOpenAI: Configured client ready for requests
        """
        kwargs = {
            "model_name": self.config.model_name,
            "openai_api_key": self.config.api_key,
            "max_tokens": self.get_max_output_tokens(),
        }
        if self.config.organization:
            kwargs["openai_organization"] = self.config.organization
        return ChatOpenAI(**kwargs)

    def query_structured(self, prompt: str, schema: Type[T]) -> T:
        """
        Send query to OpenAI's LLM with structured output.

        Uses LangChain's .with_structured_output() to ensure the response
        conforms to the provided Pydantic schema.

        Args:
            prompt (str): Prompt to send to model
            schema (Type[T]): Pydantic model class defining expected response structure

        Returns:
            T: Structured response conforming to the schema
        """
        log(f"Querying OpenAI with prompt: {prompt}, schema: {schema}")
        client = self.get_client()
        structured_client = client.with_structured_output(schema)
        return_value = structured_client.invoke(prompt)
        log(f"OpenAI returned: {return_value}")
        return return_value
