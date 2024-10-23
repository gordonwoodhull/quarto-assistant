# ------------------------------------------------------------------------------------
# A basic Shiny Chat example powered by Anthropic's Claude model.
# To run it, you'll need an Anthropic API key.
# To get one, follow the instructions at https://docs.anthropic.com/en/api/getting-started
# ------------------------------------------------------------------------------------
import os
import sys
import json
import re
from datetime import datetime
from app_utils import load_dotenv
from anthropic import AsyncAnthropic

from shiny.express import ui
from openai import AsyncOpenAI

provider = os.environ.get('QUARTO_DS_CHATBOT_MODEL') or 'openai' # anthropic broke with tools
outdir = os.environ.get('QUARTO_DS_CHATBOT_OUTPUT_DIR') or '.'
# Either explicitly set the ANTHROPIC_API_KEY environment variable before launching the
# app, or set them in a file named `.env`. The `python-dotenv` package will load `.env`
# as environment variables which can later be read by `os.getenv()`.
load_dotenv()
match provider:
    case 'anthropic':
        llm = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        model = "claude-3-opus-20240229"
    case 'openai':
        llm = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        model = "gpt-4o" # Make sure to use a model that supports function calling
    case _:
        print('unsupported provider', provider)
        sys.exit(2)

# Set some Shiny page options
ui.page_opts(
    title="Quarto Data Science Chat (" + provider + ")",
    fillable=True,
    fillable_mobile=True,
)

system_prompt = f"""
You are a terse data science chatbot. When you are asked a question,
you will submit your answer in the form of a Quarto markdown document
including the original question, your explanation, and any requested code.
For the filename, use a five-word summary of the question, separated by
dashes and the extension .qmd
Make sure to include the Quarto metadata block at the top of the document,
including the key description and value "{provider} {model}"
The date is {str(datetime.now())}
You don't need to add quadruple backticks around the document.
Please use curly braces around the language in any executable code blocks.
And thank you!
"""


match provider:
    case 'anthropic':
        chat = ui.Chat(id="chat")
    case 'openai':
        chat = ui.Chat(id="chat", messages=[
            {"role": "system", "content": system_prompt},
            {"content": "Hello! How can I help you today?", "role": "assistant"},
        ])
# Create and display empty chat
chat.ui()

def show_answer(filename, answer):
    print('\nreceived quarto markdown result\n')
    print(answer)
    if filename:
        if not re.search(r'\.qmd$', filename):
            filename = filename + '.qmd' # choose your battles
        count = None
        while True:
            if count:
                filename2 = re.sub(r'\.qmd$', '-' + str(count) + '.qmd', filename)
            else:
                filename2 = filename
            filename2 = os.path.join(outdir, filename2)
            try:
                with open(filename2, "x") as qmd_file:
                    print('\nwrote answer to', filename2)
                    qmd_file.write(answer)
                    break
            except:
                count = (count or 1) + 1

tools = [
    {
        "type": "function",
        "function": {
            "name": "show_answer",
            "description": "Show an answer including explanation in Quarto markdown format",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The name of the Quarto markdown file to output, with base derived from the question and extension .qmd"
                    },
                    "answer": {
                        "type": "string",
                        "description": "The answer and explanation as a Quarto markdown document",
                    },
                },
                "required": ["filename", "answer"],
            },
        },
    }
]


async def process_conversation(messages):
    match provider:
        case 'anthropic':
            response = await llm.messages.create(
                model=model,
                messages=messages,
                max_tokens=1000,
            )
        case 'openai':
            response = await llm.chat.completions.create(
                model=model,
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
            filename = function_args.get("filename")
            show_answer(filename, answer)
            content = '````\n' + answer + '````\n'
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
    messages = chat.messages(format=provider)

    await process_conversation(messages)
