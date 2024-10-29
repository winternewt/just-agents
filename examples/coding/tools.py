
from dotenv import load_dotenv
import requests
from just_agents.interfaces.IAgent import build_agent, IAgent
from just_agents.llm_session import LLMSession
from llm_sandbox.micromamba import MicromambaSession
from llm_sandbox.docker import SandboxDockerSession
from mounts import make_mounts, input_dir, output_dir

"""
Tools for running code in sandboxed environment that also mounts input and output directories.
"""

def download_file(source_url: str, file_name: str) -> bool:
    """ Download file from source_url and save it to '/input' folder with file_name that available mount for runtime. """
    input_path = input_dir / file_name
    try:
        print(f"Downloading: {source_url} to {input_path}")
        response = requests.get(source_url, stream=True)
        response.raise_for_status()

        with open(input_path, 'wb') as file:  # Remove encoding for binary write
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)

        print(f"File downloaded successfully and saved to {input_path}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
        return False




def ugly_log(text: str, folder: Path, name: str = "code", ext: str = "py"):
    """
    Logs code to a numbered file in the specified folder.
    Creates code_1.py if no files exist, otherwise increments the number.
    
    Args:
        text: str - The code text to log
        folder: Path - The folder where to save the file


    It is a temporal functin that will be removed soon.
    For logging purposesonly
    """
    # Create folder if it doesn't exist
    folder.mkdir(parents=True, exist_ok=True)
    
    # Find all existing code files
    existing_files = list(folder.glob(f"{name}_*.{ext}"))
    
    if not existing_files:
        # No files exist, create code_1.py
        new_file = folder / f"{name}_1.{ext}"
    else:
        # Find the highest number
        numbers = [int(f.stem.split('_')[1]) for f in existing_files]
        next_num = max(numbers) + 1
        new_file = folder / f"{name}_{next_num}.{ext}"
    
    # Write the code to the new file
    with new_file.open('w', encoding='utf-8') as f:
        f.write(text)

def run_bash_command(command: str) -> str:
    """
    command: str # command to run in bash, for example install software inside micromamba environment
    """
    mounts = make_mounts()
    try:
        with MicromambaSession(image="ghcr.io/longevity-genie/just-agents/biosandbox:main", 
                               lang="python", 
                               keep_template=True, 
                               verbose=True,
                               mounts=mounts) as session:
            result = session.execute_command(command=command)
            ugly_log(command, output_dir, "bash", "sh")
            return result
    except Exception as e:
        print(f"Error executing bash command: {e}")
        return str(e)

def run_python_code(code: str) -> str:
    """
    code: str # python code to run in micromamba environment
    """
    mounts = make_mounts()
    try:
        with MicromambaSession(image="ghcr.io/longevity-genie/just-agents/biosandbox:main", 
                               lang="python", 
                               keep_template=True, 
                               verbose=True,
                               mounts=mounts) as session:
            result = session.run(code)
            ugly_log(code, output_dir, "code", "py")
            return result
    except Exception as e:
        print(f"Error executing Python code: {e}")
        return str(e)


def write_thoughts_and_results(name: str, thoughts: str, result: str):
    """
    Write thoughts and results to a file in the output directory
    """
    print("Thoughts: ", thoughts)
    print("Result: ", result)
    # Create the output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    where = output_dir / f"thoughts_{name}.txt"
    # Write thoughts and results to the output file
    with where.open("w", encoding="utf-8") as f:
        f.write("Thoughts:\n")
        f.write(thoughts)
        f.write("\n\nResult:\n")
        f.write(result)
    
    print(f"Thoughts and results have been written to {where}")