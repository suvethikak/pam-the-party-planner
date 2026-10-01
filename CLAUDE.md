# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- Run: `uv run app.py` (serves http://localhost:8000 via uvicorn on 127.0.0.1:8000)
- Auth prerequisite: `gcloud auth application-default login`; the app uses the gcloud default project (Vertex AI / Agent Platform API must be enabled with billing).
- No tests, linter, or build step are configured.

## Architecture

A small FastAPI app that wraps a hand-written agent loop around Gemini (`vertex_ai/gemini-3.5-flash-lite`, location `global`) via LiteLLM, using OpenAI-style tool calling.

- [app.py](app.py): `run_agent(messages)` is the harness loop. It calls `litellm.completion`, appends the reply to `messages` (mutating the session's list in place), and, if the model requested tools, runs each one itself and appends `role: "tool"` messages, repeating up to `MAX_TOOL_ROUNDS` (5). It returns the final text plus a record of every tool call. The `/chat` endpoint, `/clear`, and the in-memory `sessions` dict (session_id -> message list, single process, lost on restart) are also here.
- [tools.py](tools.py): each tool has three parts that must stay in sync: the Python function, its JSON schema entry in `TOOLS` (what the model sees), and its entry in `TOOL_MAP` (what `run_tool` dispatches). Tools return JSON strings, including errors, because the model cannot see exceptions. `run_tool` guards against invented tool names and bad args so the loop never crashes.
- [index.html](index.html): a single-file chat UI served at `/`. It renders the `tool_calls` returned by `/chat` above each answer.

Gotchas:
- Assistant replies are appended with `reply.model_dump()` on purpose. The raw LiteLLM object carries provider-specific fields that break Pydantic when re-serialized on the next round.
- Model failures in `/chat` are caught and returned as a normal chat message ("Model call failed: ..."), not as a 500.
- The weather tool uses Open-Meteo (no API key needed).
