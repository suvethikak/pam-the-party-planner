# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A party planner agent for a class assignment (Columbia IEOR4570). It is built on the course's
`gemini-web-tool-calling` base code: FastAPI + LiteLLM + Gemini, with a single-page chat UI that shows every
tool call the agent makes.

The assignment requires at least three tools the agent calls, at least one of which fetches external data
(an API or database), and at least two original tools (not from the base code). Keep those requirements met.

## Branches

- `party-planner` holds all the party planner work.
- `get_weather` in `tools.py` must stay identical to the base code's version. New weather behaviour goes in a
  separate tool (as `check_party_date` does).

## Commands

There is no test suite, linter or build step.

```bash
uv run app.py        # serve on http://localhost:8000
```

The model call needs Google Cloud credentials: `gcloud auth application-default login`, with a default
project that has billing and the Vertex AI (Agent Platform) API enabled.

Call one tool directly, without the model:

```bash
uv run python -c "from tools import run_tool; print(run_tool('check_party_date', {'location': 'New York', 'date': '2026-10-05'}))"
```

Run one full chat turn through the agent without a browser:

```bash
uv run python -c "
from fastapi.testclient import TestClient; import app
r = TestClient(app.app).post('/chat', json={'message': 'Outdoor party in New York on 2026-10-05 for 15 people'}).json()
print(r['tool_calls']); print(r['response'])"
```

## Architecture

- `app.py`: the system prompt, `run_agent()` (the harness loop) and the FastAPI routes. `run_agent()` calls
  `vertex_ai/gemini-3.5-flash-lite` through LiteLLM with `TOOLS`, runs any tool calls the model asks for,
  appends each result as a `tool` message, and repeats until the model answers in text or `MAX_TOOL_ROUNDS`
  is hit. Assistant replies are stored with `model_dump()` because the raw LiteLLM objects break
  re-serialization on the next round. Conversation history lives in the in-memory `sessions` dict, keyed by
  the `session_id` the page sends back on every `/chat`. `/chat` returns the final text plus a list of every
  tool call made.
- `tools.py`: each tool is a plain Python function, plus `TOOLS` (the JSON schemas the model sees) and
  `TOOL_MAP` (name → function). `run_tool()` dispatches by name and turns unknown tools and bad arguments
  into error JSON.
- `index.html`: the chat page. It renders each entry in `tool_calls` above the assistant's answer.

### Tool conventions

- Every tool returns a JSON **string**, and reports failures (network errors, not-found, invalid input) as
  `{"error": "..."}` rather than raising. The model cannot see exceptions, and the error text is what lets
  it recover or ask the user.
- The model may pass numbers as strings, so tools that take numbers convert them with `int()`/`float()`.
  `run_tool()` catches the resulting `ValueError`/`TypeError`.
- Adding a tool takes five changes: the function, its schema in `TOOLS`, its entry in `TOOL_MAP`, a
  mention in `SYSTEM_PROMPT` saying when to use it, and an entry in `TOOL_STYLE` in `index.html`. Also add it
  to the tools table in `README.md`.

### Frontend

`index.html` is a single file with inline CSS and JS and no build step or JS dependencies (only the DM Sans
Google Font, used for everything including the title). It has a light, candlelit dinner party theme, taken from a
New Year's Eve table: ivory and greige, charcoal ink for text, the user's bubbles and buttons, and taper-candle
colors (`--blush`, `--butter`, `--sage`, `--taupe`, `--silver`) as tool-card accents.

- Background decorations: a warm candle glow on `body`, silver paper stars on threads (`.hanging-star` in
  `#stars`, generated in JS) that sway gently, plus a CSS-only chrome disco ball (`.disco`) hanging off the chat
  panel. Under `prefers-reduced-motion` the stars and disco ball stay but stop moving.
- `TOOL_STYLE` maps each tool name to the label and color of its card. `toolCard()` renders each call
  as a collapsible `<details>` showing the args and the pretty-printed result. A result with an `error` key
  is shown in red. Unknown tools fall back to a card labelled with the tool's name.
- A `make_party_playlist` card opens by default and shows `playlistView()`: one `songRow()` per song with
  artwork, a ▶ preview button and an Apple Music link, plus a "Copy tracklist" button; the raw JSON sits in a
  nested `<details class="raw">`. All previews share one `Audio` element (`toggleSong()`/`stopSong()`), and
  `body.music` speeds up the disco ball while one plays.
- `SAMPLES` holds the sample-prompt chips in the header. Clicking one sends it as is.
- The user's messages and everything in tool cards are set with `textContent`, never `innerHTML`. The model's
  answer is rendered as Markdown with `marked`, then sanitized with DOMPurify before it reaches `innerHTML`.

### External APIs (no keys needed)

- Open-Meteo (geocoding + forecast): used by `get_weather` and `check_party_date`. Daily forecasts only reach
  16 days ahead, and the furthest days can come back with `null` values.
- TheMealDB and TheCocktailDB (public test key `1` in the URL): used by `find_recipes`. With the test key,
  `filter.php` can return just one match, so `_recipe_lookup()` collects results across several endpoints.
  TheCocktailDB answers an unknown ingredient with an empty body rather than JSON. TheMealDB has been
  unreachable from some networks.
- iTunes Search: used by `make_party_playlist`. A search term also matches song titles, so songs titled just
  the search ("80s", "Beach Party") are skipped. `_bare_title()` strips "(Remastered)", "(feat. ...)" and
  " - Radio Edit" so versions of one song are not both played. Apple rate limits it to roughly 20 calls a minute.
