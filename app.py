import json
import os
import uuid
from datetime import date
from pathlib import Path

import litellm
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from tools import TOOLS, invitation_art, run_tool

# --- Config ---

SYSTEM_PROMPT = (
    "You are Pam, a party planning assistant. Today is {today}.\n"
    "Your tools:\n"
    "- check_party_date for whether an outdoor party's date works. If the day looks bad, offer its backup dates.\n"
    "- get_weather for current conditions, only when the user asks what the weather is like now.\n"
    "- find_recipes for food and drink that fit the theme.\n"
    "- make_mood_board for decor and outfit inspiration.\n"
    "- make_party_playlist for the music, with its decade for a throwback theme.\n"
    "- find_restaurants for restaurants near the party, only when the user asks about restaurants, catering "
    "or ordering food.\n"
    "- make_invitation for an invitation with artwork, only when the user asks for an invitation.\n"
    "First decide what the user is asking for, then call only the tools for that:\n"
    "- A whole party: they describe a party or ask for ideas or a plan, without asking about one part of it. "
    "A cuisine, theme, city or date in the description doesn't make it a question about one part. "
    "Call every tool that applies: check_party_date (if it's outdoors and you have the city and date), "
    "find_recipes for food and for drinks, make_mood_board and make_party_playlist. "
    "Don't call find_restaurants or make_invitation for this. Instead, end the plan with one line saying you "
    "can also find nearby restaurants to order from and make an invitation. "
    "E.g. 'Rooftop dinner in New York this Saturday with Italian food'.\n"
    "- One part: they ask about just the music, the food, the drinks, the weather or date, the decor, "
    "restaurants or the invitation, or want to change one part of an earlier plan. Call only the tool for that "
    "part and leave the rest out, even if they also mention the city, date or theme. "
    "E.g. 'I'm having a rooftop dinner in New York on Saturday, what Italian food should I make?' is only "
    "find_recipes, and 'change the music to 90s hip hop' is only make_party_playlist.\n"
    "Rules:\n"
    "- Call the tool for what the user asked about every time, even if you called it earlier, "
    "so they can see where your answer came from.\n"
    "- If a tool needs the city, date or party length and you don't have it, ask first. "
    "Use what the user already told you earlier in the chat instead of asking again.\n"
    "- Before make_invitation, check the user has typed a clock time for the start, like '7pm'. 'Dinner' or "
    "'evening' is not a start time. If they haven't, don't call the tool: ask what time it starts. "
    "E.g. after planning a dinner with no time given, 'make an invitation for it' gets the reply "
    "'What time does it start?'\n"
    "- Only use what the tools returned. Don't answer from memory, don't write out ingredients or steps "
    "(link to the recipe instead), and only use links a tool gave you. If a tool returns an error, say so.\n"
    "- Reply with a short plan in Markdown, without emojis. The chat already shows the songs, the mood "
    "board images and the invitation, so don't list or repeat them."
)
MAX_TOOL_ROUNDS = 5

# --- The Harness ---


def run_agent(messages: list[dict], tool_calls: list[dict]) -> str:
    """Complete until the model answers without asking for a tool.

    Returns the final text. Each tool call gets added to tool_calls as it happens, so chat()
    still has them to show if a later model call blows up.
    """
    for _ in range(MAX_TOOL_ROUNDS):
        reply = litellm.completion(
            model="vertex_ai/gemini-3.5-flash-lite",
            vertex_location="global",
            messages=messages,
            tools=TOOLS,
        ).choices[0].message

        # Append assistant's reply (text, tool calls, or both) to the context.
        # model_dump() keeps it a plain dict: the raw object carries provider-specific
        # fields that trip Pydantic when LiteLLM re-serializes it next round.
        messages += [reply.model_dump()]

        if not reply.tool_calls:
            return reply.content

        # The harness, not the model, runs each tool and appends the result
        for call in reply.tool_calls:
            args = json.loads(call.function.arguments)
            result = run_tool(call.function.name, args)
            tool_calls += [{"name": call.function.name, "args": args, "result": result}]

            messages += [{"role": "tool", "tool_call_id": call.id, "content": result}]

    return "Sorry, I hit my tool-call limit before finishing."


# --- Session Store ---

# session_id -> list of messages. In-memory, single process.
sessions: dict[str, list] = {}

# --- FastAPI App ---

app = FastAPI()


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    tool_calls: list[dict]


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "index.html")


@app.get("/invitation-art/{art_id}")
def invitation_artwork(art_id: str):
    # make_invitation keeps the artwork in memory and only hands the page this link to it
    if art_id not in invitation_art:
        raise HTTPException(status_code=404, detail="No artwork with that id.")
    image = invitation_art[art_id]
    kind = "image/png" if image.startswith(b"\x89PNG") else "image/jpeg"
    return Response(content=image, media_type=kind)


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    # Get or create the session
    session_id = request.session_id or str(uuid.uuid4())
    if session_id not in sessions:
        # fill in today's date here, not at startup, since the server can stay up for days
        prompt = SYSTEM_PROMPT.format(today=date.today().isoformat())
        sessions[session_id] = [{"role": "system", "content": prompt}]

    # Append user's message to the context
    sessions[session_id] += [{"role": "user", "content": request.message}]

    tool_calls = []
    try:
        response = run_agent(sessions[session_id], tool_calls)
    except Exception as e:
        # Auth, billing, a model that is not running: show it in the chat, not as a 500.
        # any tools that already ran are still in tool_calls, so their cards still show up
        response = f"Model call failed: {type(e).__name__}: {str(e)[:300]}"

    return ChatResponse(response=response, session_id=session_id, tool_calls=tool_calls)


@app.post("/clear")
def clear(session_id: str | None = None):
    sessions.pop(session_id, None)
    return {"status": "ok"}


if __name__ == "__main__":
    # Cloud Run tells us which port to use with $PORT (locally it's just 8000)
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
