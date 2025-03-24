# ========= Copyright 2023-2024 @ CAMEL-AI.org. All Rights Reserved. =========
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ========= Copyright 2023-2024 @ CAMEL-AI.org. All Rights Reserved. =========

from typing import Dict, List, Optional, Tuple


from camel.agents import ChatAgent
from camel.responses import ChatAgentResponse
from camel.messages.base import BaseMessage
from camel.societies import RolePlaying
from camel.logger import get_logger


from copy import deepcopy

logger = get_logger(__name__)


class OwlRolePlaying(RolePlaying):
    def __init__(self, **kwargs):
        self.user_role_name = kwargs.get("user_role_name", "user")
        self.assistant_role_name = kwargs.get("assistant_role_name", "assistant")

        self.output_language = kwargs.get("output_language", None)

        self.user_agent_kwargs: dict = kwargs.get("user_agent_kwargs", {})
        self.assistant_agent_kwargs: dict = kwargs.get("assistant_agent_kwargs", {})

        self.output_language = kwargs.get("output_language", None)

        super().__init__(**kwargs)

        init_user_sys_msg, init_assistant_sys_msg = self._construct_gaia_sys_msgs()

        self.assistant_agent: ChatAgent
        self.user_agent: ChatAgent
        self.assistant_sys_msg: Optional[BaseMessage]
        self.user_sys_msg: Optional[BaseMessage]

        # self.is_reasoning_task = self._judge_if_reasoning_task(self.task_prompt)

        # if self.is_reasoning_task:
        #     logger.info("The task is judged as a reasoning or coding task. The assistant agent will use the reasoning model O3-MINI.")
        # else:
        #     logger.info("The assistant agent will use the default model.")

        self._init_agents(
            init_assistant_sys_msg,
            init_user_sys_msg,
            assistant_agent_kwargs=self.assistant_agent_kwargs,
            user_agent_kwargs=self.user_agent_kwargs,
            output_language=self.output_language,
            # is_reasoning_task=self.is_reasoning_task
        )

    def _init_agents(
        self,
        init_assistant_sys_msg: BaseMessage,
        init_user_sys_msg: BaseMessage,
        assistant_agent_kwargs: Optional[Dict] = None,
        user_agent_kwargs: Optional[Dict] = None,
        output_language: Optional[str] = None,
        is_reasoning_task: bool = False,
    ) -> None:
        r"""Initialize assistant and user agents with their system messages.

        Args:
            init_assistant_sys_msg (BaseMessage): Assistant agent's initial
                system message.
            init_user_sys_msg (BaseMessage): User agent's initial system
                message.
            assistant_agent_kwargs (Dict, optional): Additional arguments to
                pass to the assistant agent. (default: :obj:`None`)
            user_agent_kwargs (Dict, optional): Additional arguments to
                pass to the user agent. (default: :obj:`None`)
            output_language (str, optional): The language to be output by the
                agents. (default: :obj:`None`)
        """
        if self.model is not None:
            if assistant_agent_kwargs is None:
                assistant_agent_kwargs = {"model": self.model}
            elif "model" not in assistant_agent_kwargs:
                assistant_agent_kwargs.update(dict(model=self.model))
            if user_agent_kwargs is None:
                user_agent_kwargs = {"model": self.model}
            elif "model" not in user_agent_kwargs:
                user_agent_kwargs.update(dict(model=self.model))

        # # If the task is a reasoning task, the assistant agent should use the reasoning model O3-MINI
        # if is_reasoning_task:
        #     assistant_agent_kwargs['model'] = ModelFactory.create(
        #         model_platform=ModelPlatformType.OPENAI,
        #         model_type=ModelType.O3_MINI,
        #     )

        self.assistant_agent = ChatAgent(
            init_assistant_sys_msg,
            output_language=output_language,
            **(assistant_agent_kwargs or {}),
        )
        self.assistant_sys_msg = self.assistant_agent.system_message

        self.user_agent = ChatAgent(
            init_user_sys_msg,
            output_language=output_language,
            **(user_agent_kwargs or {}),
        )
        self.user_sys_msg = self.user_agent.system_message

    # def _judge_if_reasoning_task(self, question: str) -> bool:
    #     r"""Judge if the question is a reasoning task."""

    #     LLM = OpenAIModel(model_type=ModelType.O3_MINI)
    #     prompt = f"""
    #     Please judge whether the following question is a reasoning or coding task, which can be solved by reasoning without leveraging external resources, or is suitable for writing code to solve the task.
    #     If it is a reasoning or coding task, please return only "yes".
    #     If it is not a reasoning or coding task, please return only "no".
    #     Note:
    #     - If the question required some world knowledge to answer the question, please carefully judge it, because the model's own knowledge is often unreliable.
    #     - If it is suitable for writing codes (e.g. process excel files, write simulation codes, etc.), in most cases, it can be considered as a coding task.
    #     Question: <question>{question}</question>
    #     """
    #     messages = [{"role": "user", "content": prompt}]
    #     resp = LLM.run(messages)
    #     if 'yes' in resp.choices[0].message.content.lower():
    #         return True
    #     else:
    #         return False

    def _construct_gaia_sys_msgs(self):
        user_system_prompt = f"""
===== RULES OF USER =====
Never forget you are a user and I am a assistant. Never flip roles! You will always instruct me. We share a common interest in collaborating to successfully complete a task.
I must help you to complete a difficult task.
You must instruct me based on my expertise and your needs to solve the task step by step. The format of your instruction is: `Instruction: [YOUR INSTRUCTION]`, where "Instruction" describes a sub-task or question.
You must give me one instruction at a time.
I must write a response that appropriately solves the requested instruction.
You should instruct me not ask me questions.

Please note that the task may be very complicated. Do not attempt to solve the task by single step. You must instruct me to find the answer step by step.
Here are some tips that will help you to give more valuable instructions about our task to me:
<tips>
- I have various tools to use, such as search toolkit, web browser simulation toolkit, document relevant toolkit, code execution toolkit, etc. Thus, You must think how human will solve the task step-by-step, and give me instructions just like that. For example, one may first use google search to get some initial information and the target url, then retrieve the content of the url, or do some web browser interaction to find the answer.
- Although the task is complex, the answer does exist. If you can't find the answer using the current scheme, try to re-plan and use other ways to find the answer, e.g. using other tools or methods that can achieve similar results.
- Always remind me to verify my final answer about the overall task. This work can be done by using multiple tools(e.g., screenshots, webpage analysis, etc.), or something else.
- If I have written code, please remind me to run the code and get the result.
- Search results typically do not provide precise answers. It is not likely to find the answer directly using search toolkit only, the search query should be concise and focuses on finding sources rather than direct answers, as it always need to use other tools to further process the url, e.g. interact with the webpage, extract webpage content, etc. 
- If the question mentions youtube video, in most cases you have to process the content of the mentioned video.
- For downloading files, you can either use the web browser simulation toolkit or write codes (for example, the github content can be downloaded via https://raw.githubusercontent.com/...).
- Flexibly write codes to solve some problems, such as excel relevant tasks.
</tips>

Now, here is the overall task: <task>{self.task_prompt}</task>. Never forget our task!

Now you must start to instruct me to solve the task step-by-step. Do not add anything else other than your instruction!
Keep giving me instructions until you think the task is completed.
When the task is completed, you must only reply with a single word <TASK_DONE>.
Never say <TASK_DONE> unless my responses have solved your task.
        """

        assistant_system_prompt = f"""
===== RULES OF ASSISTANT =====
Never forget you are a assistant and I am a user. Never flip roles! Never instruct me! You have to utilize your available tools to solve the task I assigned.
We share a common interest in collaborating to successfully complete a complex task.
You must help me to complete the task.

Here is our overall task: {self.task_prompt}. Never forget our task!

I must instruct you based on your expertise and my needs to complete the task. An instruction is typically a sub-task or question.

You must leverage your available tools, try your best to solve the problem, and explain your solutions.
Unless I say the task is completed, you should always start with:
Solution: [YOUR_SOLUTION]
[YOUR_SOLUTION] should be specific, including detailed explanations and provide preferable detailed implementations and examples and lists for task-solving.

Please note that our overall task may be very complicated. Here are some tips that may help you solve the task:
<tips>
- If one way fails to provide an answer, try other ways or methods. The answer does exists.
- If the search snippet is unhelpful but the URL comes from an authoritative source, try visit the website for more details.  
- When looking for specific numerical values (e.g., dollar amounts), prioritize reliable sources and avoid relying only on search snippets.  
- When solving tasks that require web searches, check Wikipedia first before exploring other websites.  
- When trying to solve math problems, you can try to write python code and use sympy library to solve the problem.
- Always verify the accuracy of your final answers! Try cross-checking the answers by other ways. (e.g., screenshots, webpage analysis, etc.).  
- Do not be overly confident in your own knowledge. Searching can provide a broader perspective and help validate existing knowledge.  
- After writing codes, do not forget to run the code and get the result. If it encounters an error, try to debug it. Also, bear in mind that the code execution environment does not support interactive input.
- When a tool fails to run, or the code does not run correctly, never assume that it returns the correct result and continue to reason based on the assumption, because the assumed result cannot lead you to the correct answer. The right way is to think about the reason for the error and try again.
- Search results typically do not provide precise answers. It is not likely to find the answer directly using search toolkit only, the search query should be concise and focuses on finding sources rather than direct answers, as it always need to use other tools to further process the url, e.g. interact with the webpage, extract webpage content, etc. 
- For downloading files, you can either use the web browser simulation toolkit or write codes.
</tips>

        """

        user_sys_msg = BaseMessage.make_user_message(
            role_name=self.user_role_name, content=user_system_prompt
        )

        assistant_sys_msg = BaseMessage.make_assistant_message(
            role_name=self.assistant_role_name, content=assistant_system_prompt
        )

        return user_sys_msg, assistant_sys_msg

    def step(
        self, assistant_msg: BaseMessage
    ) -> Tuple[ChatAgentResponse, ChatAgentResponse]:
        user_response = self.user_agent.step(assistant_msg)
        if user_response.terminated or user_response.msgs is None:
            return (
                ChatAgentResponse(msgs=[], terminated=False, info={}),
                ChatAgentResponse(
                    msgs=[],
                    terminated=user_response.terminated,
                    info=user_response.info,
                ),
            )
        user_msg = self._reduce_message_options(user_response.msgs)

        modified_user_msg = deepcopy(user_msg)

        if "TASK_DONE" not in user_msg.content:
            modified_user_msg.content += f"""\n
            Here are auxiliary information about the overall task, which may help you understand the intent of the current task:
            <auxiliary_information>
            {self.task_prompt}
            </auxiliary_information>
            If there are available tools and you want to call them, never say 'I will ...', but first call the tool and reply based on tool call's result, and tell me which tool you have called.
            """

        else:
            # The task is done, and the assistant agent need to give the final answer about the original task
            modified_user_msg.content += f"""\n
            Now please make a final answer of the original task based on our conversation : <task>{self.task_prompt}</task>
            """

        # process assistant's response
        assistant_response = self.assistant_agent.step(modified_user_msg)
        if assistant_response.terminated or assistant_response.msgs is None:
            return (
                ChatAgentResponse(
                    msgs=[],
                    terminated=assistant_response.terminated,
                    info=assistant_response.info,
                ),
                ChatAgentResponse(
                    msgs=[user_msg], terminated=False, info=user_response.info
                ),
            )
        assistant_msg = self._reduce_message_options(assistant_response.msgs)

        modified_assistant_msg = deepcopy(assistant_msg)
        if "TASK_DONE" not in user_msg.content:
            modified_assistant_msg.content += f"""\n
                Provide me with the next instruction and input (if needed) based on my response and our current task: <task>{self.task_prompt}</task>
                Before producing the final answer, please check whether I have rechecked the final answer using different toolkit as much as possible. If not, please remind me to do that.
                If I have written codes, remind me to run the codes.
                If you think our task is done, reply with `TASK_DONE` to end our conversation.
            """

        # return the modified messages
        return (
            ChatAgentResponse(
                msgs=[modified_assistant_msg],
                terminated=assistant_response.terminated,
                info=assistant_response.info,
            ),
            ChatAgentResponse(
                msgs=[modified_user_msg],
                terminated=user_response.terminated,
                info=user_response.info,
            ),
        )

    async def astep(
        self, assistant_msg: BaseMessage
    ) -> Tuple[ChatAgentResponse, ChatAgentResponse]:
        user_response = await self.user_agent.astep(assistant_msg)
        if user_response.terminated or user_response.msgs is None:
            return (
                ChatAgentResponse(msgs=[], terminated=False, info={}),
                ChatAgentResponse(
                    msgs=[],
                    terminated=user_response.terminated,
                    info=user_response.info,
                ),
            )
        user_msg = self._reduce_message_options(user_response.msgs)

        modified_user_msg = deepcopy(user_msg)

        if "TASK_DONE" not in user_msg.content:
            modified_user_msg.content += f"""\n
            Here are auxiliary information about the overall task, which may help you understand the intent of the current task:
            <auxiliary_information>
            {self.task_prompt}
            </auxiliary_information>
            If there are available tools and you want to call them, never say 'I will ...', but first call the tool and reply based on tool call's result, and tell me which tool you have called.
            """

        else:
            # The task is done, and the assistant agent need to give the final answer about the original task
            modified_user_msg.content += f"""\n
            Now please make a final answer of the original task based on our conversation : <task>{self.task_prompt}</task>
            """

        assistant_response = await self.assistant_agent.astep(user_msg)
        if assistant_response.terminated or assistant_response.msgs is None:
            return (
                ChatAgentResponse(
                    msgs=[],
                    terminated=assistant_response.terminated,
                    info=assistant_response.info,
                ),
                ChatAgentResponse(
                    msgs=[user_msg], terminated=False, info=user_response.info
                ),
            )
        assistant_msg = self._reduce_message_options(assistant_response.msgs)

        modified_assistant_msg = deepcopy(assistant_msg)
        if "TASK_DONE" not in user_msg.content:
            modified_assistant_msg.content += f"""\n
                Provide me with the next instruction and input (if needed) based on my response and our current task: <task>{self.task_prompt}</task>
                Before producing the final answer, please check whether I have rechecked the final answer using different toolkit as much as possible. If not, please remind me to do that.
                If I have written codes, remind me to run the codes.
                If you think our task is done, reply with `TASK_DONE` to end our conversation.
            """

        return (
            ChatAgentResponse(
                msgs=[assistant_msg],
                terminated=assistant_response.terminated,
                info=assistant_response.info,
            ),
            ChatAgentResponse(
                msgs=[user_msg],
                terminated=user_response.terminated,
                info=user_response.info,
            ),
        )


class OwlGAIARolePlaying(OwlRolePlaying):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def step(
        self, assistant_msg: BaseMessage
    ) -> Tuple[ChatAgentResponse, ChatAgentResponse]:
        user_response = self.user_agent.step(assistant_msg)
        if user_response.terminated or user_response.msgs is None:
            return (
                ChatAgentResponse(msgs=[], terminated=False, info={}),
                ChatAgentResponse(
                    msgs=[],
                    terminated=user_response.terminated,
                    info=user_response.info,
                ),
            )
        user_msg = self._reduce_message_options(user_response.msgs)

        modified_user_msg = deepcopy(user_msg)

        if "TASK_DONE" not in user_msg.content:
            modified_user_msg.content += f"""\n
            Here are auxiliary information about the overall task, which may help you understand the intent of the current task:
            <auxiliary_information>
            {self.task_prompt}
            </auxiliary_information>
            If there are available tools and you want to call them, never say 'I will ...', but first call the tool and reply based on tool call's result, and tell me which tool you have called.
            """

        else:
            # The task is done, and the assistant agent need to give the final answer about the original task
            modified_user_msg.content += f"""\n
            Now please make a final answer of the original task based on our conversation : <task>{self.task_prompt}</task>
            Please pay special attention to the format in which the answer is presented.
            You should first analyze the answer format required by the question and then output the final answer that meets the format requirements. 
            Your response should include the following content:
            - `analysis`: enclosed by <analysis> </analysis>, a detailed analysis of the reasoning result.
            - `final_answer`: enclosed by <final_answer> </final_answer>, the final answer to the question.
            Here are some hint about the final answer:
            <hint>
            Your final answer must be output exactly in the format specified by the question. It should be a number OR as few words as possible OR a comma separated list of numbers and/or strings:
            - If you are asked for a number, don't use comma to write your number neither use units such as $ or percent sign unless specified otherwise. 
            - If you are asked for a string, don't use articles, neither abbreviations (e.g. for cities), and write the digits in plain text unless specified otherwise. 
            - If you are asked for a comma separated list, apply the above rules depending of whether the element to be put in the list is a number or a string.
            </hint>
            """

        # process assistant's response
        assistant_response = self.assistant_agent.step(modified_user_msg)
        if assistant_response.terminated or assistant_response.msgs is None:
            return (
                ChatAgentResponse(
                    msgs=[],
                    terminated=assistant_response.terminated,
                    info=assistant_response.info,
                ),
                ChatAgentResponse(
                    msgs=[user_msg], terminated=False, info=user_response.info
                ),
            )
        assistant_msg = self._reduce_message_options(assistant_response.msgs)

        modified_assistant_msg = deepcopy(assistant_msg)
        if "TASK_DONE" not in user_msg.content:
            modified_assistant_msg.content += f"""\n
                Provide me with the next instruction and input (if needed) based on my response and our current task: <task>{self.task_prompt}</task>
                Before producing the final answer, please check whether I have rechecked the final answer using different toolkit as much as possible. If not, please remind me to do that.
                If I have written codes, remind me to run the codes.
                If you think our task is done, reply with `TASK_DONE` to end our conversation.
            """

        # return the modified messages
        return (
            ChatAgentResponse(
                msgs=[modified_assistant_msg],
                terminated=assistant_response.terminated,
                info=assistant_response.info,
            ),
            ChatAgentResponse(
                msgs=[modified_user_msg],
                terminated=user_response.terminated,
                info=user_response.info,
            ),
        )


def run_society(
    society: OwlRolePlaying,
    round_limit: int = 15,
) -> Tuple[str, List[dict], dict]:
    overall_completion_token_count = 0
    overall_prompt_token_count = 0

    chat_history = []
    init_prompt = """
    Now please give me instructions to solve over overall task step by step. If the task requires some specific knowledge, please instruct me to use tools to complete the task.
        """
    input_msg = society.init_chat(init_prompt)
    for _round in range(round_limit):
        assistant_response, user_response = society.step(input_msg)
        overall_completion_token_count += (
            assistant_response.info["usage"]["completion_tokens"]
            + user_response.info["usage"]["completion_tokens"]
        )
        overall_prompt_token_count += (
            assistant_response.info["usage"]["prompt_tokens"]
            + user_response.info["usage"]["prompt_tokens"]
        )

        # convert tool call to dict
        tool_call_records: List[dict] = []
        for tool_call in assistant_response.info["tool_calls"]:
            tool_call_records.append(tool_call.as_dict())

        _data = {
            "user": user_response.msg.content,
            "assistant": assistant_response.msg.content,
            "tool_calls": tool_call_records,
        }

        chat_history.append(_data)
        logger.info(f"Round #{_round} user_response:\n {user_response.msgs[0].content}")
        logger.info(
            f"Round #{_round} assistant_response:\n {assistant_response.msgs[0].content}"
        )

        if (
            assistant_response.terminated
            or user_response.terminated
            or "TASK_DONE" in user_response.msg.content
        ):
            break

        input_msg = assistant_response.msg

    answer = chat_history[-1]["assistant"]
    token_info = {
        "completion_token_count": overall_completion_token_count,
        "prompt_token_count": overall_prompt_token_count,
    }

    return answer, chat_history, token_info


async def arun_society(
    society: OwlRolePlaying,
    round_limit: int = 15,
) -> Tuple[str, List[dict], dict]:
    overall_completion_token_count = 0
    overall_prompt_token_count = 0

    chat_history = []
    init_prompt = """
    Now please give me instructions to solve over overall task step by step. If the task requires some specific knowledge, please instruct me to use tools to complete the task.
        """
    input_msg = society.init_chat(init_prompt)
    for _round in range(round_limit):
        assistant_response, user_response = await society.astep(input_msg)
        overall_prompt_token_count += assistant_response.info["usage"][
            "completion_tokens"
        ]
        overall_prompt_token_count += (
            assistant_response.info["usage"]["prompt_tokens"]
            + user_response.info["usage"]["prompt_tokens"]
        )

        # convert tool call to dict
        tool_call_records: List[dict] = []
        for tool_call in assistant_response.info["tool_calls"]:
            tool_call_records.append(tool_call.as_dict())

        _data = {
            "user": user_response.msg.content,
            "assistant": assistant_response.msg.content,
            "tool_calls": tool_call_records,
        }

        chat_history.append(_data)
        logger.info(f"Round #{_round} user_response:\n {user_response.msgs[0].content}")
        logger.info(
            f"Round #{_round} assistant_response:\n {assistant_response.msgs[0].content}"
        )

        # Check other termination conditions
        if (
            assistant_response.terminated
            or user_response.terminated
            or "TASK_DONE" in user_response.msg.content
            or "任务已完成" in user_response.msg.content
        ):
            break

        input_msg = assistant_response.msg

    answer = chat_history[-1]["assistant"]
    token_info = {
        "completion_token_count": overall_completion_token_count,
        "prompt_token_count": overall_prompt_token_count,
    }

    return answer, chat_history, token_info
