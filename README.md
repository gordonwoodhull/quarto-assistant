## Quarto Data Science Chatbot

This chatbot outputs all its responses in the form of Quarto documents.

It saves all responses to an output directory, which you can configure with `QUARTO_DS_CHATBOT_OUTPUT_DIR`.

You can specify the provider using `QUARTO_DS_CHATBOT_PROVIDER`, but only `openai` is supported for now.

Run the app with

```sh
shiny run ds-quarto-chatbot.py
```

## To do

* Anthropic support coming soon-ish!
* Should be possible to specify other models, as long as they support tools / function calls.
* Would be nice to make a full assistant app out of this, with edit and Quarto preview panes.
