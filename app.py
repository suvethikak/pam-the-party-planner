import os
import uuid
from typing import Any, Dict, List
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import litellm
from tools import TOOLS, run_tool

app = FastAPI(title="Party Planning Agent")

SYSTEM_PROMPT = """You are an expert, creative Party Planning Assistant.
Your job is to help users conceptualize, budget, design, and invite guests for memorable events.

Capabilities & Guidelines:
1. When discussing themes or visual aesthetics, use `get_theme_moodboard` to give the user image ideas and Pinterest search links.
2. When users mention guest count, party duration, or expenses, use `calculate_party_budget` to give realistic estimates for food, drinks, and ice.
3. When users are ready to invite people or draft invitations, use `generate_partiful_kit` to draft creative copy and direct them to Partiful.
4. Maintain a warm, festive, and highly organized tone. Present budget and quantity breakdowns in structured lists or clear summaries.
"""

MODEL = os.environ.get("MODEL_NAME", "gemini/gemini-2.5-flash")
MAX_TOOL_ROUNDS = 5

sessions: Dict[str, List[Dict[str, Any]]] = {}


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    tool_calls: List[Dict[str, Any]] = []


def run_agent(session_history: List[Dict[str, Any]]) -> tuple[str, List[Dict[str, Any]]]:
    executed_tool_calls = []
    
    for _ in range(MAX_TOOL_ROUNDS):
        response = litellm.completion(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + session_history,
            tools=TOOLS,
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        
        if hasattr(message, "tool_calls") and message.tool_calls:
            session_history.append(message.model_dump())
            
            for tool_call in message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = eval(tool_call.function.arguments) if isinstance(tool_call.function.arguments, str) else tool_call.function.arguments
                
                tool_output = run_tool(fn_name, fn_args)
                
                executed_tool_calls.append({
                    "tool": fn_name,
                    "args": fn_args,
                    "output": tool_output
                })
                
                session_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_output
                })
        else:
            final_text = message.content or ""
            session_history.append({"role": "assistant", "content": final_text})
            return final_text, executed_tool_calls

    return "Reached maximum tool processing limit.", executed_tool_calls


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())
    if session_id not in sessions:
        sessions[session_id] = []
        
    history = sessions[session_id]
    history.append({"role": "user", "content": request.message})
    
    try:
        reply_text, tools_executed = run_agent(history)
        return ChatResponse(
            response=reply_text,
            session_id=session_id,
            tool_calls=tools_executed
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/", response_class=HTMLResponse)
async def root():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8080, reload=True)
