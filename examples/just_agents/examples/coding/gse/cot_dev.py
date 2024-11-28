from typing import ClassVar, Optional, Literal, Any
from just_agents.base_agent import BaseAgent
from pydantic import BaseModel, Field
from just_agents.core.types import Output, SupportedMessages
from just_agents.core.interfaces.IAgent import IAgent
from just_agents.patterns.interfaces.IThinkingAgent import IThinkingAgent, IThought, THOUGHT_TYPE

class ActionableThought(IThought):
    """
    This is a thought object that is used to represent a thought in the chain of thought agent.
    """
    title: str = Field(..., description="Represents the title/summary of the current thinking step")
    content: str = Field(..., description="The detailed explanation/reasoning for this thought step")
    next_action: Literal["continue", "final_answer"] = Field(default="continue", description="Indicates whether to continue thinking or provide final answer")

    code: Optional[str] = Field(None, description="Optional field containing script code")
    console: Optional[str] = Field(None, description="Optional field containing console outputs")

    def is_final(self) -> bool:
        # Helper method to check if this is the final thought in the chain
        return self.next_action == "final_answer"


class ChainOfThoughtDevAgent(BaseAgent, IThinkingAgent[SupportedMessages, SupportedMessages, SupportedMessages, ActionableThought]):
    """
    Agen uses default prompt that instructs the agent to:
    1. Explain reasoning step by step
    2. Use at least 3 steps
    3. Consider limitations and alternative answers
    4. Use multiple methods to verify answers
    5. Format response as JSON with specific fields

    This prompt may be appended after the other custom prompt to introduce COT pattern
    """
    RESPONSE_FORMAT: ClassVar[str] = """
RESPONSE FORMAT:

Your input may contain 'final_answer' entries, consider these answers of other agents.   
For each step, provide a title that describes what you're doing in that step, along with the content.
Decide if you need another step or if you're ready to give the final answer. 
Respond in JSON format with 'title', 'content', 'code', 'console', and 'next_action' (either 'continue' or 'final_answer') keys.
Make sure you send only one JSON step object. You response should be a valid JSON object. In the JSON use Use Triple Quotes for Multi-line Strings.

USE AS MANY REASONING STEPS AS POSSIBLE. AT LEAST 3. 
BE AWARE OF YOUR LIMITATIONS AS AN LLM AND WHAT YOU CAN AND CANNOT DO. 
IN YOUR REASONING, INCLUDE EXPLORATION OF ALTERNATIVE ANSWERS. 
CONSIDER YOU MAY BE WRONG, AND IF YOU ARE WRONG IN YOUR REASONING, WHERE IT WOULD BE. 
FULLY TEST ALL OTHER POSSIBILITIES. 
YOU CAN BE WRONG. WHEN YOU SAY YOU ARE RE-EXAMINING, ACTUALLY RE-EXAMINE, AND USE ANOTHER APPROACH TO DO SO. 
DO NOT JUST SAY YOU ARE RE-EXAMINING. USE AT LEAST 3 METHODS TO DERIVE THE ANSWER. USE BEST PRACTICES.

Examples of a valid JSON response:
```json
{
  "title": "Identifying Key Information",
  "content": "To begin solving this problem, we need to carefully examine the given information and identify the crucial elements that will guide our solution process. This involves...",
  "next_action": "continue"
}```

```json
{
  "title": "Code to solve the problem",
  "content": "This code is expected to ... As a result the following should be produced: ...",
  "code": "\"\"
        import numpy as np
        ...
  \"\"",
  "next_action": "final_answer"
}```

```json
{
  "title": "Code execution observations",
  "content": "Code execution failed during ... , root cause of the problem likely is ..."
  "code": " "
  "console": "\"\"
      Traceback (most recent call last):
  \"\"",
  "next_action": "final_answer"
}```
"""

    # Allow customization of the system prompt while maintaining the default as fallback
    DEFAULT_COT_PROMPT: ClassVar[str] = """ You are an expert AI assistant that explains your reasoning step by step. 
    """
    system_prompt: str = Field(
        DEFAULT_COT_PROMPT,
        description="System prompt of the agent")

    response_format: str = Field(
        RESPONSE_FORMAT,
        description="System prompt of the agent")

    append_response_format: bool = Field(True, description="Whether to append default COT prompt of this agent to the provided")

    def model_post_init(self, __context: Any) -> None:
        # Call parent class's post_init first (from JustAgentProfile)
        super().model_post_init(__context)
        if self.append_response_format:
            system_prompt  = self.system_prompt + "\n\n" + self.response_format
            self.memory.clear_messages()
            self.instruct(system_prompt) # don't modify self system prompt to avoid saving it into profile

    def thought_query(self, query: SupportedMessages, **kwargs) -> ActionableThought:
        # Parses the LLM response into a structured ActionableThought object
        if self.supports_response_format and "gpt-4" in self.llm_options["model"]:  # despite what they declare only openai does support reponse format right
            return self.query_structural(query, parser=ActionableThought, response_format={"type": "json_object"}, **kwargs)
        else:
            return self.query_structural(query, parser=ActionableThought, **kwargs)



