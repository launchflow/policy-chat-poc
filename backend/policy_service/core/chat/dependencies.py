from datetime import datetime
from pathlib import Path
from typing import List

import requests
from buildflow.dependencies import Scope, dependency
from jinja2 import Environment, FileSystemLoader

from policy_service.core.storage.api import Policy
from policy_service.settings import env


def render_policy_instructions(
    policies: List[Policy], template_file: str = "instructions.jinja"
) -> str:
    if len(policies) == 0:
        raise Exception("No policies found")

    # Setting up the environment to load templates from the file system
    templates_path = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(str(templates_path)))

    # Loading the template from a .jinja file
    template = env.get_template(template_file)

    user_name = policies[0].policy_holder
    policy_summary = [policy.json() for policy in policies]

    # Rendering the template with the policy information
    return template.render(
        date_today=datetime.now().strftime("%d/%m/%Y"),
        user_name=user_name,
        policy_summary=policy_summary,
    )


def PolicyChatModelBuilder(anyscale_base_url: str, anyscale_api_key: str):
    @dependency(scope=Scope.NO_SCOPE)
    class AnyscaleChatModel:
        def __init__(self):
            self._anyscale_url = f"{anyscale_base_url}/chat/completions"
            self._anyscale_api_key = anyscale_api_key

        def query(self, system_content: str, user_content: str) -> str:
            body = {
                "model": "meta-llama/Llama-2-70b-chat-hf",
                "messages": [
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_content},
                ],
                "temperature": 0.7,
            }
            with requests.post(
                self._anyscale_url,
                headers={"Authorization": f"Bearer {self._anyscale_api_key}"},
                json=body,
            ) as resp:
                return resp.json()["choices"][0]["message"]["content"]

    @dependency(scope=Scope.PROCESS)
    class PolicyChatModel:
        def __init__(self, chat_model: AnyscaleChatModel):
            self.chat_model = chat_model

        def handle_user_inquiry(self, inquiry: str, policies: List[Policy]):
            instructions = render_policy_instructions(policies)
            response = self.chat_model.query(
                system_content=instructions, user_content=inquiry
            )
            return response

    return PolicyChatModel


PolicyChatModel = PolicyChatModelBuilder(
    anyscale_base_url=env.anyscale_base_url,
    anyscale_api_key=env.anyscale_api_key,
)
