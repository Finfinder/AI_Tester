"""Placeholder example: how an agent could generate code using LangChain/OpenAI and write it to task/agent_output.py.
This file is illustrative and not executed by the PoC by default.
"""
# pip install langchain openai
from pathlib import Path

EXAMPLE_CODE = '''def sum_list(xs):
    """Sums a list of numbers"""
    return sum(xs)
'''

def write_agent_output(path: Path):
    path.mkdir(parents=True, exist_ok=True)
    file = path / 'agent_output.py'
    file.write_text(EXAMPLE_CODE)
    print(f'Wrote generated code to {file}')

if __name__ == '__main__':
    write_agent_output(Path(__file__).parent / 'task')
