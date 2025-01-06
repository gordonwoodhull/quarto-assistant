import os
import sys
import json
import re
import pathlib
from datetime import datetime
from app_utils import load_dotenv

from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles

import docker

from chatlas import ChatAnthropic, ChatOpenAI, ChatGoogle, ChatOllama

from shiny import App, ui, render, reactive

# Either explicitly set the OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable before launching the
# app, or set them in a file named `.env`. The `python-dotenv` package will load `.env`
# as environment variables which can later be read by `os.getenv()`.
load_dotenv()

provider = os.environ.get('QUARTO_DS_CHATBOT_PROVIDER') or 'anthropic'
model = os.environ.get('QUARTO_DS_CHATBOT_MODEL')
debug = os.environ.get('QUARTO_DS_CHATBOT_DEBUG') or False
outdir = os.environ.get('QUARTO_DS_CHATBOT_OUTPUT_DIR') or '.'
docker_image = os.environ.get('QUARTO_DS_CHATBOT_DOCKER_IMAGE') or None
extra_python_packages = []
epp = os.environ.get('QUARTO_DS_CHATBOT_EXTRA_PYTHON_PACKAGES')
if epp:
    extra_python_packages = re.split(r',\s*', epp)
extra_r_packages = []
erp = os.environ.get('QUARTO_DS_CHATBOT_EXTRA_R_PACKAGES')
if erp:
    extra_r_packages = re.split(r',\s*', erp)

if debug:
    os.environ['CHATLAS_LOG'] = 'info'
    os.environ['ANTHROPIC_LOG'] = 'info'
    os.environ['OPENAI_LOG'] = 'info'

static_output = StaticFiles(directory=outdir)

provider_greeting = ""
match provider:
    case 'anthropic':
        # requires patch to chatlas, see
        # https://github.com/posit-dev/chatlas/issues/10#issuecomment-2566552159
        model = model or "claude-3-5-sonnet-latest"
        # works with stock chatlas
        # model = model or "claude-3-5-sonnet-20240620"
    case 'openai':
        model = model or "gpt-4o"
    case 'google':
        model = model or 'gemini-1.5-flash'
        provider_greeting = "> 🚧 Warning\\\n> `google gemini` tool calling is not quite working, but it looks like it could work. If you know how to fix this, please submit a PR.\n\n"
    case 'ollama':
        model = model or "llama3.2"
        provider_greeting = "> 🚧 Warning\\\n> `ollama` tool calling does not seem to be working, so you probably won't get Quarto document outputs yet. If you know how to fix this, please submit a PR.\n\n"
    case _:
        print('unsupported provider', provider)
        sys.exit(2)

print(f'Using provider {provider}, model {model}')
print('Output directory:', outdir)

author_name = f"{provider} {model}"

app_ui = ui.page_sidebar(
    ui.sidebar(ui.chat_ui("chat"), width='40%'),
    ui.output_ui('rendered'),
    title = ui.div(
        ui.h2("Quarto Assistant"),
        ui.h6(ui.code(author_name))
    ),
    fillable=True,
    fillable_mobile=True,
)

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

docker_client = docker.from_env()
output_url = reactive.value('output/none.html')

def render_quarto(qmdfilename: str):
    qmddir = os.path.dirname(qmdfilename)
    qmdfile = os.path.basename(qmdfilename)
    cmds = []
    if extra_python_packages:
        extra_python_packages_fmt = ' '.join(extra_python_packages)
        cmds.append(f"pip install {extra_python_packages_fmt}")
    if extra_r_packages:
        extra_r_packages_fmt = ', '.join([f'\\"{p}\\"' for p in extra_r_packages])
        cmds.append(f"sudo R --vanilla -e \"install.packages(c({extra_r_packages_fmt}), repos=\\\"http://cran.us.r-project.org\\\")\"")
    cmds += [
        'cd /home/quarto',
        f'quarto render {qmdfile}',
    ]
    command = f"bash -c '{"; ".join(cmds)}'"
    print('quarto command', command)
    if not docker_image:
        print('QUARTO_DS_CHATBOT_DOCKER_IMAGE not set, not running Quarto')
        return
    logs = docker_client.containers.run(
        docker_image,
        command,
        volumes = {
            qmddir: {
                'bind': '/home/quarto',
                'mode': 'rw'
            }
        })
    output_url.set(re.sub('^' + outdir, 'output',
                          re.sub(r'\.qmd$', '.html', qmdfilename)))

def show_answer(filename: str, answer: str) -> bool:
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
    True for success, False for failure
    """
    print('\nreceived quarto markdown result\n')
    print(answer)
    if filename:
        if not re.search(r'\.qmd$', filename):
            filename = filename + '.qmd' # choose your battles
        count = 0
        stem = pathlib.Path(filename).stem
        while True:
            if count:
                if count > 100:
                    print('\ntoo many collisions, giving up')
                    return False
                stem2 = stem + '-' + str(count)
            else:
                stem2 = stem
            iodir = os.path.join(outdir, stem2)
            try:
                os.mkdir(iodir)
                qmdfilename = os.path.join(iodir, filename)
                with open(qmdfilename, "x") as qmd_file:
                    qmd_file.write(answer)
                    print('\nwrote answer to', qmdfilename)
                render_quarto(qmdfilename)
                break
            except FileExistsError:
                count = count + 1
    else:
        return False
    return True

messages = [
    {"role": "system", "content": system_prompt},
    {"content": f"Hello! I am a chatbot which responds to questions with Quarto documents.\n\n"
        + provider_greeting
        + "How can I help you today?", "role": "assistant"},
]
streaming = True
match provider:
    case 'anthropic':
        chat_model_constructor = ChatAnthropic
    case 'openai':
        chat_model_constructor = ChatOpenAI
    case 'google':
        chat_model_constructor = ChatGoogle
    case 'ollama':
        chat_model_constructor = ChatOllama
        streaming = False
chat_model = chat_model_constructor(system_prompt=system_prompt, model=model)
chat_model.register_tool(show_answer)

def server(input):
    # Create a chat instance and display it
    chat = ui.Chat(id="chat", messages = messages)

    # Define a callback to run when the user submits a message
    @chat.on_user_submit
    async def _():
        if streaming:
            response = chat_model.stream(chat.user_input(), echo = debug and "all")
            # object bool can't be used in 'await' expression'"
            # response = await chat_model.stream_async(chat.user_input(), echo = debug and "all")
            await chat.append_message_stream(response)
        else:
            response = chat_model.chat(chat.user_input(), echo = debug and "all")
            await chat.append_message(response.content)

    @render.ui
    def rendered():
        return ui.tags.iframe(src=output_url(), style='height: 100%'),


app_shiny = App(app_ui, server)


# combine apps ----
routes = [
    Mount('/output', app=static_output),
    Mount('/', app=app_shiny)
]

app = Starlette(routes=routes)

# Define a callback to run when the user submits a message


