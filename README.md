# Pam the Party Planner

Pam is a party planning chat agent. Tell her the occasion, city, date, guest count, budget and theme,
and she checks the forecast for your date (and suggests backup dates if it looks bad), finds real food and
cocktail recipes for your theme, works out how much to buy, and splits your budget. Every tool call she
makes is shown in the chat as a card you can expand to see its arguments and result.

Built on the course's `gemini-web-tool-calling` base code: FastAPI + LiteLLM + Gemini
(`vertex_ai/gemini-3.5-flash-lite`).

## Use the deployed agent

Open **https://pam-the-party-planner-git-704627147159.europe-west1.run.app** in a browser.

- Type in the box at the bottom, or click one of the sample ideas under the title to send it.
- Give Pam the details she asks for (city, date, guest count, budget); she remembers everything said
  earlier in the conversation.
- Tool calls appear above her answer. Click a card to see what was sent to the tool and what came back;
  a red card means the tool returned an error that Pam then worked around.
- Reload the page to start a new conversation. Each tab has its own separate session.
- The "Party lights" button turns the disco ball, light beams and confetti off (and back on).

Weather forecasts only reach about 16 days ahead, so pick a party date within the next two weeks to see
the forecast and backup-date tools in action.

## Sample queries

1. "Mexican rooftop dinner in New York this Saturday, 20 people, $250"
2. "Is next Sunday good for a picnic in Chicago?"
3. "Asian inspired cocktail ideas with tequila"

The first query exercises most of the tools at once: the date forecast, recipes, supplies and budget.

## Tools

| Tool | What it does | Source |
| --- | --- | --- |
| `get_weather` | Current weather for a city, or the forecast (high, low, chance of rain, wind) for a given date | External API: Open-Meteo. Base code, extended with the optional date |
| `check_party_date` | Whether a date suits an outdoor party: flags rain, snow, hail, strong wind or a high below 50°F, and if the day looks bad suggests the closest good backup dates | External API: Open-Meteo. Original |
| `find_recipes` | Real food or cocktail ideas for a cuisine, ingredient or name | External API: TheMealDB and TheCocktailDB. Original |
| `estimate_supplies` | How much food, drink, ice and tableware to buy for a guest count and party length | Local calculation. Original |
| `plan_budget` | Splits a total budget across food, drinks, decorations, entertainment, supplies and a buffer, with cost per guest | Local calculation. Original |

The tools live in `tools.py`; the harness loop, system prompt and routes are in `app.py`; the chat page
is `index.html`. None of the APIs need a key. Tools report problems (unknown city, date outside the
forecast window, bad arguments) back to the model as JSON errors instead of crashing.

## Run it locally

1. A GCP project with billing and the Agent Platform API enabled
   (older docs and the endpoint itself still call it Vertex AI).
2. `gcloud auth application-default login`. The app uses your gcloud default project.
3. `uv run app.py`, then open http://localhost:8000.

The server listens on the port in the `PORT` environment variable (8000 if unset), which is how
Cloud Run runs it.

## Deployment

Deployed to Cloud Run (region `europe-west1`) with continuous deployment from this GitHub repo:
every push to `main` builds and deploys a new revision.

## Team

Suvethika Kandasamy (sk5697) and Gaby Chu (gc3203).
