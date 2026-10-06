"""The tools the harness can run, and the JSON that describes them to the model."""

import json
import random

import requests

# all of these APIs are free and don't need a key (the "1" in the recipe URLs is their public test key)
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
MEAL_URL = "https://www.themealdb.com/api/json/v1/1"
COCKTAIL_URL = "https://www.thecocktaildb.com/api/json/v1/1"
ITUNES_URL = "https://itunes.apple.com/search"
ARENA_URL = "https://api.are.na/v2"


def get_weather(location: str, date: str | None = None) -> str:
    """Get the current weather for a location"""
    try:
        places = requests.get(GEOCODE_URL, params={"name": location, "count": 1}, timeout=10).json()
        if not places.get("results"):
            return json.dumps({"error": f"City '{location}' was not found."})
        place = places["results"][0]

        params = {
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "timezone": "auto",
        }
        if date:
            params |= {
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max",
                "start_date": date,
                "end_date": date,
            }
        else:
            params |= {"current": "temperature_2m,relative_humidity_2m,wind_speed_10m"}

        data = requests.get(FORECAST_URL, params=params, timeout=10).json()
    except requests.RequestException as e:
        # The model cannot see an exception. Return something it can reason about.
        return json.dumps({"error": f"Weather service failed: {e}"})

    if data.get("error"):
        # usually means the date is more than ~16 days out, or not formatted right
        return json.dumps({"error": f"No forecast for {date}: {data.get('reason')}"})

    if date:
        daily = data["daily"]
        return json.dumps({
            "location": place["name"],
            "date": date,
            "high_f": daily["temperature_2m_max"][0],
            "low_f": daily["temperature_2m_min"][0],
            "rain_chance_pct": daily["precipitation_probability_max"][0],
            "max_wind_mph": daily["wind_speed_10m_max"][0],
        })

    current = data["current"]
    return json.dumps({
        "location": place["name"],
        "temp_f": current["temperature_2m"],
        "humidity": current["relative_humidity_2m"],
        "wind_mph": current["wind_speed_10m"],
    })


def weather_problems(day: dict) -> list[str]:
    """Returns what's wrong with a day for an outdoor party (an empty list means it's fine)."""
    if None in day.values():
        return ["no forecast yet"]  # days far out sometimes come back blank
    problems = []
    if day["rain_chance_pct"] >= 50:
        problems.append(f"{day['rain_chance_pct']}% chance of rain")
    if day["max_wind_mph"] >= 25:
        problems.append(f"strong wind ({day['max_wind_mph']} mph)")
    if day["high_f"] < 50:
        problems.append(f"cold (high of {day['high_f']}°F)")
    return problems


def check_party_date(location: str, date: str) -> str:
    """Checks if a date works for an outdoor party, and finds backup dates if it doesn't."""
    try:
        places = requests.get(GEOCODE_URL, params={"name": location, "count": 1}, timeout=10).json()
        if not places.get("results"):
            return json.dumps({"error": f"City '{location}' was not found."})
        place = places["results"][0]

        # grab all 16 days so we have backup dates to pick from
        data = requests.get(FORECAST_URL, params={
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "daily": "temperature_2m_max,precipitation_probability_max,wind_speed_10m_max",
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "timezone": "auto",
            "forecast_days": 16,
        }, timeout=10).json()
    except requests.RequestException as e:
        return json.dumps({"error": f"Weather service failed: {e}"})

    dates = data["daily"]["time"]
    if date not in dates:
        return json.dumps({"error": f"No forecast for {date}. Pick a date from {dates[0]} to {dates[-1]}."})

    days = []
    for i in range(len(dates)):
        days.append({
            "date": dates[i],
            "high_f": data["daily"]["temperature_2m_max"][i],
            "rain_chance_pct": data["daily"]["precipitation_probability_max"][i],
            "max_wind_mph": data["daily"]["wind_speed_10m_max"][i],
        })

    party_day = days[dates.index(date)]
    problems = weather_problems(party_day)
    result = {"location": place["name"], "forecast": party_day, "good_for_outdoors": not problems}

    if problems:
        result["problems"] = problems
        # backup dates = the good days closest to the party
        good_days = [day for day in days if not weather_problems(day)]
        good_days.sort(key=lambda day: abs(dates.index(day["date"]) - dates.index(date)))
        result["backup_dates"] = good_days[:3]
    return json.dumps(result)


def find_recipes(kind: str, query: str) -> str:
    """Finds food or drink recipes for a cuisine, ingredient or name."""
    if kind == "food":
        # try the query as a cuisine, then a category, then an ingredient, then a dish name
        urls = [MEAL_URL + "/filter.php?a=", MEAL_URL + "/filter.php?c=",
                MEAL_URL + "/filter.php?i=", MEAL_URL + "/search.php?s="]
        list_key, name_key, id_key = "meals", "strMeal", "idMeal"
        page = "https://www.themealdb.com/meal/"
        backup = MEAL_URL + "/filter.php?c=Side"  # closest thing they have to snacks
        backup_name = "snacks"
    elif kind == "drink":
        # try the query as an ingredient, then a cocktail name
        urls = [COCKTAIL_URL + "/filter.php?i=", COCKTAIL_URL + "/search.php?s="]
        list_key, name_key, id_key = "drinks", "strDrink", "idDrink"
        page = "https://www.thecocktaildb.com/drink/"
        backup = COCKTAIL_URL + "/filter.php?c=Punch / Party Drink"
        backup_name = "drinks"
    else:
        return json.dumps({"error": "kind must be 'food' or 'drink'."})

    recipes = []
    for url in urls:
        try:
            found = requests.get(url + query, timeout=10).json().get(list_key)
        except requests.RequestException:
            continue  # sometimes the API sends back an empty page instead of JSON
        if not isinstance(found, list):
            continue  # "no results" shows up as None or the text "no data found"
        for recipe in found:
            # the recipe's page has the ingredients and steps
            recipe = {"name": recipe[name_key], "link": page + recipe[id_key]}
            if recipe not in recipes:
                recipes.append(recipe)
        if len(recipes) >= 6:
            break

    result = {"kind": kind, "query": query, "recipes": recipes[:6]}

    # nothing matched, so fall back to general party snacks or drinks
    if not recipes:
        try:
            found = requests.get(backup, timeout=10).json().get(list_key)
        except requests.RequestException as e:
            return json.dumps({"error": f"Recipe service failed: {e}"})
        backup_recipes = [{"name": recipe[name_key], "link": page + recipe[id_key]} for recipe in found]
        result["recipes"] = random.sample(backup_recipes, 6)  # random so it's not always the same A-Z ones
        result["note"] = f"Nothing matched '{query}', so these are general party {backup_name}."
    return json.dumps(result)


def make_mood_board(searches: list) -> str:
    """Makes a 9-image mood board from Are.na boards, split between the searches."""
    searches = searches[:3]
    if not searches:
        return json.dumps({"error": "Give 1 to 3 searches, like ['garden', 'birthday', 'disco']."})
    per_search = 9 // len(searches)  # 9 for one search, 4 each for two, 3 each for three

    # Are.na answers 429 with a web page instead of JSON when it gets too many requests
    busy = json.dumps({
        "error": "The image service (Are.na) is busy right now. Don't call make_mood_board again in this reply; "
                 "tell the user to try the mood board again in a minute."
    })

    images, empty = [], []
    try:
        for search in searches:
            found = []
            response = requests.get(ARENA_URL + "/search/channels", params={"q": search, "per": 5}, timeout=10)
            if response.status_code == 429:
                return busy
            boards = response.json()
            for board in boards["channels"]:
                response = requests.get(f"{ARENA_URL}/channels/{board['slug']}/contents", params={"per": 20}, timeout=10)
                if response.status_code == 429:
                    return busy
                contents = response.json()
                for block in contents["contents"]:
                    if block["class"] == "Image" and len(found) < per_search:
                        found.append({
                            "image": block["image"]["thumb"]["url"],
                            "link": f"https://www.are.na/block/{block['id']}",
                            "board": board["title"],
                        })
                if len(found) == per_search:
                    break
            if not found:
                empty.append(search)
            images += found
    except requests.RequestException as e:
        return json.dumps({"error": f"Are.na failed: {e}"})

    if not images:
        return json.dumps({"error": f"No images found for {searches}. Try common words, like 'party' or 'friends'."})
    result = {"searches": searches, "images": images}
    if empty:
        result["no_images_for"] = empty  # so the model knows which searches came up empty
    return json.dumps(result)


def make_party_playlist(searches: list, hours: float, decade: int | None = None) -> str:
    """Builds a playlist of real songs that fits the theme and lasts as long as the party."""
    party_seconds = float(hours) * 3600
    if party_seconds <= 0:
        return json.dumps({"error": "hours must be more than 0."})

    # one list of songs per search
    song_lists = []
    try:
        for search in searches[:4]:
            data = requests.get(ITUNES_URL, params={"term": search, "entity": "song", "limit": 100}, timeout=10).json()
            songs = []
            for track in data["results"]:
                year = int(track.get("releaseDate", "0000")[:4])
                if decade and not (decade <= year < decade + 10):
                    continue  # wrong decade
                seconds = track.get("trackTimeMillis", 0) // 1000
                songs.append({
                    "title": track["trackName"],
                    "artist": track["artistName"],
                    "year": year,
                    "length": f"{seconds // 60}:{seconds % 60:02d}",
                    "seconds": seconds,
                    "preview": track.get("previewUrl"),
                    "link": track.get("trackViewUrl"),
                    "artwork": track.get("artworkUrl100"),
                })
            song_lists.append(songs)
    except requests.RequestException as e:
        return json.dumps({"error": f"Music search failed: {e}"})

    # take turns pulling a song from each search until the party is full (max 60 songs)
    playlist, titles, total = [], [], 0
    while total < party_seconds and len(playlist) < 60 and any(song_lists):
        for songs in song_lists:
            if not songs:
                continue
            song = songs.pop(0)
            title = song["title"].split(" (")[0].lower()  # so "Song (Remastered)" and "Song" count as the same
            if title not in titles and total < party_seconds:
                playlist.append(song)
                titles.append(title)
                total += song["seconds"]

    if not playlist:
        return json.dumps({"error": f"No songs found for {searches}. Try other genres or well-known artists."})
    return json.dumps({
        "party_minutes": round(party_seconds / 60),
        "playlist_minutes": round(total / 60),
        "songs": playlist,
    })


# What the model sees: the "set notes" in the screenplay.
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": (
                "Get the weather for a city: current conditions, or with a date, that day's forecast "
                "(high, low, chance of rain, wind). Forecasts only go about 16 days ahead."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name, e.g. 'New York'"},
                    "date": {"type": "string", "description": "Optional day as YYYY-MM-DD"},
                },
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_party_date",
            "description": (
                "Check if a date is good for an outdoor party. Flags 50%+ chance of rain, wind of 25+ mph or a "
                "high below 50°F, and if the day is bad, returns the closest good backup dates. "
                "Only works for dates within about 16 days."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name, e.g. 'New York'"},
                    "date": {"type": "string", "description": "Day of the party as YYYY-MM-DD"},
                },
                "required": ["location", "date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_recipes",
            "description": (
                "Find up to 6 real recipes, each with a name and a link to its ingredients and instructions. "
                "If nothing matches, returns random party snacks or party drinks instead, with a note."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "kind": {"type": "string", "enum": ["food", "drink"]},
                    "query": {
                        "type": "string",
                        "description": (
                            "One word or name. Food: a cuisine ('Mexican'), category ('Dessert', 'Vegetarian'), "
                            "ingredient or dish. Drinks: a base spirit ('Tequila') or cocktail name."
                        ),
                    },
                },
                "required": ["kind", "query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "make_mood_board",
            "description": (
                "Make a mood board of 9 images for decor and outfit inspiration, from Are.na boards. Boards are "
                "found by their names, so use common one or two word terms someone would name a board."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "searches": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "1 to 3 searches, one for each part of the party the user mentioned: the setting "
                            "('garden', 'beach'), the occasion ('dinner party', 'birthday') and the theme "
                            "('fiesta', 'disco', '1920s'). Skip parts they didn't mention. "
                            "E.g. an Italian rooftop dinner: ['city', 'tablescape', 'pizza']."
                        ),
                    },
                },
                "required": ["searches"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "make_party_playlist",
            "description": (
                "Build a playlist of real songs that lasts as long as the party, taking turns between the "
                "searches. Each song has a 30 second preview the user can play in the chat."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "searches": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "1 to 4 artists or genres that fit the theme. Well-known artists work best "
                            "('Selena', 'Bad Bunny'); genres work too ('cumbia', 'disco')."
                        ),
                    },
                    "hours": {"type": "number", "description": "How long the party lasts, in hours"},
                    "decade": {
                        "type": "integer",
                        "description": "Only songs from this decade, e.g. 1980 for an 80s party. Leave out for any era.",
                    },
                },
                "required": ["searches", "hours"],
            },
        },
    },
]

# What the harness runs: tool name -> Python function.
TOOL_MAP = {
    "get_weather": get_weather,
    "check_party_date": check_party_date,
    "find_recipes": find_recipes,
    "make_mood_board": make_mood_board,
    "make_party_playlist": make_party_playlist,
}


def run_tool(name: str, args: dict) -> str:
    """Run one tool call. Models invent tool names and arguments; never let that crash the loop."""
    if name not in TOOL_MAP:
        return json.dumps({"error": f"Unknown tool '{name}'. Available: {list(TOOL_MAP)}"})
    try:
        return TOOL_MAP[name](**args)
    except (TypeError, ValueError, KeyError) as e:
        return json.dumps({"error": f"Bad arguments for {name}: {e}"})
