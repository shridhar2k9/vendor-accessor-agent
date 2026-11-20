# AI Vendor Risk Assessor

## Configure AI findings

The assessment service uses the Groq API through its OpenAI-compatible endpoint.
Set the API key in the process environment or in a local `.env` file:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL_ID=openai/gpt-oss-120b
GROQ_BASE_URL=https://api.groq.com/openai/v1
```

`GROQ_MODEL_ID` and `GROQ_BASE_URL` are optional; they default to
`openai/gpt-oss-120b` and `https://api.groq.com/openai/v1`. The older
`GROQ_MODEL` setting is still accepted if `GROQ_MODEL_ID` is unset. If your
`.env` contains a `replace_with_...` placeholder for either model setting,
remove it or replace it with a model supported by your Groq account. Keep
`.env` local and do not commit API keys.

Install dependencies and launch the app:

```powershell
pip install -r requirements.txt
python app.py
```

Upload company policies and vendor evidence, enter the vendor details, then run
the assessment. Findings are generated for the built-in security checklist and
are drafts for human review, not approval decisions. The app verifies that
reported citations match excerpts retrieved from the uploaded documents.
Relevant retrieved excerpts are sent to Groq for analysis; do not use this
integration with documents you are not permitted to share with that provider.