"""The tools the harness can run, and the JSON that describes them to the model."""

import json
import math

import requests

# Open-Meteo, TheMealDB and TheCocktailDB are free and need no API key
# ("1" in the recipe URLs is their public test key).
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
MEAL_URL = "https://www.themealdb.com/api/json/v1/1"
COCKTAIL_URL = "https://www.thecocktaildb.com/api/json/v1/1"


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
        # Usually a date outside the ~16 day forecast window, or a badly formatted one.
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


# WMO weather codes Open-Meteo reports, grouped into what matters for an outdoor party.
RAIN_CODES = {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82}
SNOW_CODES = {71, 73, 75, 77, 85, 86}
STORM_CODES = {95, 96, 99}  # thunderstorms; 96 and 99 come with hail
MIN_HIGH_F = 50
MAX_WIND_MPH = 25
MAX_RAIN_CHANCE_PCT = 50


def _weather_problems(day: dict) -> list[str]:
    """List what makes a day bad for an outdoor party. An empty list means the day looks good."""
    problems = []
    code = day["weather_code"]
    if code in STORM_CODES:
        problems.append("thunderstorms with hail" if code in {96, 99} else "thunderstorms")
    elif code in SNOW_CODES:
        problems.append("snow")
    elif code in RAIN_CODES or (day["rain_chance_pct"] or 0) >= MAX_RAIN_CHANCE_PCT:
        problems.append(f"rain ({day['rain_chance_pct']}% chance)")
    if day["max_wind_mph"] >= MAX_WIND_MPH:
        problems.append(f"strong wind ({day['max_wind_mph']} mph)")
    if day["high_f"] < MIN_HIGH_F:
        problems.append(f"cold (high of {day['high_f']}°F)")
    return problems


def check_party_date(location: str, date: str) -> str:
    """Check whether a date suits an outdoor party, and suggest the closest good dates if not."""
    try:
        places = requests.get(GEOCODE_URL, params={"name": location, "count": 1}, timeout=10).json()
        if not places.get("results"):
            return json.dumps({"error": f"City '{location}' was not found."})
        place = places["results"][0]

        # Fetch the whole 16 day window so there are backup dates to choose from.
        data = requests.get(FORECAST_URL, params={
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max",
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "timezone": "auto",
            "forecast_days": 16,
        }, timeout=10).json()
    except requests.RequestException as e:
        return json.dumps({"error": f"Weather service failed: {e}"})

    if data.get("error"):
        return json.dumps({"error": f"Weather service error: {data.get('reason')}"})

    daily = data["daily"]
    days = [
        {
            "date": d,
            "weather_code": code,
            "high_f": high,
            "low_f": low,
            "rain_chance_pct": rain,
            "max_wind_mph": wind,
        }
        for d, code, high, low, rain, wind in zip(
            daily["time"], daily["weather_code"], daily["temperature_2m_max"], daily["temperature_2m_min"],
            daily["precipitation_probability_max"], daily["wind_speed_10m_max"],
        )
        # The furthest days can come back with nulls; they cannot be judged.
        if None not in (code, high, wind)
    ]
    dates = [d["date"] for d in days]
    if date not in dates:
        return json.dumps({
            "error": f"No forecast for {date}. Forecasts cover {dates[0]} to {dates[-1]} (dates as YYYY-MM-DD)."
            if dates else f"No forecast available for {location}."
        })

    party_day = days[dates.index(date)]
    problems = _weather_problems(party_day)
    result = {
        "location": place["name"],
        "date": date,
        "forecast": {k: v for k, v in party_day.items() if k != "weather_code"},
        "good_for_outdoors": not problems,
    }
    if problems:
        result["problems"] = problems
        # Closest good days first, before or after the party date.
        target = dates.index(date)
        backups = sorted(
            (d for i, d in enumerate(days) if i != target and not _weather_problems(d)),
            key=lambda d: abs(dates.index(d["date"]) - target),
        )
        result["backup_dates"] = [
            {k: v for k, v in d.items() if k != "weather_code"} for d in backups[:3]
        ]
        if not backups:
            result["note"] = "No day in the forecast window looks good for outdoors. Consider an indoor venue."
    return json.dumps(result)


def _recipe_lookup(base_url: str, key: str, attempts: list[tuple[str, str]], query: str) -> list[dict]:
    """Try each (endpoint, param) in turn, collecting recipes until there are enough to choose from."""
    recipes = []
    for endpoint, param in attempts:
        response = requests.get(f"{base_url}/{endpoint}", params={param: query}, timeout=10)
        try:
            found = response.json().get(key)
        except ValueError:
            # If the response is not valid JSON, skip this endpoint.
            
            continue
        
        if isinstance(found, list):
            recipes += [r for r in found if r not in recipes]
        if len(recipes) >= 6:
            break
    return recipes


def find_recipes(kind: str, query: str) -> str:
    """Look up food or drink ideas that match a cuisine, ingredient or name."""
    try:
        if kind == "drink":
            attempts = [("filter.php", "i"), ("search.php", "s")]
            found = _recipe_lookup(COCKTAIL_URL, "drinks", attempts, query)
            names = list(dict.fromkeys(d["strDrink"] for d in found))
        elif kind == "food":
            # Cuisine ("Mexican"), then category ("Dessert"), then ingredient, then dish name.
            attempts = [("filter.php", "a"), ("filter.php", "c"), ("filter.php", "i"), ("search.php", "s")]
            found = _recipe_lookup(MEAL_URL, "meals", attempts, query)
            names = list(dict.fromkeys(m["strMeal"] for m in found))
        else:
            return json.dumps({"error": "kind must be 'food' or 'drink'."})
    except requests.RequestException as e:
        return json.dumps({"error": f"Recipe service failed: {e}"})

    if not names:
        return json.dumps({"error": f"No {kind} recipes found for '{query}'. Try a broader term."})
    return json.dumps({"kind": kind, "query": query, "recipes": names[:6]})


def estimate_supplies(guests: int, hours: float, meal: str = "snacks", alcohol: bool = True) -> str:
    """Work out how much food and drink to buy, using standard catering rules of thumb."""
    guests, hours = int(guests), float(hours)
    if guests < 1 or hours <= 0:
        return json.dumps({"error": "guests and hours must both be greater than zero."})

    # Food: appetizer pieces per guest for snacks, otherwise portions by weight.
    if meal == "snacks":
        food = {"appetizer_pieces": math.ceil(guests * min(6 * hours, 15))}
    elif meal == "dinner":
        food = {
            "main_protein_lbs": round(guests * 0.4, 1),
            "side_dish_lbs": round(guests * 0.5, 1),
            "appetizer_pieces": guests * 4,
        }
    elif meal == "dessert":
        food = {"dessert_servings": math.ceil(guests * 1.5)}
    else:
        return json.dumps({"error": "meal must be 'snacks', 'dinner' or 'dessert'."})

    # Drinks: two in the first hour, one for every hour after that.
    total_drinks = math.ceil(guests * (2 + max(hours - 1, 0)))
    if alcohol:
        alcoholic = round(total_drinks * 0.7)
        drinks = {
            "beers": math.ceil(alcoholic * 0.5),
            "wine_bottles": math.ceil(alcoholic * 0.3 / 5),    # 5 glasses per bottle
            "liquor_bottles": math.ceil(alcoholic * 0.2 / 16),  # 16 pours per 750ml
            "soft_drink_servings": total_drinks - alcoholic,
        }
    else:
        drinks = {"soft_drink_servings": total_drinks}

    return json.dumps({
        "guests": guests,
        "hours": hours,
        "food": food,
        "drinks": drinks,
        "ice_lbs": math.ceil(guests * 1.5),
        "cups": math.ceil(guests * 2.5),
        "plates": guests * 2,
        "napkins": guests * 3,
    })


# Share of the budget each category gets, by how the party is catered.
BUDGET_SPLITS = {
    "casual": {"food": 0.40, "drinks": 0.25, "decorations": 0.10, "entertainment": 0.10, "supplies": 0.05, "buffer": 0.10},
    "dinner": {"food": 0.50, "drinks": 0.20, "decorations": 0.10, "entertainment": 0.05, "supplies": 0.05, "buffer": 0.10},
    "kids": {"food": 0.30, "drinks": 0.10, "decorations": 0.15, "entertainment": 0.25, "supplies": 0.10, "buffer": 0.10},
}


def plan_budget(total_budget: float, guests: int, style: str = "casual") -> str:
    """Split a total budget across party categories and work out the cost per guest."""
    total_budget, guests = float(total_budget), int(guests)
    if total_budget <= 0 or guests < 1:
        return json.dumps({"error": "total_budget and guests must both be greater than zero."})
    if style not in BUDGET_SPLITS:
        return json.dumps({"error": f"style must be one of {list(BUDGET_SPLITS)}."})

    per_guest = round(total_budget / guests, 2)
    result = {
        "total_budget": total_budget,
        "per_guest": per_guest,
        "allocation": {category: round(total_budget * share, 2) for category, share in BUDGET_SPLITS[style].items()},
    }
    if per_guest < 10:
        result["warning"] = "Under $10 per guest is tight. Consider a potluck or BYOB."
    return json.dumps(result)


# What the model sees: the "set notes" in the screenplay.
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": (
                "Get the weather for a city. With a date, returns that day's forecast "
                "(high, low, chance of rain, wind); forecasts only reach about 16 days ahead. "
                "Without a date, returns current conditions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name, e.g. 'New York'"},
                    "date": {"type": "string", "description": "Day of the party as YYYY-MM-DD"},
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
                "Check whether a date is good for an outdoor party: returns that day's forecast and flags rain, "
                "snow, hail, strong wind or a high below 50°F. If the day looks bad, also returns the closest "
                "good backup dates. Only works for dates within about 16 days."
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
                "Look up real recipe names for the party menu. For food, query by cuisine "
                "('Mexican', 'Italian'), category ('Dessert', 'Vegetarian'), main ingredient, or dish name. "
                "For drinks, query by base ingredient ('Tequila', 'Gin') or cocktail name."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "kind": {"type": "string", "enum": ["food", "drink"]},
                    "query": {"type": "string", "description": "One cuisine, ingredient or name, e.g. 'Mexican'"},
                },
                "required": ["kind", "query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "estimate_supplies",
            "description": (
                "Calculate how much food, drink, ice and tableware to buy for a party. "
                "Always use this rather than estimating quantities yourself."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "guests": {"type": "integer", "description": "Number of guests"},
                    "hours": {"type": "number", "description": "How long the party lasts, in hours"},
                    "meal": {
                        "type": "string",
                        "enum": ["snacks", "dinner", "dessert"],
                        "description": "What food is served. Defaults to snacks.",
                    },
                    "alcohol": {"type": "boolean", "description": "Whether alcohol is served. Defaults to true."},
                },
                "required": ["guests", "hours"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "plan_budget",
            "description": (
                "Split a total party budget in dollars across food, drinks, decorations, entertainment, "
                "supplies and a buffer, and work out the cost per guest."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "total_budget": {"type": "number", "description": "Total budget in dollars"},
                    "guests": {"type": "integer", "description": "Number of guests"},
                    "style": {
                        "type": "string",
                        "enum": ["casual", "dinner", "kids"],
                        "description": "Kind of party. Defaults to casual.",
                    },
                },
                "required": ["total_budget", "guests"],
            },
        },
    },
]

# What the harness runs: tool name -> Python function.
TOOL_MAP = {
    "get_weather": get_weather,
    "check_party_date": check_party_date,
    "find_recipes": find_recipes,
    "estimate_supplies": estimate_supplies,
    "plan_budget": plan_budget,
}


def run_tool(name: str, args: dict) -> str:
    """Run one tool call. Models invent tool names and arguments; never let that crash the loop."""
    if name not in TOOL_MAP:
        return json.dumps({"error": f"Unknown tool '{name}'. Available: {list(TOOL_MAP)}"})
    try:
        return TOOL_MAP[name](**args)
    except (TypeError, ValueError) as e:
        return json.dumps({"error": f"Bad arguments for {name}: {e}"})
