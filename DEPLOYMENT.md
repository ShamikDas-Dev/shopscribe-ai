# Deployment: Groq API + Streamlit Community Cloud

## 1. Create your Groq API key

1. Sign in to https://console.groq.com/keys
2. Create a new API key and copy it once.
3. Keep it private. Do not paste it into `app.py`, a GitHub file, an issue, or a public message.

The application can use a Groq-hosted open-weight model for cloud deployment. API usage is subject to the current model availability, free-tier limits, and Groq terms.

## 2. Push the project to GitHub

Create an empty repository on https://github.com/new named `shopscribe-ai`. Do not initialize it with a README or license if you want to push this folder directly.

In PowerShell, open the extracted `shopscribe-ai` folder and run:

```powershell
git init
git add .
git status
```

Before committing, confirm that `.streamlit/secrets.toml`, `.env`, databases, `.venv`, and API keys are not staged. The project's `.gitignore` is configured to exclude local secrets and common generated files.

Then run:

```powershell
git commit -m "Add ShopScribe AI with Groq deployment support"
git branch -M main
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/shopscribe-ai.git
git push -u origin main
```

Replace `YOUR_GITHUB_USERNAME` with your GitHub username. If this folder is already a Git repository, do not repeat `git init` or `git remote add`; use the existing remote and commit/push the changed files.

## 3. Deploy on Streamlit Community Cloud

1. Visit https://share.streamlit.io/ and sign in with GitHub.
2. Choose **Create app**.
3. Select your `shopscribe-ai` repository, branch `main`, and main file path `app.py`.
4. In **Advanced settings → Secrets**, add:

   ```toml
   GROQ_API_KEY = "PASTE_YOUR_OWN_GROQ_KEY_HERE"
   SHOPSCRIBE_DISABLE_SERVER_HISTORY = true
   ```

5. Deploy the app. The app will select Groq cloud mode by default when this secret is available.
6. Test an English content pack with a non-sensitive product example. History is disabled in the hosted app so visitors cannot view a shared history list.

Never commit the actual key. If a key is accidentally pushed, revoke it in Groq Console and create another key immediately.

## 4. If deployment fails

- Open the app's **Manage app** or logs view in Streamlit Community Cloud.
- Check that `GROQ_API_KEY` is configured under app Secrets.
- Confirm that the selected model is available to your Groq account and has not been deprecated.
- Verify that `requirements.txt` installed successfully.
- Test with a short product description first. Review API rate limits if requests return a 429 error.

## 5. Understand the two modes

- **Ollama (local):** generation happens through your local Ollama server; this is appropriate for the offline/local demo.
- **Groq API (cloud):** product facts are sent to Groq for model inference. Set `SHOPSCRIBE_DISABLE_SERVER_HISTORY = true` in Streamlit secrets to disable and clear shared server-side history. History remains available only when running the app locally without that setting.

The source code can be open-source, but that does not make a hosted inference API unlimited or guarantee zero cost forever.
