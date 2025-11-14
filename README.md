# AI Video Shorts Generator

This project provides a Flask-based web application that mirrors the autonomous short-form video workflow originally requested for n8n. Supply a 1–3 sentence idea and the app delivers a finished 9:16 `.mp4` with script, captions, and metadata.

## Features

- **Idea analysis** – Evaluates multiple AI-generated video angles and picks the most viral-friendly option.
- **Script & shot planning** – Produces a 15–30 second script, shot list, and on-screen captions.
- **Video creation** – Integrates with a generative video API (Pika Labs by default) or uses the built-in demo renderer.
- **Voiceover** – Connects to ElevenLabs (or any compatible TTS) with a fully offline pyttsx3 fallback.
- **Subtitle burn-in** – Auto generates SRT timings and overlays bold white captions near the bottom of the frame.
- **Final delivery** – Combines everything into a single `.mp4`, exposes a download link, and surfaces raw metadata.

## Getting Started

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment** (optional, demo mode is on by default)

   ```bash
   export AIVID_DEMO_MODE=false
   export OLLAMA_BASE_URL=http://127.0.0.1:11434
   export OLLAMA_MODEL=llama3.1
   export VIDEO_API_KEY=your-pika-api-key
   export VIDEO_API_URL=https://api.pikalabs.com/v1/videos
   export TTS_API_KEY=your-elevenlabs-key
   export TTS_API_URL=https://api.elevenlabs.io/v1/text-to-speech
   export TTS_VOICE_ID=EXAVITQu4vr4xnSDxMaL
   ```

   Leave `AIVID_DEMO_MODE=true` to generate placeholder clips and voiceovers locally without any external APIs. Make sure your Ollama server is running (`ollama serve`) and that the specified model is pulled (`ollama pull llama3.1` or any model you prefer).

3. **Run the web application**

   ```bash
   python -m app.main
   ```

   Visit `http://localhost:8000` and submit a short prompt. The workflow will run end-to-end and return the final video and metadata.

## Output Artifacts

Each generation stores results under `app/static/outputs/` so the front-end can serve download links. Metadata includes:

- Selected concept and scoring leaderboard
- Full script text and captions
- Serialized shot list (JSON)
- Prompt and run identifier

Set `AIVID_KEEP_INTERMEDIATES=true` to preserve per-shot clips, SRT files, and voiceover assets for inspection.

## Notes on External APIs

- **Ollama** powers ideation, scripting, and caption planning. Set `OLLAMA_MODEL` to whichever local model you want to run (for example `llama3.1` or `qwen2.5`).
- **Video generation** defaults to Pika Labs, but any service with a JSON HTTP API returning a downloadable URL will work.
- **Text-to-speech** assumes ElevenLabs compatibility; adjust URLs and headers to connect a different provider if desired.

Example payloads with placeholder keys are already implemented in the pipeline modules, so plugging in credentials is enough to go live.
