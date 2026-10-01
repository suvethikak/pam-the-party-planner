# party-planner-agent

A party planning agent, built on `gemini-web-tool-calling`: FastAPI + LiteLLM + Gemini,
with every tool call shown in the chat above the assistant's answer.

## Tools

| Tool | What it does | Source |
| --- | --- | --- |
| `get_weather` | Current weather (temperature, humidity, wind) for the party's city | External API: Open-Meteo. From the base code |
| `check_party_date` | Forecast for the party date; if it has rain, snow, hail, strong wind or a high below 50°F, suggests the closest good dates | External API: Open-Meteo. Original |
| `find_recipes` | Real food and cocktail ideas for a cuisine, ingredient or name | External API: TheMealDB and TheCocktailDB. Original |
| `estimate_supplies` | How much food, drink, ice and tableware to buy | Local calculation. Original |
| `plan_budget` | Splits a budget across categories, with cost per guest | Local calculation. Original |

The tools live in `tools.py`; the harness loop and the system prompt are in `app.py`.
None of the APIs need a key.

## Setup

1. A GCP project with billing and the Agent Platform API enabled
   (older docs and the endpoint itself still call it Vertex AI)
2. `gcloud auth application-default login`. The app uses your gcloud default
   project, so run `gemini-hello-world` first to check it.
3. `uv run app.py`, then open http://localhost:8000

Try: "I'm throwing a Mexican-themed rooftop dinner party in New York this Saturday,
6 to 10pm, for 20 people, with a $500 budget. Help me plan it."
