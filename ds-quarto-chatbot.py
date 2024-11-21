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

from shiny.express import ui
from chatlas import ChatAnthropic, ChatOpenAI

# Either explicitly set the OPENAI_API_KEY (or soon, ANTHROPIC_API_KEY) environment variable before launching the
# app, or set them in a file named `.env`. The `python-dotenv` package will load `.env`
# as environment variables which can later be read by `os.getenv()`.

provider = os.environ.get('QUARTO_DS_CHATBOT_PROVIDER') or 'anthropic'
model = os.environ.get('QUARTO_DS_CHATBOT_MODEL')
outdir = os.environ.get('QUARTO_DS_CHATBOT_OUTPUT_DIR') or '.'


load_dotenv()
match provider:
    case 'anthropic':
        model = model or "claude-3-5-sonnet-20240620" # claude-3-5-sonnet-latest currently crashes
    case 'openai':
        model = model or "gpt-4o"
    case _:
        print('unsupported provider', provider)
        sys.exit(2)

print(f'Using provider {provider}, model {model}')
print('Output directory:', outdir)

# Set some Shiny page options
ui.page_opts(
    title="Quarto Data Science Chat (" + provider + ")",
    fillable=True,
    fillable_mobile=True,
)

author_name = f"{provider} {model}"

system_prompt = f"""
You are a terse data science chatbot. When you are asked a question,
you will submit your answer in the form of a Quarto markdown document
including the original question, an overview, any requested code, and an explanation.
Please use the `show_answer` tool for all of your responses.
For the filename, use a five-word summary of the question, separated by
dashes and the extension .qmd
Make sure to include the Quarto metadata block at the top of the document:
* the author is "{author_name}"
* the date is {str(datetime.now())}
You don't need to add quadruple backticks around the document.
Please remember to surround the language with curly braces when outputting a code block, e.g.
```{{python}}
```{{r}}
Thank you!
"""

def show_answer(filename: str, answer: str) -> str:
    """
    Reports an answer in Quarto markdown format.

    Parameters
    ----------
    filename
        The output filename for the Quarto document, with extension "qmd".
    answer
        The answer and explanation in Quarto markdown format.
    
    Returns
    -------
    The same answer, wrapped in quadruple backticks.
    """
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
    return '````\n' + answer + '````\n'

messages = [
    {"role": "system", "content": system_prompt},
    {"content": f"Hello! I am an instance of `{author_name}`.\n\n"
        + "I respond to all questions with Quarto documents, written to \\\n`"
        + outdir + "` \n\n"
        + "How can I help you today?", "role": "assistant"},
]
match provider:
    case 'anthropic':
        chat_model = ChatAnthropic(system_prompt=system_prompt, model=model)
    case 'openai':
        chat_model = ChatOpenAI(system_prompt=system_prompt, model=model)
chat_model.register_tool(show_answer)
chat = ui.Chat(id="chat", messages=messages)
# Create and display empty chat
chat.ui()


# Define a callback to run when the user submits a message
@chat.on_user_submit
async def _():
    response = chat_model.stream(chat.user_input())
    await chat.append_message_stream(response)
