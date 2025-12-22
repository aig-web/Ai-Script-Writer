import os
from pathlib import Path
from dotenv import load_dotenv

# Ensure .env is loaded
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.agents.prompts import RESEARCH_COMPRESSOR_PROMPT


class ResearchCompressor:
    def __init__(self):
        # OPENROUTER CONFIGURATION
        self.llm = ChatOpenAI(
            model="openai/gpt-4o-mini",  # OpenRouter Model ID
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0
        )

    def compress(self, raw_text: str) -> str:
        """
        Takes huge text (PDF/Search) -> Returns 6-8 Bullet Points
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", RESEARCH_COMPRESSOR_PROMPT),
            ("human", "{raw_text}")
        ])

        chain = prompt | self.llm
        # Context limit safety (approx 15k chars)
        result = chain.invoke({"raw_text": raw_text[:15000]})
        return result.content
