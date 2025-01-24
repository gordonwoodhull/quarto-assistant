## Quarto Assistant

This chatbot outputs all its responses in the form of Quarto documents.

Using Quarto as the output format allows you to verify the results produced by an LLM in a reproducible way.

### Implementation

Quarto Assistant is implemented in [Shiny for Python](https://shiny.posit.co/py/), using [chatlas](https://github.com/posit-dev/chatlas).

Since Quarto documents can have arbitrary code in them, the chatbot spawns Quarto in a Docker container. Watch this space for published Quarto images.

> :warning: Warning
>
> This is a single-user chatbot which serves its entire output directory at `output/`
>
> For this reason, and also because it is using your API key, you should only run this locally or on secure networks.

### Environment variables

*  `QUARTO_ASSISTANT_OUTPUT_DIR` - output directory. Default: `.`

* `QUARTO_ASSISTANT_GENAI_PROVIDER` - generative AI provider currently `anthropic` and `openai` are supported. Default: `anthropic`
  (`google` and `ollama` are implemented but don't work yet.) 

* `QUARTO_ASSISTANT_GENAI_MODEL` - generative AI model. Defaults to best known model that works.
* `QUARTO_ASSISTANT_DOCKER_IMAGE` - Quarto docker image to use for rendering. If not set, documents will not be rendered automatically and a warning will be printed.

Provide your API keys through e.g. `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`.


### Running manually

This project uses [pipenv](https://pipenv.pypa.io/en/latest/)

Install pipenv, then run

```
pipenv install
pipenv run shiny run quarto-assistant.py
```

The app will pick up `.env` if it exists; otherwise make sure you have set the necessary environment variables.
