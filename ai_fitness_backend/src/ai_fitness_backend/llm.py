import os
import re
import requests
import time
import logging
from typing import Any, Dict, List, Mapping, Optional
from dotenv import load_dotenv
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class HuggingFaceLLM(LLM):
    """Custom LLM implementation for Hugging Face models"""

    model_name: str = "mistralai/Mistral-7B-Instruct-v0.2"
    temperature: float = 0.7
    max_length: int = 1024

    @property
    def _llm_type(self) -> str:
        return "huggingface"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Call the Hugging Face API"""
        logger.info(f"Starting LLM request using model: {self.model_name}")
        start_time = time.time()

        api_token = os.getenv("HUGGINGFACE_API_TOKEN")
        if not api_token:
            logger.error("No HUGGINGFACE_API_TOKEN found in environment variables")
            raise Exception("Error: No API token found")

        headers = {"Authorization": f"Bearer {api_token}"}

        # Add system role if provided
        system_role = kwargs.get("system_role", "You are a helpful assistant.")
        full_prompt = f"{system_role}\n\n{prompt}"
        logger.info(f"Prompt length: {len(full_prompt)} characters")

        model_url = f"https://api-inference.huggingface.co/models/{self.model_name}"

        try:
            logger.info(f"Sending request to {model_url}")
            response = requests.post(
                model_url,
                headers=headers,
                json={
                    "inputs": full_prompt,
                    "parameters": {
                        "max_length": self.max_length,
                        "temperature": self.temperature,
                    },
                },
                timeout=180,  # Add timeout to prevent hanging indefinitely
            )

            request_time = time.time() - start_time
            logger.info(
                f"Request completed in {request_time:.2f} seconds with status code: {response.status_code}"
            )

            if response.status_code == 200:
                try:
                    response_json = response.json()
                    logger.info("Successfully parsed JSON response")

                    if isinstance(response_json, list) and len(response_json) > 0:
                        if "generated_text" in response_json[0]:
                            generated_text = response_json[0]["generated_text"]
                            logger.info(
                                f"Generated text length: {len(generated_text)} characters"
                            )

                            # Extract only the structured response part
                            clean_response = extract_structured_response(generated_text)
                            if clean_response:
                                logger.info(
                                    f"Extracted structured response of length: {len(clean_response)} characters"
                                )
                                return clean_response
                            else:
                                # If we couldn't extract the structured format, return the full response
                                logger.warning(
                                    "Could not extract structured response, returning full response"
                                )
                                return generated_text
                        else:
                            logger.error(
                                f"Missing 'generated_text' in response: {response_json}"
                            )
                            raise Exception(
                                f"Error: Unexpected response format - {response_json}"
                            )
                    else:
                        logger.error(f"Unexpected response structure: {response_json}")
                        raise Exception(
                            f"Error: Unexpected response structure - {response_json}"
                        )
                except Exception as e:
                    logger.error(f"Error parsing JSON response: {e}")
                    logger.error(f"Raw response: {response.text}")
                    raise Exception(f"Error parsing response: {e}")
            else:
                logger.error(
                    f"Error response: {response.status_code} - {response.text}"
                )
                raise Exception(f"Error: {response.status_code} - {response.text}")

        except requests.exceptions.Timeout:
            logger.error("Request timed out after 180 seconds")
            raise Exception("Error: Request to LLM timed out after 180 seconds")
        except Exception as e:
            logger.error(f"Exception during LLM request: {str(e)}")
            raise

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get the identifying parameters."""
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_length": self.max_length,
        }


def get_llm_client(
    model_name: str = "mistralai/Mistral-7B-Instruct-v0.2",
    temperature: float = 0.7,
    max_length: int = 1024,
) -> HuggingFaceLLM:
    """
    Get a LangChain-compatible LLM client using Hugging Face

    Args:
        model_name: The Hugging Face model to use
        temperature: Temperature for generation (higher = more creative)
        max_length: Maximum length of generated text

    Returns:
        A LangChain-compatible LLM client
    """
    return HuggingFaceLLM(
        model_name=model_name, temperature=temperature, max_length=max_length
    )


def get_llm_response(
    prompt,
    system_role="You are a helpful assistant.",
    model="mistralai/Mistral-7B-Instruct-v0.2",
):
    """Get a response from a free LLM model via Hugging Face"""
    # Create an instance of our custom LLM
    llm = HuggingFaceLLM(model_name=model)

    # Call the LLM with the system role as a keyword argument
    return llm._call(prompt, system_role=system_role)


def extract_structured_response(text):
    """Extract just the structured response part from the LLM output, skipping the instruction repetition"""
    # Find all occurrences of "OBSERVATIONS:" (case insensitive)
    # Look for all occurrences of each section header
    observations_matches = list(re.finditer(r"OBSERVATIONS:", text, re.IGNORECASE))
    suggestions_matches = list(
        re.finditer(r"DIETARY SUGGESTIONS:", text, re.IGNORECASE)
    )
    summary_matches = list(re.finditer(r"SUMMARY:", text, re.IGNORECASE))

    # If we found multiple occurrences of OBSERVATIONS, use the second one
    if len(observations_matches) > 1:
        # Get the position of the second occurrence
        start_index = observations_matches[1].start()
        return text[start_index:]

    # If we only found one occurrence of each section, we need to determine if it's the instruction or the content
    # We'll check if the first occurrence is followed by bullet points or actual content

    # Check if the first OBSERVATIONS is just repeating the instructions
    if observations_matches and len(observations_matches) == 1:
        obs_index = observations_matches[0].start()
        # Get the text after OBSERVATIONS: until the next section
        next_section_index = min(
            (
                m.start()
                for m in suggestions_matches + summary_matches
                if m.start() > obs_index
            ),
            default=len(text),
        )
        obs_text = text[obs_index:next_section_index].strip()

        # If this section contains bullet points with "List key observations" or similar instruction text
        if "List key observations" in obs_text or "Include patterns" in obs_text:
            # This is likely the instruction repetition, so look for content after all the instructions
            # Find where the last instruction section ends
            last_instruction_end = max(
                summary_matches[0].start() + len("SUMMARY:") if summary_matches else 0,
                (
                    suggestions_matches[0].start() + len("DIETARY SUGGESTIONS:")
                    if suggestions_matches
                    else 0
                ),
                (
                    observations_matches[0].start() + len("OBSERVATIONS:")
                    if observations_matches
                    else 0
                ),
            )

            # Find the next occurrence of any section header after the instructions
            next_section_matches = list(
                re.finditer(
                    r"(OBSERVATIONS:|DIETARY SUGGESTIONS:|SUMMARY:)",
                    text[last_instruction_end:],
                    re.IGNORECASE,
                )
            )

            if next_section_matches:
                # Return from this section onwards
                start_index = last_instruction_end + next_section_matches[0].start()
                return text[start_index:]

    # If we couldn't find a clear second occurrence or determine the instruction repetition,
    # fall back to the original logic

    # Look for the first real content section
    for section_name in ["OBSERVATIONS:", "DIETARY SUGGESTIONS:", "SUMMARY:"]:
        # Find all occurrences
        matches = list(re.finditer(section_name, text, re.IGNORECASE))

        for match in matches:
            start_idx = match.start()
            # Get some text after this section header
            sample_text = text[start_idx : start_idx + 200].lower()

            # Check if this looks like instruction repetition
            if (
                "list key observations" in sample_text
                or "provide specific dietary" in sample_text
                or "brief conclusion summarizing" in sample_text
            ):
                continue  # Skip this occurrence, it's likely the instruction

            # This looks like actual content
            return text[start_idx:]

    # If all else fails, return the original text
    logger.warning(
        "Could not extract clean structured response, returning full response"
    )
    return text
