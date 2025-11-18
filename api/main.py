from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import httpx
import asyncio
import os

app = FastAPI()

PERSONAS = {
    "Empath": "You are a kind, emotionally intelligent counselor. Focus on feelings and support.",
    "Strategist": "You are a logical advisor. Give structured, actionable plans.",
    "Avara": "You are a financial literacy coach for beginners. Use simple, clear advice.",
    "Chronicler": "You are a well-informed analyst. Provide useful facts or context."
}

class QueryRequest(BaseModel):
    user_message: str

async def ask_persona(name: str, system_prompt: str, user_msg: str) -> str:
    payload = {
        "model": "glm-4",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg}
        ],
        "temperature": 0.7,
        "max_tokens": 400
    }
    headers = {
        "Authorization": f"Bearer {os.getenv('GLM_API_KEY')}",
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient(timeout=25.0) as client:
        try:
            r = await client.post("https://open.bigmodel.cn/api/paas/v4/chat/completions", json=payload, headers=headers)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return f"[{name} unavailable: {str(e)[:60]}]"

@app.post("/council")
async def council_api(req: QueryRequest):
    tasks = [ask_persona(n, p, req.user_message) for n, p in PERSONAS.items()]
    replies = await asyncio.gather(*tasks)
    return {name: reply for name, reply in zip(PERSONAS.keys(), replies)}

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>✨ Astris Council</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: system-ui; max-width: 800px; margin: 20px auto; padding: 0 15px; }
            textarea { width: 100%; height: 80px; padding: 12px; margin: 10px 0; font-size: 16px; }
            button { background: #4F46E5; color: white; border: none; padding: 12px 24px; font-size: 16px; cursor: pointer; }
            button:disabled { background: #ccc; }
            .response { margin-top: 20px; padding: 15px; background: #f9fafb; border-radius: 8px; }
            .persona { margin: 15px 0; padding: 12px; border-left: 4px solid #4F46E5; }
            .persona h3 { margin: 0 0 8px 0; color: #3730A3; }
        </style>
    </head>
    <body>
        <h1>✨ Astris Council</h1>
        <p>Ask your question. Four experts will respond.</p>
        <textarea id="query" placeholder="e.g., I'm overwhelmed with work and money..."></textarea><br>
        <button onclick="ask()">Ask the Council</button>
        <div id="result"></div>

        <script>
        async function ask() {
            const input = document.getElementById("query");
            const btn = document.querySelector("button");
            const result = document.getElementById("result");
            const msg = input.value.trim();
            if (!msg) return;

            btn.disabled = true;
            btn.textContent = "Thinking...";
            result.innerHTML = "<p>Consulting the council...</p>";

            try {
                const res = await fetch("/council", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({user_message: msg})
                });
                const data = await res.json();
                let html = "";
                for (const [name, reply] of Object.entries(data)) {
                    html += `<div class="persona"><h3>${name}</h3><p>${reply.replace(/\n/g, '<br>')}</p></div>`;
                }
                result.innerHTML = '<div class="response">' + html + '</div>';
            } catch (e) {
                result.innerHTML = "<p style='color:red'>Error: " + e.message + "</p>";
            } finally {
                btn.disabled = false;
                btn.textContent = "Ask the Council";
            }
        }
        </script>
    </body>
    </html>
    """