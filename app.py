import os
import json
import requests
import threading
from flask import Flask, request
from openai import OpenAI

app = Flask(__name__)

# --- CONFIGURATION (Regenerate your keys if needed) ---
PAGE_ACCESS_TOKEN = "EAAMDopgTxP4BQXlMd51KpNEVMWDtY1ZAkvZAgL0vP9qn2uZAIJ6NU3UA5Uj0gEU6VbXZBrI6OxyC6TNcwV7Mgq1G8pOdCIw2kBgHMLG4NPpRFwURsnaNYIZBCLrZBneTJfmYQmBZAi5vZA7WGju2bVtRpw41mlh3uNnoF5MHYpz9O2VyNTxOrmt3JjqVMCET7vz6tP9bodsHrAZDZD"
WHATSAPP_TOKEN = "EAAMDopgTxP4BQGiv4cTvJloEiWdrduKChsu8bA1eQYGQsFLduIoKYcZA0q7GrlT0DzL8VZA0CP3ZAc3SCnQZCZCxRxTzCBTyHjWOfeI0oxs9mZAa1R3V4gQkiWzWTetF0ZBXrJsmwOonmKFiULi9fgfQBOJzxErLdcw4ZBZCsl3Ps9PMc0QJ4JKqY7nN47nzNBAs74c2IGcGaWwOftsCfZBTLToSlBt126qZCzBv2WZCgtGZBYZC2NCZB2mEPTiDDZCfPZAUCNZCILTfhCMfLItbThjxKngZBr0gYDW"
WHATSAPP_PHONE_ID = "875675892306352"
DEEPSEEK_API_KEY = "sk-f43fe0642f3f4337b4ea7235c9fe5b8e"
VERIFY_TOKEN = "mahi2004"

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

# --- 🧠 PERMANENT MEMORY SYSTEM ---
CHAT_DB_FILE = "chat_memory.json"
ORDER_DB_FILE = "order_status.json"

# Load Memory on Startup
if os.path.exists(CHAT_DB_FILE):
    with open(CHAT_DB_FILE, 'r', encoding='utf-8') as f:
        user_histories = json.load(f)
else:
    user_histories = {}

if os.path.exists(ORDER_DB_FILE):
    with open(ORDER_DB_FILE, 'r', encoding='utf-8') as f:
        completed_orders = json.load(f) # List of IDs who ordered
else:
    completed_orders = []

def save_memory():
    """Saves chat history to a file so we don't lose it on restart."""
    with open(CHAT_DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(user_histories, f, ensure_ascii=False, indent=2)

def save_order_status(user_id):
    """Marks a user as 'Ordered' forever."""
    if user_id not in completed_orders:
        completed_orders.append(user_id)
        with open(ORDER_DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(completed_orders, f, ensure_ascii=False, indent=2)

# --- AI PROMPTS ---

BASE_SYSTEM_PROMPT = """
SYSTEM / INSTRUCTIONS:
You are a professional sales assistant for **Hiamso**, a luxury fashion store in Algeria. Speak **ONLY** in Algerian Darja (Derja) mixed with arabic. Tone: friendly, classy, "Old Money" — polite, confident, unobtrusive. KEEP ALL REPLIES SHORT: **max 3 sentences**.

PRODUCT:
- Name: Ensemble Ralph Lauren (Old Money Style)
- Description: Navy Blue (Bleu Nuit), high-quality cotton, half-zip sweater + pants.
- Price: 6000 DA  ← (assistant must use the exact numeric price when asked)

DELIVERY (exact wilaya prices — use these values ONLY):
- Blida: 400 DA
- Alger: 500 DA
- Tipaza, Boumerdes: 750 DA
- Oran, Constantine, Annaba, Sétif, Béjaïa, Tlemcen, Skikda: 800 DA
- Chlef, Bouira, Médéa: 750 DA
- Adrar: 1400 DA
- Tamanrasset, In Salah: 1600 DA
- Ouargla, Biskra, El Oued, Ghardaia: 950 DA
- Béchar: 1100 DA
- Standard other Northern Wilayas: 800 DA
- Standard other Southern Wilayas: 1200 DA

RULES / BEHAVIOR:
1. Always answer in Algerian Darja mixed with arabic. No other languages.
2. If the customer asks about delivery cost, **return the exact price** from the list above for the wilaya they give (do not approximate).
3. Keep every reply ≤ 3 sentences and concise — no long paragraphs.
4. Use polite sales phrasing (e.g. "s’il vous plaît", "parfait", "d’accord"), but maintain classy Old-Money vibe.
5. If asked for the product price, reply with the product price **exact number + 'DA'**.
6. If the customer asks size, stock, or color questions, answer briefly and honestly.
7. When the customer confirms order and gives required info (name, phone, wilaya, address), output **ONLY** the final JSON object below — nothing else.
8. ask the customer for his name and phone number and wilaya and full address if missing.
9. dont make sexe difference when talking talk like you dont know the sexe of the customer.
ORDER COMPLETE OUTPUT (exact JSON format):
When order is complete, reply with **only** this JSON (replace values with customer data):
{"ORDER_COMPLETE": true, "name": "FULL NAME", "phone": "PHONE_NUMBER", "wilaya": "WILAYA_NAME", "address": "FULL_ADDRESS", "product": "Ensemble Ralph Lauren", "price_DA": NUMBER}

ERROR / MISSING INFO:
- If any required order field is missing, ask **one** concise question requesting that single missing item (still ≤ 3 sentences).

Customer confirms with details:
Assistant (only JSON):
{"ORDER_COMPLETE": true, "name": "...", "phone": "...", "wilaya": "...", "address": "...", "product": "...", "price_DA": "..."}
"""

# --- CORE FUNCTIONS ---

def save_order_to_sheet(order_data, user_id):
    try:
        # 1. Send to Google Sheets
        requests.post(SCRIPT_URL, json=order_data)
        
        # 2. Mark user as 'Ordered' in our local database
        save_order_status(user_id) 
        return True
    except Exception as e:
        print(f"❌ Sheet Error: {e}")
        return False

def get_ai_response(user_id, user_message):
    # 1. Initialize User Memory if new
    if user_id not in user_histories:
        user_histories[user_id] = []
    
    # 2. Check if this is an "Old Client" (VIP Check)
    dynamic_prompt = BASE_SYSTEM_PROMPT
    if user_id in completed_orders:
        dynamic_prompt += "\n\n[NOTE: This user has ALREADY ordered from us before. Welcome them back warmly. Ask if they liked the previous product.]"
    
    # 3. Build Messages (System + History + New)
    messages = [{"role": "system", "content": dynamic_prompt}] + user_histories[user_id][-10:] # Keep last 10 msgs context
    messages.append({"role": "user", "content": user_message})

    try:
        # 4. Call DeepSeek
        response = client.chat.completions.create(
            model="deepseek-chat", 
            messages=messages, 
            temperature=0.3
        )
        ai_reply = response.choices[0].message.content
        
        # 5. Save to Memory
        user_histories[user_id].append({"role": "user", "content": user_message})
        user_histories[user_id].append({"role": "assistant", "content": ai_reply})
        save_memory() # <--- SAVES TO FILE IMMEDIATELY

        return ai_reply
    except Exception as e:
        print(f"❌ AI Error: {e}")
        return "Semhili, kayen mochkil sghir fel reseau."

# --- PROCESSOR ---

def process_message(user_id, user_text, platform):
    print(f"📩 [{platform}] {user_id}: {user_text}")
    
    # Get Reply
    ai_text = get_ai_response(user_id, user_text)
    
    # Check JSON
    clean_text = ai_text
    if "ORDER_COMPLETE" in ai_text:
        try:
            start = ai_text.find('{')
            end = ai_text.rfind('}') + 1
            json_str = ai_text[start:end]
            order_data = json.loads(json_str)
            
            # Save to Sheet AND Local Memory
            if save_order_to_sheet(order_data, user_id):
                clean_text = "Bsahtek! Commande ta3ek tsajlet (Saved). N'3aytoulak 9rib."
            else:
                clean_text = "Order received but sheet error."
                
        except Exception as e:
            print(f"JSON Error: {e}")

    # Send Reply
    if platform == "whatsapp":
        send_whatsapp_message(user_id, clean_text)
    else:
        send_facebook_message(user_id, clean_text)

# --- SENDING FUNCTIONS ---
# (Paste your send_facebook_message and send_whatsapp_message functions here)
# ... [Keep your previous sending code unchanged] ...

def send_facebook_message(recipient_id, text):
    # ... [PASTE YOUR PREVIOUS CODE HERE] ...
    params = {"access_token": PAGE_ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}
    data = json.dumps({"recipient": {"id": recipient_id}, "message": {"text": text}})
    requests.post("https://graph.facebook.com/v18.0/me/messages", params=params, headers=headers, data=data)

def send_whatsapp_message(recipient_phone, text):
    # ... [PASTE YOUR PREVIOUS CODE HERE] ...
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    data = json.dumps({"messaging_product": "whatsapp", "to": recipient_phone, "text": {"body": text}})
    requests.post(f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_ID}/messages", headers=headers, data=data)

# --- FLASK SERVER ---
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge"), 200
        return "Verification failed", 403

    data = request.get_json()
    
    # WHATSAPP
    if data.get('object') == 'whatsapp_business_account':
        try:
            for entry in data['entry']:
                for change in entry['changes']:
                    if change['value'].get('messages'):
                        msg = change['value']['messages'][0]
                        threading.Thread(target=process_message, args=(msg['from'], msg['text']['body'], "whatsapp")).start()
        except: pass

    # FACEBOOK/INSTAGRAM
    elif data.get('object') in ['page', 'instagram']:
        try:
            for entry in data['entry']:
                for event in entry.get('messaging', []):
                    if 'message' in event and 'text' in event['message'] and not event['message'].get('is_echo'):
                        threading.Thread(target=process_message, args=(event['sender']['id'], event['message']['text'], "facebook")).start()
        except: pass

    return "ok", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
