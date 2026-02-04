# This agent uses a Large Language Model (LLM) to clearly explain why a particular flight and hotel were chosen.
from langchain_core.messages import SystemMessage, HumanMessage

class ReasoningAgent:
    """
    Uses LLM to explain trade-offs clearly
    """
    # it only explains narrates and compares

    def explain(self, llm, flight: dict, hotel: dict) -> str:
        prompt = [
            SystemMessage(content="You are an expert travel advisor."),
            HumanMessage(
                content=f"""
                Explain why the following flight and hotel were selected.

                Flight:
                {flight}

                Hotel:
                {hotel}

                Clearly explain trade-offs and benefits.
                """
            )
        ]

        return llm.invoke(prompt).content
# Prompt is sent to the model,Model generates explanation,Only text output is returned