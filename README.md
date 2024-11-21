## Quarto Data Science Chatbot

This Shiny for Python chatbot outputs all its responses in the form of Quarto documents.

### Configuration

Change the output directory with `QUARTO_DS_CHATBOT_OUTPUT_DIR`, otherwise the current directory will be used.

You can specify the provider using `QUARTO_DS_CHATBOT_PROVIDER`; currently `anthropic` and `openai` are supported.

Specify the model with `QUARTO_DS_CHATBOT_MODEL` or an appropriate one will be chosen.

### Installing and running

This uses [chatlas](https://github.com/posit-dev/chatlas) to interface with the LLM; please install that first.

You can install Shiny for Python with `pip install shiny`

Specify your configuration through environment variables, and set up keys `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in `./.env`

Then run the app with

```sh
shiny run ds-quarto-chatbot.py
```

