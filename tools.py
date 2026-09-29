import json
import os
import urllib.parse
import httpx

UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "YOUR_UNSPLASH_ACCESS_KEY")


def get_theme_moodboard(theme: str) -> str:
    """
    Fetches visual inspiration images from Unsplash API and generates a Pinterest search link.
    """
    pinterest_query = urllib.parse.quote(f"{theme} party decor aesthetic")
    pinterest_url = f"https://www.pinterest.com/search/pins/?q={pinterest_query}"

    images = []
    if UNSPLASH_ACCESS_KEY and UNSPLASH_ACCESS_KEY != "YOUR_UNSPLASH_ACCESS_KEY":
        try:
            url = f"https://api.unsplash.com/search/photos?query={urllib.parse.quote(theme + ' party')}&per_page=3"
            headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
            response = httpx.get(url, headers=headers, timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                for item in data.get("results", []):
                    images.append({
                        "description": item.get("alt_description", theme),
                        "url": item.get("urls", {}).get("regular"),
                        "photographer": item.get("user", {}).get("name")
                    })
        except Exception as e:
            pass

    return json.dumps({
        "theme": theme,
        "pinterest_search_url": pinterest_url,
        "sample_images": images if images else "Add UNSPLASH_ACCESS_KEY env variable for live image previews."
    })


def calculate_party_budget(guest_count: int, duration_hours: float = 3.0, budget_tier: str = "moderate") -> str:
    """
    Calculates estimated food, drink, and supply quantities and costs for a party.
    """
    tier_multipliers = {"budget": 15.0, "moderate": 35.0, "premium": 75.0}
    cost_per_head = tier_multipliers.get(budget_tier.lower(), 35.0)
    
    # 2 drinks per person for hour 1, 1 drink per hour after
    drinks_per_person = 2 + max(0.0, duration_hours - 1.0)
    total_drinks = int(guest_count * drinks_per_person)
    wine_bottles = int(total_drinks * 0.4 / 5)  # 5 glasses per bottle
    beer_cans = int(total_drinks * 0.4)
    cocktails_or_mocktails = int(total_drinks * 0.2)

    total_estimated_budget = guest_count * cost_per_head

    return json.dumps({
        "guest_count": guest_count,
        "duration_hours": duration_hours,
        "budget_tier": budget_tier,
        "estimated_total_cost_usd": total_estimated_budget,
        "suggested_quantities": {
            "total_drinks_needed": total_drinks,
            "wine_bottles_estimate": wine_bottles,
            "beer_cans_estimate": beer_cans,
            "cocktail_servings_estimate": cocktails_or_mocktails,
            "appetizer_pieces_estimate": guest_count * 6 if duration_hours <= 3 else guest_count * 10,
            "ice_lbs_estimate": guest_count * 1.5
        }
    })


def generate_partiful_kit(title: str, theme: str, date_time: str, location: str, dress_code: str = "Casual") -> str:
    """
    Generates structured copy and a launch link for setting up a Partiful invitation page.
    """
    partiful_create_url = "https://partiful.com/create"
    
    description_draft = (
        f"🎉 YOU'RE INVITED! 🎉\n\n"
        f"Theme: {theme}\n"
        f"When: {date_time}\n"
        f"Where: {location}\n"
        f"Dress Code: {dress_code}\n\n"
        f"RSVP so we can stock up on food & drinks!"
    )

    return json.dumps({
        "partiful_launch_url": partiful_create_url,
        "event_title": title,
        "theme": theme,
        "formatted_description_copy": description_draft,
        "setup_instructions": [
            "1. Click the partiful_launch_url to open Partiful.",
            "2. Paste the event_title and formatted_description_copy into the event fields.",
            "3. Set the date and location details as listed above.",
            "4. Publish and share your invite link with guests!"
        ]
    })


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_theme_moodboard",
            "description": "Fetches mood board images and Pinterest search links for party themes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "theme": {"type": "string", "description": "The theme or aesthetic for the party (e.g. 70s Disco, Speakeasy, Tropical Luau)"}
                },
                "required": ["theme"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_party_budget",
            "description": "Calculates food, drink, ice, and budget requirements based on party size and duration.",
            "parameters": {
                "type": "object",
                "properties": {
                    "guest_count": {"type": "integer", "description": "Number of expected guests"},
                    "duration_hours": {"type": "number", "description": "Duration of party in hours (default 3.0)"},
                    "budget_tier": {"type": "string", "enum": ["budget", "moderate", "premium"], "description": "Budget level"}
                },
                "required": ["guest_count"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_partiful_kit",
            "description": "Generates formatted invitation copy and quick links for creating a Partiful invite.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title of the party event"},
                    "theme": {"type": "string", "description": "Party theme"},
                    "date_time": {"type": "string", "description": "Date and time of event"},
                    "location": {"type": "string", "description": "Location or venue"},
                    "dress_code": {"type": "string", "description": "Suggested dress code or attire"}
                },
                "required": ["title", "theme", "date_time", "location"]
            }
        }
    }
]

TOOL_MAP = {
    "get_theme_moodboard": get_theme_moodboard,
    "calculate_party_budget": calculate_party_budget,
    "generate_partiful_kit": generate_partiful_kit
}


def run_tool(name: str, args: dict) -> str:
    if name not in TOOL_MAP:
        return json.dumps({"error": f"Tool '{name}' not found."})
    try:
        return TOOL_MAP[name](**args)
    except Exception as e:
        return json.dumps({"error": str(e)})
