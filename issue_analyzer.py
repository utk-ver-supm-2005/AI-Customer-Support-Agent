import os

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field


# Load variables from .env
load_dotenv()

# Get Gemini API key
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY was not found in the .env file.")


# Create Gemini client
# One attempt only, with a 30-second timeout.
client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(
        timeout=30000,
        retry_options=types.HttpRetryOptions(
            attempts=1
        )
    )
)


# Structure of the AI's output
class IssueAnalysis(BaseModel):

    issue: str = Field(
        description="A concise description of the customer's main problem."
    )

    intent: str = Field(
        description="The main reason or purpose of the customer's support request."
    )

    entities: dict[str, str] = Field(
        description="Important entities mentioned by the customer, such as product, version, error code, feature, or account information."
    )

    context: str = Field(
        description="Important conversational or historical information relevant to the issue."
    )


def analyze_customer_request(customer_email: str) -> IssueAnalysis:

    prompt = f"""
You are an AI customer-support issue analysis system.

Analyze the following customer-support email.

Extract:

1. The customer's main issue.
2. The customer's intent or reason for contacting support.
3. Important entities such as product, version, error code,
   feature, account information, or other relevant identifiers.
4. Important context relevant to the issue.

Rules:
- Do not invent information.
- If information is not present, do not fabricate it.
- Return only the requested structured information.

Customer email:
----------------
{customer_email}
----------------
"""

    try:

        interaction = client.interactions.create(
            model="gemini-3.5-flash-lite",
            input=prompt,

            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": IssueAnalysis.model_json_schema()
            },

            generation_config={
                "thinking_level": "low"
            }
        )

        return IssueAnalysis.model_validate_json(
            interaction.output_text
        )

    except Exception as e:

        raise RuntimeError(
            f"Gemini API request failed: {e}"
        ) from e