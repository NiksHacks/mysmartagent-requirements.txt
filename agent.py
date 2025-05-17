
import os, json, openai
from fastapi import FastAPI
from pydantic import BaseModel

# Load prompt and tools at startup
with open("Prompt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

with open("Tools.json", "r", encoding="utf-8") as f:
    TOOLS = json.load(f)["tools"]

FUNCTIONS = [{"name": t["name"], "description": t["description"], "parameters": t["parameters"]} for t in TOOLS]

# ---- Handlers ----
def restart_workflow_handler(params):
    name = params.get("name", "unknown")
    # TODO: replace with real logic
    return {"ok": True, "message": f"Workflow '{name}' restarted (placeholder)"}

# Map tool names to handlers
HANDLERS = {
    "restart_workflow": restart_workflow_handler,
    # Add more tool handlers here...
}

# OpenAI key from env
openai.api_key = os.getenv("OPENAI_API_KEY")

# FastAPI app
app = FastAPI()

class ChatRequest(BaseModel):
    content: str

# Shared conversation state (simple demo)
messages = [{"role": "system", "content": SYSTEM_PROMPT}]

def run_agent(user_input):
    if user_input is not None:
        messages.append({"role": "user", "content": user_input})

    response = openai.ChatCompletion.create(
        model="gpt-4o-audio-preview",   # or gpt-4o (depends on availability)
        messages=messages,
        functions=FUNCTIONS,
        function_call="auto"
    )
    msg = response.choices[0].message

    if msg.get("function_call"):
        fn_name = msg["function_call"]["name"]
        fn_args = json.loads(msg["function_call"]["arguments"])
        handler = HANDLERS.get(fn_name, lambda _: {"error": "handler not implemented"})
        result = handler(fn_args)
        messages.append({"role": "function", "name": fn_name, "content": json.dumps(result)})
        return run_agent(None)  # continue, maybe model wants to answer
    else:
        messages.append({"role": "assistant", "content": msg["content"]})
        return msg["content"]

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    reply = run_agent(req.content)
    return {"reply": reply}

# Optional CLI loop
if __name__ == "__main__":
    print("Type messages; Ctrl+C to quit.")
    while True:
        try:
            user_in = input("You: ")
            print("Bot:", run_agent(user_in))
        except KeyboardInterrupt:
            break
