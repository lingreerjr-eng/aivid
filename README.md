# AI Video Shorts Generator

This repository packages the autonomous short-form video workflow into a Netlify-friendly project. The front-end is a static site (`web/`) and the heavy lifting runs inside a Python Netlify Function (`/.netlify/functions/run_workflow`). Provide a 1–3 sentence idea and the pipeline returns a fully assembled 9:16 `.mp4` with script, captions, and metadata.

## Features

- **Idea analysis** – Generates multiple angles with Ollama and selects the highest scoring concept.
- **Script & shot planning** – Produces a 15–30 second script, shot list, and on-screen captions in structured JSON.
- **Video creation** – Calls an external video API (Pika Labs by default) or uses the built-in demo renderer when no key is supplied.
- **Voiceover** – Connects to ElevenLabs-compatible TTS or falls back to an offline pyttsx3 synthesiser.
- **Subtitle burn-in** – Builds SRT timings and burns bold white captions near the bottom of the frame.
- **Serverless delivery** – Returns the final `.mp4` as a base64 payload so the Netlify front-end can stream and download the result.

## Project Layout

```
web/                     # Static assets deployed as-is to Netlify
  index.html             # Single-page interface that calls the serverless function
  styles.css             # Dark UI styling
  app.js                 # Fetch logic and client-side rendering
netlify/functions/
  run_workflow.py        # Python handler that orchestrates the full workflow
  requirements.txt       # Delegates to the root dependency list
app/pipeline/            # Core workflow logic (ideation, scripting, media, assembly)
app/config.py            # Environment + runtime configuration
netlify.toml             # Netlify configuration (publish dir + included files)
```

## Running Locally

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables** (optional – demo mode is enabled by default)

   ```bash
   export AIVID_DEMO_MODE=true        # Leave true to use built-in demo clips/audio
   export OLLAMA_BASE_URL=http://127.0.0.1:11434
   export OLLAMA_MODEL=llama3.1
   export VIDEO_API_KEY=your-pika-api-key
   export VIDEO_API_URL=https://api.pikalabs.com/v1/videos
   export TTS_API_KEY=your-elevenlabs-key
   export TTS_API_URL=https://api.elevenlabs.io/v1/text-to-speech
   export TTS_VOICE_ID=EXAVITQu4vr4xnSDxMaL
   export AIVID_OUTPUT_DIR=./outputs   # Optional override for local artifacts
   ```

   Make sure your Ollama daemon is running (`ollama serve`) and the chosen model is pulled (`ollama pull llama3.1` or whichever model you prefer).

3. **Serve the site and function**

   - With the Netlify CLI:

     ```bash
     netlify dev
     ```

     The CLI will host the static site from `web/` and proxy function calls to `run_workflow.py` so you can exercise the entire flow locally at `http://localhost:8888`.

   - Without the CLI you can still invoke the function directly:

     ```bash
     python netlify/functions/run_workflow.py
     ```

     (Provide a JSON body to `handler` in a REPL or add your own thin wrapper. The Netlify CLI path above is the recommended approach for end-to-end testing.)

## Deploying to Netlify

1. Commit this repository and push it to your own Git provider.
2. In Netlify, create a new site from your repository.
3. Use the following settings when prompted:
   - **Build command:** leave blank (static publish)
   - **Publish directory:** `web`
   - **Functions directory:** detected automatically from `netlify.toml`
4. Add the required environment variables (`AIVID_DEMO_MODE`, `OLLAMA_BASE_URL`, `VIDEO_API_URL`, etc.) in the Netlify dashboard under *Site configuration → Environment variables*.
5. Deploy. The generated site will present the prompt form and invoke the `run_workflow` function autonomously.

The function stores intermediate assets inside `/tmp/aivid_outputs` (or `AIVID_OUTPUT_DIR` if specified) which is compatible with Netlify’s serverless runtime. Set `AIVID_KEEP_INTERMEDIATES=true` to retain temporary clips, SRT files, and audio for debugging.

## External Service Notes

- **Ollama** powers ideation, scripting, and captions. Specify the model with `OLLAMA_MODEL` (e.g. `llama3.1`, `qwen2.5`).
- **Video generation** defaults to Pika Labs, but any provider that returns a downloadable URL will work once you update `VIDEO_API_URL` and headers.
- **Text-to-speech** expects an ElevenLabs-style endpoint; adjust URLs and API keys to swap providers.

All API requests are performed through the Netlify Function using simple HTTP calls, so replacing services only requires tweaking environment variables or the corresponding modules in `app/pipeline/`.
