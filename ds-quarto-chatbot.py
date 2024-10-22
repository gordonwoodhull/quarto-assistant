# ------------------------------------------------------------------------------------
# A basic Shiny Chat example powered by Anthropic's Claude model.
# To run it, you'll need an Anthropic API key.
# To get one, follow the instructions at https://docs.anthropic.com/en/api/getting-started
# ------------------------------------------------------------------------------------
import os
import sys
import json

from app_utils import load_dotenv
from anthropic import AsyncAnthropic

from shiny.express import ui
from openai import AsyncOpenAI

model = os.environ.get('DS_QUARTO_MODEL') or 'openai' # anthropic broke with tools

# Either explicitly set the ANTHROPIC_API_KEY environment variable before launching the
# app, or set them in a file named `.env`. The `python-dotenv` package will load `.env`
# as environment variables which can later be read by `os.getenv()`.
load_dotenv()
match model:
    case 'anthropic':
        llm = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    case 'openai':
        llm = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    case _:
        print('unsupported model', model)
        sys.exit(2)

# Set some Shiny page options
ui.page_opts(
    title="Quarto Data Science Chat (" + model + ")",
    fillable=True,
    fillable_mobile=True,
)

system_prompt = """
You are a data science chatbot. When you are asked a question,
you will submit your answer in the form of a Quarto markdown document
including your explanation and any requested code.
"""


match model:
    case 'anthropic':
        chat = ui.Chat(id="chat")
    case 'openai':
        chat = ui.Chat(id="chat", messages=[
            {"role": "system", "content": system_prompt},
            {"content": "Hello! How can I help you today?", "role": "assistant"},
        ])
# Create and display empty chat
chat.ui()

def show_answer(answer):
    print('received markdown?')
    print(answer)

tools = [
    {
        "type": "function",
        "function": {
            "name": "show_answer",
            "description": "Show an answer including explanation in Quarto markdown format",
            "parameters": {
                "type": "object",
                "properties": {
                    "answer": {
                        "type": "string",
                        "description": "The answer and explanation as a Quarto markdown document",
                    },
                },
                "required": ["answer"],
            },
        },
    }
]


async def process_conversation(messages):
    response = await llm.chat.completions.create(
        model="gpt-4o",  # Make sure to use a model that supports function calling
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )

    message = response.choices[0].message

    if not message.tool_calls:
        await chat.append_message(response)
        return

    # Process all tool calls
    for tool_call in message.tool_calls:
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)

        if function_name == "show_answer":
            answer = function_args.get("answer")
            show_answer(answer)
            content = answer
        else:
            # If the function is unknown, return an error message
            # and also log to stderr
            content = f"Unknown function: {function_name}"
            print(f"Unknown function: {function_name}", file=sys.stderr)

        await chat.append_message(
            {
                "role": "assistant",
                # "tool_call_id": tool_call.id,
                # "name": function_name,
                "content": content,
            }
        )


# Define a callback to run when the user submits a message
@chat.on_user_submit
async def _():
    # Get messages currently in the chat
    messages = chat.messages(format=model)

    await process_conversation(messages)
