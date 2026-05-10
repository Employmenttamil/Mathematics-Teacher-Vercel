import os
import json
import requests
from http.server import BaseHTTPRequestHandler

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

SYSTEM_PROMPT = """You are a professional mathematics teacher (கணித ஆசிரியர்) who helps students solve math problems.

Rules:
1. ONLY respond to math-related questions or math screenshots. If the message is NOT about math, respond with exactly: "SKIP"
2. Use Tamil language for explanations
3. Use shortcut methods whenever possible
4. Use relevant emojis in your response
5. Keep solutions clear and step-by-step
6. Be encouraging and friendly

Format your response like this:
- Start with a greeting using 🙏
- Show the shortcut method step by step
- End with the final answer clearly marked
- Always be helpful and professional"""


def is_math_related(text):
    """Quick check if message might be math-related"""
    if not text:
        return False
    math_indicators = [
        '+', '-', '*', '/', '=', '%', '^',
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
        'math', 'calculate', 'solve', 'sum', 'add', 'subtract',
        'multiply', 'divide', 'root', 'square', 'percentage',
        'area', 'volume', 'angle', 'triangle', 'circle',
        'equation', 'formula', 'average', 'mean', 'median',
        'கணக்கு', 'கூட்டல்', 'கழித்தல்', 'பெருக்கல்', 'வகுத்தல்',
        'சதவீதம்', 'பரப்பளவு', 'சராசரி', 'விடை', 'கணித',
        'x', 'X', '×', '÷', '√', 'π',
    ]
    return any(indicator in text for indicator in math_indicators)


def call_groq(messages):
    """Call Groq API for text-based math solving"""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 1500
    }
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=9
    )
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    return None


def call_groq_vision(image_url, caption=""):
    """Call Groq API with vision model for image-based math"""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    user_content = [
        {
            "type": "image_url",
            "image_url": {"url": image_url}
        }
    ]
    if caption:
        user_content.insert(0, {"type": "text", "text": caption})
    else:
        user_content.insert(0, {"type": "text", "text": "Solve this math problem from the image."})

    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.3,
        "max_tokens": 1500
    }
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=9
    )
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    return None


def get_file_url(file_id):
    """Get Telegram file URL"""
    resp = requests.get(f"{TELEGRAM_API}/getFile?file_id={file_id}", timeout=5)
    if resp.status_code == 200:
        file_path = resp.json()["result"]["file_path"]
        return f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
    return None


def send_message(chat_id, text, reply_to_message_id=None):
    """Send message to Telegram"""
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id
    requests.post(f"{TELEGRAM_API}/sendMessage", json=payload, timeout=5)


def process_message(update):
    """Process incoming Telegram message"""
    message = update.get("message")
    if not message:
        return

    chat_id = message["chat"]["id"]
    message_id = message["message_id"]

    # Get user info for tagging
    user = message.get("from", {})
    first_name = user.get("first_name", "")
    username = user.get("username", "")

    if username:
        user_tag = f'<a href="tg://user?id={user.get("id", "")}">{first_name}</a>'
    else:
        user_tag = f'<a href="tg://user?id={user.get("id", "")}">{first_name}</a>'

    # Check if it's a photo/image
    photo = message.get("photo")
    document = message.get("document")
    text = message.get("text", "") or message.get("caption", "")

    response = None

    if photo:
        # Get the largest photo
        file_id = photo[-1]["file_id"]
        file_url = get_file_url(file_id)
        if file_url:
            response = call_groq_vision(file_url, text)
    elif document and document.get("mime_type", "").startswith("image/"):
        file_id = document["file_id"]
        file_url = get_file_url(file_id)
        if file_url:
            response = call_groq_vision(file_url, text)
    elif text:
        # Check if it's math-related
        if not is_math_related(text):
            return  # Stay silent for non-math messages

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ]
        response = call_groq(messages)
    else:
        return

    if response and response.strip() != "SKIP" and "SKIP" not in response[:10]:
        # Add shop link at the end
        shop_link = '\n\n🛒 <a href="https://employmenttamil.in/shop/">விற்பனை நிலையம்</a>'
        final_response = f"{user_tag}\n\n{response}{shop_link}"
        send_message(chat_id, final_response, reply_to_message_id=message_id)


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        try:
            update = json.loads(body)
            process_message(update)
        except Exception as e:
            print(f"Error: {e}")

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}).encode())

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "Math Teacher Bot is running!"}).encode())
