from windows_use.agent.registry.views import ToolResult
from windows_use.agent.views import AgentStep, AgentData
from windows_use.desktop.views import DesktopState
from langchain.prompts import PromptTemplate
from importlib.resources import files
from datetime import datetime
from getpass import getuser
from textwrap import dedent
from pathlib import Path
import pyautogui as pg
import platform

class Prompt:
    @staticmethod
    def system_prompt(tools_prompt:str,max_steps:int,instructions: list[str]=[]) -> str:
        width, height = pg.size()
        template =PromptTemplate.from_file(files('windows_use.agent.prompt').joinpath('system.md'))
        return template.format(**{
            'current_datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'instructions': '\n'.join(instructions),
            'tools_prompt': tools_prompt,
            'os':platform.system(),
            'home_dir':Path.home().as_posix(),
            'user':getuser(),
            'resolution':f'{width}x{height}',
            'max_steps': max_steps
        })
    
    @staticmethod
    def action_prompt(agent_data:AgentData) -> str:
        template = PromptTemplate.from_file(files('windows_use.agent.prompt').joinpath('action.md'))
        return template.format(**{
            'evaluate': agent_data.evaluate,
            'memory':  agent_data.memory,
            'thought': agent_data.thought,
            'action_name': agent_data.action.name,
            'action_input': agent_data.action.params
        })
    
    @staticmethod
    def previous_observation_prompt(observation: str)-> str:
        template=PromptTemplate.from_template(dedent('''
        ```xml
        <Observation>{observation}</Observation>
        ```
        '''))
        return template.format(**{'observation': observation})
         
    @staticmethod
    def observation_prompt(agent_step: AgentStep, tool_result:ToolResult,desktop_state: DesktopState) -> str:
        cursor_position = pg.position()
        tree_state = desktop_state.tree_state
        template = PromptTemplate.from_file(files('windows_use.agent.prompt').joinpath('observation.md'))
        return template.format(**{
            'steps': agent_step.step_number,
            'max_steps': agent_step.max_steps,
            'observation': tool_result.content if tool_result.is_success else tool_result.error,
            'active_app': desktop_state.active_app_to_string(),
            'cursor_location': f'{cursor_position.x},{cursor_position.y}',
            'apps': desktop_state.apps_to_string(),
            'interactive_elements': tree_state.interactive_elements_to_string() or 'No interactive elements found',
            'informative_elements': tree_state.informative_elements_to_string() or 'No informative elements found',
            'scrollable_elements': tree_state.scrollable_elements_to_string() or 'No scrollable elements found',
        })
    
    @staticmethod
    def answer_prompt(agent_data: AgentData, tool_result: ToolResult):
        template = PromptTemplate.from_file(files('windows_use.agent.prompt').joinpath('answer.md'))
        return template.format(**{
            'evaluate': agent_data.evaluate,
            'memory':  agent_data.memory,
            'thought': agent_data.thought,
            'final_answer': tool_result.content
        })

    
