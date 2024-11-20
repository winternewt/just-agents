from pathlib import Path
import pprint
from dotenv import load_dotenv
from llm_sandbox.micromamba import MicromambaSession
from llm_sandbox.docker import SandboxDockerSession

from just_agents_examples.coding.mounts import make_mounts, input_dir, output_dir, coding_examples_dir
from just_agents.base_agent import BaseAgent
from just_agents.interfaces.IAgent import IAgent
from just_agents.just_profile import JustAgentProfile
from just_agents.utils import build_agent
from just_agents.simple.llm_session import LLMSession
from just_agents_examples.coding.tools import write_thoughts_and_results, amino_match_endswith
from just_agents_examples.coding.mounts import input_dir, output_dir, coding_examples_dir

load_dotenv(override=True)

"""
This example shows how to use a simple code agent to run python code and bash commands, it does not use volumes and is based on basic LLMSession class.
"""

if __name__ == "__main__":
    ref="FLPMSAKS"
    #here we use claude sonnet 3.5 as default mode, if you want to switch to another please edit yaml
    config_path = coding_examples_dir / "coding_agents.yaml"
    agent: BaseAgent = BaseAgent.from_yaml("SimpleCodeAgent", file_path=config_path)
    result = agent.query("Get FGF2 human protein sequence from uniprot using biopython. As a result, return only the sequence")
    print("RESULT+++++++++++++++++++++++++++++++++++++++++++++++")
    pprint.pprint(result)
    #assert amino_match_endswith(result, ref), f"Sequence ending doesn't match reference {ref}: {result}"