# backend/rag/llm.py
"""
LLM integration for generating answers from prompts.
"""
import os
from typing import Optional
from openai import OpenAI


# Initialize OpenAI client (will use OPENAI_API_KEY from environment)
_client: Optional[OpenAI] = None


def get_client() -> OpenAI:
    """Get or create OpenAI client instance."""
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is not set. "
                "Please set it to use the LLM functionality."
            )
        _client = OpenAI(api_key=api_key)
    return _client


def generate_answer(
    prompt: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.3,
    max_tokens: int = 500,
) -> str:
    """
    Generate an answer from a prompt using OpenAI API.
    
    Args:
        prompt: The prompt string to send to the LLM
        model: The model to use (default: gpt-4o-mini for cost efficiency)
        temperature: Sampling temperature (lower = more deterministic)
        max_tokens: Maximum tokens in response
        
    Returns:
        The generated answer text
    """
    client = get_client()
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that answers questions based on provided evidence. Be concise, accurate, and only use information from the evidence."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        answer = response.choices[0].message.content
        if not answer:
            return "I apologize, but I couldn't generate an answer. Please try again."
        
        return answer.strip()
    
    except Exception as e:
        # Fallback error message
        return f"I encountered an error while generating an answer: {str(e)}. Please check your API configuration."

