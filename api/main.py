from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import httpx
import os

app = FastAPI()

# === Single Persona: CEO ===
CEO_PROMPT = (
    "You are a visionary startup CEO in tech with a million-dollar business. "
    "You provide high-level, brutally honest, fact-based guidance to a 4th-year CS student who wants to become like you. "
    "You give structured, actionable plans for career, decisions, and personal growth. "
    "You also act as a financial literacy coach—teaching how to generate, manage, and grow money to become a millionaire. "
    "Explain everything clearly, simply, and without jargon. Be direct, pragmatic, and encouraging—but never fluff."
)

class QueryRequest(BaseModel):
    user_message: str

@app.post("/advice")
async def get_ceo_advice(req: QueryRequest):
    payload = {
        "model": "glm-4",
        "messages": [
            {"role": "system", "content": CEO_PROMPT},
            {"role": "user", "content": req.user_message}
        ],
        "temperature": 0.7,
        "max_tokens": 800
    }
    headers = {
        "Authorization": f"Bearer {os.getenv('GLM_API_KEY')}",
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                "https://open.bigmodel.cn/api/paas/v4/chat/completions",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            reply = data["choices"][0]["message"]["content"].strip()
            return {"ceo": reply}
        except Exception as e:
            return {"error": f"CEO is unavailable: {str(e)}"}

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
        <title>🚀 CEO Advisor</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                max-width: 700px;
                margin: 30px auto;
                padding: 0 15px;
                background: #fffaf7;
                color: #1c1917;
            }
            h1 { color: #9a3412; }
            textarea {
                width: 100%;
                height: 100px;
                padding: 14px;
                margin: 12px 0;
                border: 1px solid #d6d3d1;
                border-radius: 10px;
                font-size: 16px;
                resize: vertical;
            }
            button {
                background: #ea580c;
                color: white;
                border: none;
                padding: 14px 28px;
                font-size: 17px;
                border-radius: 8px;
                cursor: pointer;
            }
            button:disabled {
                background: #f97316;
                cursor: not-allowed;
            }
            .response {
                margin-top: 25px;
                padding: 20px;
                background: white;
                border-radius: 12px;
                border-left: 4px solid #f97316;
                box-shadow: 0 2px 6px rgba(0,0,0,0.05);
            }
            .loading {
                color: #c2410c;
                font-style: italic;
            }
        </style>
    </head>
    <body>
        <h1>🚀 CEO Advisor</h1>
        <p>Ask your question. Get direct, actionable advice from a self-made tech CEO.</p>
        <textarea id="query" placeholder="e.g., How do I turn my side project into income as a CS student?"></textarea><br>
        <button onclick="ask()">Get CEO Advice</button>
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
            result.innerHTML = '<p class="loading">CEO is crafting your strategy...</p>';

            try {
                const res = await fetch("/advice", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ user_message: msg })
                });
                const data = await res.json();
                if (data.error) {
                    result.innerHTML = `<p style="color:#dc2626">Error: ${data.error}</p>`;
                } else {
                    const reply = data.ceo.replace(/\n/g, "<br>");
                    result.innerHTML = `<div class="response"><strong>CEO says:</strong><br><br>${reply}</div>`;
                }
            } catch (e) {
                result.innerHTML = `<p style="color:#dc2626">Network error: ${e.message}</p>`;
            } finally {
                btn.disabled = false;
                btn.textContent = "Get CEO Advice";
            }
        }
        </script>
    </body>
    </html>
    """