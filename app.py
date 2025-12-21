import os
import json
import requests
import threading
from flask import Flask, request
from openai import OpenAI

app = Flask(__name__)

# --- CONFIGURATION ---
# 🔴 IMPORTANT: Regenerate your keys and paste them here.
# Do NOT use the keys you posted online, they are not safe anymore.

# 1. FACEBOOK & INSTAGRAM (From App A)
PAGE_ACCESS_TOKEN = "EAAMCt1EzGVEBQcULVIDkZCT1BYGVG2JfQmEpMu4IGHcx6hsyzgz1C1h7yNwZAfMQb4aONwSdS0IZCvZBB4ZCaKpZBrOtw8kRwUmIv2ZAQXXG1Yzlor13nnkSxdQuFkwGcRrRDOoefYtliKvZCCmLvCYAf5muggJkOQi93apXQrGUvMPnkOqbgA5fhokIBskKIfGUlRpvDmM5ZAWr4Hqpuk7sVydZAfj4mQkIh86xgmyedNfPjqi6wBsiv5Msh7MBhL4daZBXpAUMYsZAih9GrPZCDKZCcwJxmKHQZDZD"

# 2. WHATSAPP (From App B)
WHATSAPP_TOKEN = "EAAMDopgTxP4BQGiv4cTvJloEiWdrduKChsu8bA1eQYGQsFLduIoKYcZA0q7GrlT0DzL8VZA0CP3ZAc3SCnQZCZCxRxTzCBTyHjWOfeI0oxs9mZAa1R3V4gQkiWzWTetF0ZBXrJsmwOonmKFiULi9fgfQBOJzxErLdcw4ZBZCsl3Ps9PMc0QJ4JKqY7nN47nzNBAs74c2IGcGaWwOftsCfZBTLToSlBt126qZCzBv2WZCgtGZBYZC2NCZB2mEPTiDDZCfPZAUCNZCILTfhCMfLItbThjxKngZBr0gYDW"
WHATSAPP_PHONE_ID = "875675892306352"

# 3. AI & SYSTEM
DEEPSEEK_API_KEY = "sk-f43fe0642f3f4337b4ea7235c9fe5b8e"
VERIFY_TOKEN = "mahi2004"

# --- GOOGLE SHEETS ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbypBK1c1T4lW74Jy92SMU-vEL0TNY_ZyZH1f74DdmRCeXnKIgLxwoJn6PxNE7soNQZi/exec"

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
user_histories = {}

SYSTEM_PROMPT = """
You are a sales assistant for 'Hiamso Algérie'.
Goal: Sell products and get: Name, Phone, Address.
Keep answers short (under 50 words).
WHEN ORDER COMPLETE, OUTPUT ONLY JSON: {"ORDER_COMPLETE": true, "name": "...", "phone": "...", "address": "...", "product": "..."}
"""

# --- HELPER FUNCTIONS ---

def save_order_to_sheet(order_data):
    try:
        requests.post(SCRIPT_URL, json=order_data)
        return True
    except Exception as e:
        print(f"❌ Sheet Error: {e}")
        return False

def get_ai_response(user_id, user_message):
    if user_id not in user_histories:
        user_histories[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    user_histories[user_id].append({"role": "user", "content": user_message})
    
    # Keep memory short (Last 10 messages)
    if len(user_histories[user_id]) > 12:
        user_histories[user_id] = [user_histories[user_id][0]] + user_histories[user_id][-10:]

    try:
        response = client.chat.completions.create(
            model="deepseek-chat", 
            messages=user_histories[user_id], 
            temperature=0.3
        )
        ai_reply = response.choices[0].message.content
        user_histories[user_id].append({"role": "assistant", "content": ai_reply})
        return ai_reply
    except Exception as e:
        print(f"❌ AI Error: {e}")
        return "System error. Please try again later."

# --- SENDING FUNCTIONS (DEBUG VERSION) ---

def send_facebook_message(recipient_id, text):
    print(f"🚀 Sending FB message to {recipient_id}...")
    
    params = {"access_token": PAGE_ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}
    data = json.dumps({
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    })
    
    try:
        r = requests.post("https://graph.facebook.com/v18.0/me/messages", params=params, headers=headers, data=data)
        if r.status_code == 200:
            print("✅ FB Message SENT!")
        else:
            print(f"❌ FB SEND ERROR {r.status_code}: {r.text}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

def send_whatsapp_message(recipient_phone, text):
    print(f"🚀 Sending WhatsApp message to {recipient_phone}...")
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "messaging_product": "whatsapp",
        "to": recipient_phone,
        "text": {"body": text}
    })
    
    try:
        r = requests.post(f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_ID}/messages", headers=headers, data=data)
        if r.status_code == 200:
            print("✅ WhatsApp Message SENT!")
        else:
            print(f"❌ WHATSAPP SEND ERROR {r.status_code}: {r.text}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

# --- PROCESSOR (RUNS IN BACKGROUND) ---

def process_message(user_id, user_text, platform):
    print(f"📩 [{platform}] Msg from {user_id}: {user_text}")
    
    # 1. Get AI Reply
    print("🤖 Waiting for AI response...")
    ai_text = get_ai_response(user_id, user_text)
    print(f"💡 AI Says: {ai_text[:30]}...") # Print preview
    
    # 2. Check for Order
    clean_text = ai_text
    if "ORDER_COMPLETE" in ai_text:
        try:
            print("📝 Processing Order JSON...")
            start = ai_text.find('{')
            end = ai_text.rfind('}') + 1
            json_str = ai_text[start:end]
            order_data = json.loads(json_str)
            
            if save_order_to_sheet(order_data):
                clean_text = "✅ Order Confirmed! We will call you soon."
            else:
                clean_text = "Order received (System Note: Sheet Error)."
                
        except Exception as e:
            print(f"⚠️ JSON Parse Error: {e}")

    # 3. Send Reply
    if platform == "whatsapp":
        send_whatsapp_message(user_id, clean_text)
    else:
        send_facebook_message(user_id, clean_text)

# --- WEBHOOK ROUTES ---

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge"), 200
    return "Verification failed", 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    
    # 🟢 1. DETECT WHATSAPP
    if data.get('object') == 'whatsapp_business_account':
        try:
            for entry in data['entry']:
                for change in entry['changes']:
                    if change['value'].get('messages'):
                        msg = change['value']['messages'][0]
                        sender_phone = msg['from']
                        text = msg['text']['body']
                        
                        # Run in background
                        threading.Thread(target=process_message, args=(sender_phone, text, "whatsapp")).start()
        except Exception as e:
            print(f"❌ WhatsApp Hook Error: {e}")

    # 🔵 2. DETECT FACEBOOK / INSTAGRAM
    elif data.get('object') == 'page' or data.get('object') == 'instagram':
        for entry in data['entry']:
            for event in entry.get('messaging', []):
                # Skip echoes
                if event.get('message', {}).get('is_echo'): continue
                
                if 'message' in event and 'text' in event['message']:
                    sender_id = event['sender']['id']
                    text = event['message']['text']
                    
                    # Run in background
                    threading.Thread(target=process_message, args=(sender_id, text, "facebook")).start()

    return "ok", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
# NEW:




