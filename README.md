## Quarto Assistant

This chatbot outputs all its responses in the form of Quarto documents.

It is implemented in Shiny for Python, using 

### Configuration

Change the output directory with `QUARTO_ASSISTANT_OUTPUT_DIR`, otherwise the current directory will be used.

You can specify the provider using `QUARTO_ASSISTANT_GENAI_PROVIDER`; currently `anthropic` and `openai` are supported. (`google` and `ollama` are implemented but don't work yet.)

Specify the model with `QUARTO_ASSISTANT_GENAI_MODEL` or an appropriate one will be chosen.

Provide your API keys through e.g. `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`

### Installing and running

This uses [chatlas](https://github.com/posit-dev/chatlas) to interface with the LLM; please install that first.

You can install Shiny for Python with `pip install shiny`

Then run the app with

```sh
shiny run ds-quarto-chatbot.py
```

The app will pick up `.env` if it exists; otherwise use the environment.


