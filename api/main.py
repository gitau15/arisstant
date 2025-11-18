from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import httpx
import os

app = FastAPI()

# === Single Persona: CEO ===
CEO_PROMPT = (
    "You are Avara, my close friend who’s a self-made tech CEO and millionaire. "
    "I’m a 4th-year CS student trying to walk the same path. "
    "Talk to me like a real friend: keep it short, direct, and human—like we’re texting or grabbing coffee. "
    "No long essays. No jargon. No fluff. "
    "If I say 'hi', just say hi back—don’t give a 10-paragraph life plan. "
    "Be brutally honest when needed, but always supportive. "
    "Ask quick follow-ups if you need clarity. "
    "And if I’m stuck, give ONE clear, actionable step—not a whole strategy doc."
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
            return {"error": f"Avara is unavailable: {str(e)}"}

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
        <title>Avara 😎</title>
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
            .input-area {
                background: white;
                padding: 20px;
                border-radius: 12px;
                box-shadow: 0 2px 6px rgba(30, 64, 175, 0.1);
                margin-bottom: 20px;
            }
            .input-group {
                margin: 12px 0;
            }
            label {
                display: block;
                margin-bottom: 5px;
                font-weight: 600;
                color: #3b82f6;
                font-size: 14px;
            }
            input, textarea {
                width: 100%;
                padding: 10px;
                border: 1px solid #93c5fd;
                border-radius: 6px;
                font-size: 15px;
            }
            textarea {
                height: 70px;
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
                margin: 15px auto 5px;
            }
            button:disabled {
                background: #60a5fa;
                cursor: not-allowed;
            }
            #history-toggle {
                background: #dbeafe;
                color: #1e40af;
                margin: 10px auto;
                display: block;
            }
            #chat-history {
                display: none;
                border: 1px solid #bfdbfe;
                padding: 15px;
                border-radius: 10px;
                background: white;
                margin-top: 10px;
            }
            .topic-header {
                margin-top: 18px;
                padding-top: 12px;
                border-top: 1px dashed #cbd5e1;
                color: #1d4ed8;
                font-weight: 700;
                font-size: 15px;
            }
            .message {
                margin: 8px 0;
                padding: 6px 0;
                line-height: 1.5;
                font-size: 14px;
            }
            .user { text-align: right; color: #1e40af; }
            .ceo {
                background: #eff6ff;
                padding: 8px;
                border-radius: 6px;
                border-left: 2px solid #3b82f6;
            }
            .loading {
                color: #1e40af;
                font-style: italic;
                text-align: center;
                padding: 8px;
            }
        </style>
    </head>
    <body>
        <h1>Avara 😎</h1>
        
        <div class="input-area">
            <div class="input-group">
                <label for="topic">Topic (e.g., Career, Money, Side Project)</label>
                <input type="text" id="topic" placeholder="General" value="General">
            </div>
            <div class="input-group">
                <label for="query">Your message</label>
                <textarea id="query" placeholder="Hey, quick question..."></textarea>
            </div>
            <button onclick="sendMessage()">Send</button>
            <button id="history-toggle" onclick="toggleHistory()">📁 View History</button>
        </div>

        <div id="chat-history"></div>

        <script>
        let chatHistory = JSON.parse(localStorage.getItem('ceoChat')) || false;

        function saveHistory() {
            localStorage.setItem('ceoChat', JSON.stringify(chatHistory));
        }

        function groupByTopic(messages) {
            const groups = {};
            messages.forEach(msg => {
                const t = msg.topic || 'General';
                if (!groups[t]) groups[t] = [];
                groups[t].push(msg);
            });
            return groups;
        }

        function renderHistory() {
            const div = document.getElementById('chat-history');
            if (!chatHistory || chatHistory.length === 0) {
                div.innerHTML = '<p style="text-align:center;color:#94a3b8">No past chats</p>';
                return;
            }
            const groups = groupByTopic(chatHistory);
            let html = '';
            for (const [topic, msgs] of Object.entries(groups)) {
                html += `<div class="topic-header">📌 ${topic}</div>`;
                msgs.forEach(msg => {
                    const sender = msg.role === 'user' ? 'You' : 'CEO';
                    const cls = msg.role === 'user' ? 'user' : 'ceo';
                    const content = msg.content.split('\\n').join('<br>');
                    html += `<div class="message ${cls}"><strong>${sender}:</strong> ${content}</div>`;
                });
            }
            div.innerHTML = html;
        }

        function toggleHistory() {
            const div = document.getElementById('chat-history');
            const btn = document.getElementById('history-toggle');
            if (div.style.display === 'block') {
                div.style.display = 'none';
                btn.textContent = '📁 View History';
            } else {
                renderHistory();
                div.style.display = 'block';
                btn.textContent = '⏫ Hide History';
            }
        }

        async function sendMessage() {
            const topic = document.getElementById('topic').value.trim() || 'General';
            const msg = document.getElementById('query').value.trim();
            if (!msg) return;

            // Init history if first time
            if (!Array.isArray(chatHistory)) chatHistory = [];

            // Add user message
            chatHistory.push({ role: 'user', content: msg, topic });
            saveHistory();

            // Reset input
            document.getElementById('query').value = '';
            document.querySelector('.input-area button').disabled = true;

            // Show loading in history (if open)
            if (document.getElementById('chat-history').style.display === 'block') {
                document.getElementById('chat-history').innerHTML += 
                    '<div class="message ceo loading">🤔💭</div>';
            }

            try {
                const res = await fetch('/advice', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_message: msg })
                });
                const data = await res.json();
                const reply = data.error ? `⚠️ ${data.error}` : data.ceo;

                chatHistory.push({ role: 'ceo', content: reply, topic });
                saveHistory();

                // Update history if visible
                if (document.getElementById('chat-history').style.display === 'block') {
                    renderHistory();
                }
            } catch (e) {
                if (document.getElementById('chat-history').style.display === 'block') {
                    const err = `<div class="message ceo"><strong>CEO:</strong> 🛑 ${e.message}</div>`;
                    document.getElementById('chat-history').innerHTML += err;
                }
            } finally {
                document.querySelector('.input-area button').disabled = false;
                document.getElementById('query').focus();
            }
        }

        document.getElementById('query').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        </script>
    </body>
    </html>
    """