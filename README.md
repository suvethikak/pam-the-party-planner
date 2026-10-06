# Pam the Party Planner

Pam is a party planning chat agent. Tell her the occasion, city, date, party length and theme,
and she checks the forecast for your date (and suggests backup dates if it looks bad), finds real food and
cocktail recipes for your theme, makes a mood board of images for it, and builds a playlist of real
songs for the theme that you can preview right in the chat. Ask and she will also make an invitation with
artwork generated for your theme, or find restaurants near the party to order from. Every tool call she
makes is shown in the chat as a card you can expand to see its arguments and result.

Built on the course's `gemini-web-tool-calling` base code: FastAPI + LiteLLM + Gemini
(`vertex_ai/gemini-3.5-flash-lite`).

## Use the deployed agent

Open **https://pam-the-party-planner-git-704627147159.europe-west1.run.app** in a browser.

- Type in the box at the bottom, or click one of the sample ideas under the title to send it.
- Give Pam the details she asks for (city, date, party length); she remembers everything said
  earlier in the conversation.
- Tool calls appear above her answer. Click a card to see what was sent to the tool and what came back;
  a red card means the tool returned an error that Pam then worked around.
- Playlists show up as a tracklist: press ▶ to hear a 30 second preview, follow the Apple Music link to the
  full song, or "Copy tracklist" to rebuild it in your own music app.
- Ask for an invitation ("make an invitation for it") and Pam draws one with artwork made for your theme.
  She needs the date, start time and place, and asks for whatever is missing. Use the buttons under it to
  save it as an image or add the party to your calendar.
- Ask where to order food ("any Italian restaurants near the East Village?") for restaurants near the party,
  with their websites, phone numbers and hours.
- Reload the page to start a new conversation. Each tab has its own separate session.

Weather forecasts only reach about 16 days ahead, so pick a party date within the next two weeks to see
the forecast and backup-date tools in action.

## Sample queries

These are also the sample ideas under the title on the page, so you can click them instead of typing.

1. "Rooftop dinner in New York this Saturday with Italian food"
2. "Karaoke birthday in Chicago next week, 3 hours"
3. "Give me ideas for a 70s disco housewarming party"

The first two are full plans: Pam checks the forecast for the date, finds recipes, makes a mood board and
builds a playlist. The first finds Italian recipes; the second has no cuisine, so it falls back to general
party snacks and drinks. The third has no city or date, so Pam skips the forecast and builds the mood board,
recipes and a 1970s-only playlist.

Pam only runs the tools for what you ask about, so a follow-up like "change the music to 90s hip hop" only
rebuilds the playlist. Two tools only run when asked for. Good follow-ups to try after the first query:

- "Make an invitation for it. It starts at 7pm at 55 Water St, Brooklyn."
- "Are there Italian restaurants nearby I could order from instead?"

## Tools

| Tool | What it does | Source |
| --- | --- | --- |
| `get_weather` | Current weather for a city, or the forecast (high, low, chance of rain, wind) for a given date | External API: Open-Meteo. Base code, extended with the optional date |
| `check_party_date` | Whether a date suits an outdoor party: flags a high chance of rain, strong wind or a high below 50°F, and if the day looks bad suggests the closest good backup dates | External API: Open-Meteo. Original |
| `find_recipes` | Real food or cocktail recipes for a cuisine, ingredient or name, each linking to its ingredients and instructions; if nothing matches, 6 random party snacks or party drinks instead | External API: TheMealDB and TheCocktailDB. Original |
| `make_mood_board` | A mood board of 9 images for the party's theme, for decor and outfit inspiration | External API: Are.na. Original |
| `find_restaurants` | Up to 8 real restaurants near the party to cater or order from, by cuisine if given, with distance, address, website, phone and hours when known | External API: OpenStreetMap (Overpass, with Nominatim as the backup). Original |
| `make_invitation` | An invitation card for the party with artwork generated for the theme, plus an add-to-calendar link; the page lets you save it as an image or download a calendar file | Google's Gemini image model on Vertex AI. Original |
| `make_party_playlist` | A playlist of real songs that fills the party's length, from artists and genres that fit the theme, optionally from one decade; each song has a 30 second preview | External API: iTunes Search. Original |

The tools live in `tools.py`; the harness loop, system prompt and routes are in `app.py`; the chat page
is `index.html`. None of the APIs need a key; the invitation artwork uses the same Google Cloud login as
Gemini. Tools report problems (unknown city, date outside the
forecast window, bad arguments) back to the model as JSON errors instead of crashing.

## Run it locally

1. A GCP project with billing and the Agent Platform API enabled
   (older docs and the endpoint itself still call it Vertex AI).
2. `gcloud auth application-default login`. The app uses your gcloud default project.
3. `uv run app.py`, then open http://localhost:8000.

The server listens on the port in the `PORT` environment variable (8000 if unset), which is how
Cloud Run runs it.

## Team

Suvethika Kandasamy (sk5697) and Gabriella Chu (gc3203).
