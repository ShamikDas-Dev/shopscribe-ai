# ShopScribe AI

ShopScribe AI creates editable Instagram captions, WhatsApp promotions, and product listings in English from facts supplied by a small retailer.

## AI providers

ShopScribe supports two inference options:

- **Ollama (local):** Runs an open-weight model on your own computer. Once the model has been downloaded, generation can work offline.
- **Groq API (cloud):** Calls an open-weight model served by Groq. This mode is suitable for a public Streamlit demo, but product facts are transmitted to Groq for inference and requests are subject to the provider's current rate limits and pricing.

The code defaults to `qwen3:4b` for local Ollama and `openai/gpt-oss-20b` for Groq. Available API models can change; select a model that is enabled in your Groq account. The Groq model identifier is not the same thing as downloading that model to your laptop.

## Features

- Product listing, Instagram caption, and WhatsApp message generation.
- English output with editable copy and export options.
- Pydantic validation for structured output.
- Warnings for some unsupported medical, clinical, absolute, and price claims.
- Deterministic discount calculation in Python when MRP and selling price are supplied.
- Editable results and Markdown export.
- Local SQLite history for recent generations.

## Run locally with Ollama

1. Install Python 3.12 and [Ollama](https://ollama.com/).
2. Pull the model:

   ```powershell
   ollama pull qwen3:4b
   ```

3. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

4. Install dependencies and run tests:

   ```powershell
   python -m pip install -r requirements.txt
   python -m pytest -q
   ```

5. Run the application:

   ```powershell
   streamlit run app.py
   ```

Choose **Ollama (local)** in the app's sidebar.

## Run with Groq

1. Create an API key in [Groq Console](https://console.groq.com/keys).
2. Do not commit your API key to GitHub. Locally, put it in `.streamlit/secrets.toml`:

   ```toml
   GROQ_API_KEY = "paste-your-own-key-here"
   ```

3. Ensure `.streamlit/secrets.toml` remains ignored by Git. Alternatively, set the `GROQ_API_KEY` environment variable.
4. Run `streamlit run app.py`, select **Groq API (cloud)**, and generate a test content pack.

This project deliberately does not contain a real API key.

## Deploy to Streamlit Community Cloud

1. Push this repository to GitHub with `app.py` at the repository root.
2. Open [Streamlit Community Cloud](https://share.streamlit.io/) and create an app using your GitHub repository, branch, and `app.py` entry point.
3. In the deploy dialog's **Advanced settings → Secrets**, add:

   ```toml
   GROQ_API_KEY = "paste-your-own-key-here"
   SHOPSCRIBE_DISABLE_SERVER_HISTORY = true
   ```

4. Deploy, open the public app URL, choose **Groq API (cloud)**, and test English output. The history panel is disabled in the hosted app to prevent visitors from seeing shared server-side records.

Do not add `.streamlit/secrets.toml`, `.env` files, keys, or local databases with private data to the repository. If a key is ever committed, revoke it in Groq Console and create a replacement immediately.

## How generation works

1. The retailer enters verified product facts.
2. The app builds a prompt with strict language and factuality requirements.
3. The selected provider generates a JSON response.
4. Pydantic validates the returned fields.
5. The application validates the structured output and flags suspicious claims or price mismatches for review.
6. Basic deterministic checks flag some suspicious claims and prices for human review.
7. The retailer edits, copies, or exports the result.

These checks do not prove that every generated claim is true. Review all output against the actual product packaging before publication.

## Data and privacy

- In Ollama mode, inference is processed by the configured Ollama service.
- In Groq mode, product facts and prompt text are sent to Groq's hosted API.
- When running on your own computer without `SHOPSCRIBE_DISABLE_SERVER_HISTORY`, history is stored in a local SQLite database on that computer.
- On Streamlit Community Cloud, set `SHOPSCRIBE_DISABLE_SERVER_HISTORY = true`. The app then stops saving and displaying history and removes the previous server-side SQLite history files, so visitors do not share a history panel. Hosted visitors do not get a persistent per-browser history feature.
- In Groq mode, product facts are sent to Groq for inference. Do not enter customer personal information or confidential business data into the prototype.

## Project structure

```text
shopscribe-ai/
├── app.py
├── core/
│   ├── __init__.py
│   ├── schemas.py
│   ├── prompts.py
│   ├── generator.py
│   ├── language_checks.py
│   ├── validators.py
│   └── pricing.py
├── storage/
│   ├── __init__.py
│   └── history.py
├── tests/
├── sample_data/cosmetics_demo.json
├── .streamlit/config.toml
├── requirements.txt
├── .gitignore
└── LICENSE
```

## Model notes

The application's own source is licensed under MIT. The selected open-weight models are separate assets subject to their respective model licenses and provider terms. Check the exact model and license before commercialization. Free hosted API availability, usage limits, model identifiers, and pricing can change.

## Challenge demo checklist

- Show an actual model request and generated output.
- Demonstrate an actual generated content pack and have a retailer review the content.
- Keep the local inference option to demonstrate the open-weight model.
- Test with a real retailer and record actual feedback; do not claim payment or user results unless they occurred.
