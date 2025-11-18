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
            .input-group {
                margin: 10px 0;
            }
            label {
                display: block;
                margin-bottom: 4px;
                font-weight: 600;
                color: #3b82f6;
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
                margin: 15px auto 10px;
            }
            button:disabled {
                background: #60a5fa;
                cursor: not-allowed;
            }
            #chat {
                border: 1px solid #bfdbfe;
                padding: 15px;
                margin: 15px 0;
                border-radius: 10px;
                background: white;
                min-height: 300px;
            }
            .topic-header {
                margin-top: 20px;
                padding-top: 15px;
                border-top: 2px solid #dbeafe;
                color: #1d4ed8;
                font-weight: 700;
            }
            .message {
                margin: 10px 0;
                padding: 8px 0;
                line-height: 1.5;
            }
            .user { text-align: right; color: #1e40af; font-weight: 500; }
            .ceo {
                background: #eff6ff;
                padding: 10px;
                border-radius: 8px;
                border-left: 3px solid #3b82f6;
            }
            .loading {
                color: #1e40af;
                font-style: italic;
            }
        </style>
    </head>
    <body>
        <h1>Avara 😎</h1>
        <div class="input-group">
            <label for="topic">Topic (e.g., Career, Finances, Side Project)</label>
            <input type="text" id="topic" placeholder="Choose a topic for this chat" value="General">
        </div>
        <div class="input-group">
            <label for="query">Your message</label>
            <textarea id="query" placeholder="Hey, I need advice about..."></textarea>
        </div>
        <button onclick="sendMessage()">Send</button>
        <div id="chat"></div>

        <script>
        let chatHistory = JSON.parse(localStorage.getItem('ceoChat')) || [];

        function groupByTopic(messages) {
            const groups = {};
            messages.forEach(msg => {
                const t = msg.topic || 'General';
                if (!groups[t]) groups[t] = [];
                groups[t].push(msg);
            });
            return groups;
        }

        function renderChat() {
            const chatDiv = document.getElementById('chat');
            const groups = groupByTopic(chatHistory);
            chatDiv.innerHTML = '';

            for (const [topic, msgs] of Object.entries(groups)) {
                const topicEl = document.createElement('div');
                topicEl.className = 'topic-header';
                topicEl.textContent = `📌 ${topic}`;
                chatDiv.appendChild(topicEl);

                msgs.forEach(msg => {
                    const msgEl = document.createElement('div');
                    msgEl.className = 'message ' + (msg.role === 'user' ? 'user' : 'ceo');
                    const sender = msg.role === 'user' ? 'You' : 'CEO';
                    msgEl.innerHTML = `<strong>${sender}:</strong> ${msg.content.split('\\n').join('<br>')}`;
                    chatDiv.appendChild(msgEl);
                });
            }
            chatDiv.scrollTop = chatDiv.scrollHeight;
        }

        async function sendMessage() {
            const topicInput = document.getElementById('topic');
            const queryInput = document.getElementById('query');
            const topic = topicInput.value.trim() || 'General';
            const message = queryInput.value.trim();
            if (!message) return;

            // Add user message with topic
            chatHistory.push({ role: 'user', content: message, topic });
            renderChat();
            queryInput.value = '';
            queryInput.disabled = true;
            topicInput.disabled = true;
            document.querySelector('button').disabled = true;

            // Loading indicator
            const loadingEl = document.createElement('div');
            loadingEl.className = 'message ceo loading';
            loadingEl.textContent = '🤔💭';
            document.getElementById('chat').appendChild(loadingEl);

            try {
                const res = await fetch('/advice', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_message: message })
                });
                const data = await res.json();
                const reply = data.error ? `⚠️ ${data.error}` : data.ceo;

                // Add CEO reply with same topic
                chatHistory.push({ role: 'ceo', content: reply, topic });
                localStorage.setItem('ceoChat', JSON.stringify(chatHistory));
                renderChat();

            } catch (e) {
                const errEl = document.createElement('div');
                errEl.className = 'message ceo';
                errEl.innerHTML = `<strong>Avara:</strong> 🛑 Network error: ${e.message}`;
                document.getElementById('chat').replaceChild(errEl, loadingEl);
            } finally {
                queryInput.disabled = false;
                topicInput.disabled = false;
                document.querySelector('button').disabled = false;
                queryInput.focus();
            }
        }

        document.getElementById('query').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        renderChat();
        </script>
    </body>
    </html>
    """