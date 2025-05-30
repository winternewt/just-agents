from dotenv import load_dotenv
from just_agents.patterns.chain_of_throught import ChainOfThoughtAgent
import just_agents.llm_options

def count_letters(character: str, word: str) -> str:
    """ Returns the number of character occurrences in the word. """
    count:int = 0
    for char in word:
        if char == character:
            count += 1
    print("Function: ", character, " occurres in ", word, " ", count, " times.")
    return str(count)


def test_function_query():
    load_dotenv(override = True)

    llm_options = just_agents.llm_options.LLAMA4_SCOUT
    agent: ChainOfThoughtAgent = ChainOfThoughtAgent(llm_options=llm_options, tools=[count_letters])
    result, thoughts = agent.think("Count the number of occurrences of the letter 'L' in the word - 'LOLLAPALOOZA'.")
    print("Thoughts: ", thoughts)
    print("Results: ", result)
    assert "4" in result.content
