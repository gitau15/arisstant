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
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                max-width: 700px;
                margin: 20px auto;
                padding: 0 15px;
                background: #f0f9ff;
                color: #1e40af;
            }
            h1 { 
                color: #1d4ed8; 
                text-align: center;
                margin-bottom: 10px;
            }
            #chat { 
                height: 400px; 
                overflow-y: auto; 
                border: 1px solid #bfdbfe; 
                padding: 15px; 
                margin: 15px 0; 
                border-radius: 10px; 
                background: white;
            }
            .message { margin-bottom: 15px; line-height: 1.5; }
            .user { text-align: right; color: #1e40af; }
            .ceo { 
                text-align: left; 
                background: #eff6ff; 
                padding: 10px; 
                border-radius: 8px; 
                border-left: 3px solid #3b82f6;
            }
            textarea {
                width: 100%;
                height: 80px;
                padding: 12px;
                margin: 10px 0;
                border: 1px solid #93c5fd;
                border-radius: 8px;
                font-size: 16px;
                resize: vertical;
            }
            button {
                background: #2563eb;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 16px;
                border-radius: 6px;
                cursor: pointer;
                display: block;
                margin: 0 auto;
            }
            button:disabled {
                background: #60a5fa;
                cursor: not-allowed;
            }
            .loading {
                color: #1e40af;
                font-style: italic;
                text-align: center;
                padding: 10px;
            }
        </style>
    </head>
    <body>
        <h1>🚀 CEO Advisor</h1>
        <div id="chat"></div>
        <textarea id="query" placeholder="Ask your question..."></textarea>
        <button onclick="sendMessage()">Send</button>

        <script>
        // Load chat history from localStorage
        let chatHistory = JSON.parse(localStorage.getItem('ceoChat')) || [];

        function renderChat() {
            const chatDiv = document.getElementById('chat');
            chatDiv.innerHTML = '';
            chatHistory.forEach(msg => {
                const div = document.createElement('div');
                div.className = 'message ' + (msg.role === 'user' ? 'user' : 'ceo');
                div.innerHTML = `<strong>${msg.role === 'user' ? 'You' : 'CEO'}:</strong> ${msg.content.replace(/\n/g, '<br>')}`;
                chatDiv.appendChild(div);
            });
            chatDiv.scrollTop = chatDiv.scrollHeight;
        }

        async function sendMessage() {
            const input = document.getElementById('query');
            const msg = input.value.trim();
            if (!msg) return;

            // Add user message
            chatHistory.push({ role: 'user', content: msg });
            renderChat();
            input.value = '';
            input.disabled = true;
            document.querySelector('button').disabled = true;

            // Show loading
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'message ceo loading';
            loadingDiv.textContent = 'CEO is thinking...';
            document.getElementById('chat').appendChild(loadingDiv);
            document.getElementById('chat').scrollTop = document.getElementById('chat').scrollHeight;

            try {
                // Prepare full message history for GLM (system + chat)
                const payload = {
                    user_message: msg,
                    history: chatHistory.slice(0, -1) // exclude current user msg
                };

                const response = await fetch('/advice', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_message: msg })
                });

                const data = await response.json();
                const ceoReply = data.error ? `⚠️ Error: ${data.error}` : data.ceo;

                // Remove loading
                document.getElementById('chat').removeChild(loadingDiv);

                // Add CEO reply
                chatHistory.push({ role: 'ceo', content: ceoReply });
                localStorage.setItem('ceoChat', JSON.stringify(chatHistory));
                renderChat();

            } catch (e) {
                // Remove loading
                document.getElementById('chat').removeChild(loadingDiv);
                const errDiv = document.createElement('div');
                errDiv.className = 'message ceo';
                errDiv.innerHTML = `<strong>CEO:</strong> 🛑 Network error: ${e.message}`;
                document.getElementById('chat').appendChild(errDiv);
            } finally {
                input.disabled = false;
                document.querySelector('button').disabled = false;
                input.focus();
            }
        }

        // Allow Enter key to send (Shift+Enter for newline)
        document.getElementById('query').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        // Initial render
        renderChat();
        </script>
    </body>
    </html>
    """