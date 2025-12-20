# import os
# import json
# import requests
# from flask import Flask, request
# from openai import OpenAI
# import gspread
# from oauth2client.service_account import ServiceAccountCredentials

# app = Flask(__name__)

# # --- CONFIGURATION ---
# # DeepSeek Config (OpenAI Compatible)
# DEEPSEEK_API_KEY = "sk-f43fe0642f3f4337b4ea7235c9fe5b8e"
# client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

# # Meta (Facebook/Instagram) Config
# PAGE_ACCESS_TOKEN = "EAAMCt1EzGVEBQFmFD14sZBeOekgDPpBVU9EIaifXAeicXr6TdLV66kL4cnTYyjrGeAmsrph3XI6Jrnb4bAI5RZCrZASlv3TQ2YXb489thbZAgHxbwCFwzT3sZBrmNuES4wSv1SpKeyWf5ikNZBkB0TpOGIcKhZBjIWmNE3USyZAy3ZANy8JZAPEDWoSRuB11ZAAKgGZBYiQLnO2bslG5R1vpL5ZCGkeJkYwZDZD"
# VERIFY_TOKEN = "mahi2004"  # You choose this, used for webhook verification

# # Google Sheets Config
# SHEET_NAME = "Orders_Sheet" # Create this sheet in your Google Drive
# CREDENTIALS_FILE = "credentials.json" # Download this from Google Cloud

# # --- PRODUCT KNOWLEDGE BASE ---
# # This is how the AI "knows" the difference between your products.
# SYSTEM_PROMPT = """
# You are a smart sales bot for 'MyEcomStore'.
# Products:
# 1. "UltraWatch 2" - $50 (Waterproof, 7-day battery).
# 2. "SlimWallet X" - $30 (Leather, RFID).

# RULES:
# 1. Be short and direct.
# 2. If the user wants to buy, ask for these 3 things one by one or together: Name, Phone, Address.
# 3. CRITICAL: As soon as you have Name, Phone, AND Address, do NOT ask "Do you want to confirm?".
# 4. Instead, IMMEDIATELY output this JSON block at the end of your message:
#    ```json
#    {"ORDER_CONFIRMED": true, "product": "product_name", "customer_name": "the_name", "phone": "the_phone", "address": "the_address"}
# """

# # --- GOOGLE SHEETS FUNCTION ---
# def save_to_sheet(order_data):
#     try:
#         scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
#         creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
#         client_gs = gspread.authorize(creds)
#         sheet = client_gs.open(SHEET_NAME).sheet1
        
#         # Append row: [Product, Name, Phone, Address, Status]
#         row = [
#             order_data.get("product"),
#             order_data.get("customer_name"),
#             order_data.get("phone"),
#             order_data.get("address"),
#             "New Order"
#         ]
#         sheet.append_row(row)
#         return True
#     except Exception as e:
#         print(f"Sheet Error: {e}")
#         return False

# # --- DEEPSEEK AI FUNCTION ---
# def get_ai_response(user_message):
#     try:
#         response = client.chat.completions.create(
#             model="deepseek-chat",
#             messages=[
#                 {"role": "system", "content": SYSTEM_PROMPT},
#                 {"role": "user", "content": user_message},
#             ],
#             temperature=0.7
#         )
#         return response.choices[0].message.content
#     except Exception as e:
#         print(f"AI Error: {e}")
#         return "Sorry, I am having trouble connecting right now."

# # --- META WEBHOOK ROUTES ---
# @app.route('/webhook', methods=['GET'])
# def verify():
#     """Verifies the webhook for Facebook/Instagram"""
#     if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
#         if request.args.get("hub.verify_token") == VERIFY_TOKEN:
#             return request.args.get("hub.challenge"), 200
#         return "Verification token mismatch", 403
#     return "Hello world", 200

# @app.route('/webhook', methods=['POST'])
# def webhook():
#     data = request.get_json()
    
#     if data['object'] == 'page':
#         for entry in data['entry']:
#             for messaging_event in entry['messaging']:
#                 if 'message' in messaging_event and 'text' in messaging_event['message']:
#                     sender_id = messaging_event['sender']['id']
#                     user_text = messaging_event['message']['text']
                    
#                     # 1. Get AI Response
#                     ai_reply = get_ai_response(user_text)
                    
#                     # 2. Check for Hidden Order JSON
#                     clean_reply = ai_reply
#                     if '{"ORDER_CONFIRMED": true' in ai_reply:
#                         # Extract JSON
#                         try:
#                             json_str = ai_reply[ai_reply.find('{'):ai_reply.rfind('}')+1]
#                             order_data = json.loads(json_str)
                            
#                             # Save to Google Sheet
#                             save_to_sheet(order_data)
                            
#                             # Remove JSON from the reply sent to user
#                             clean_reply = ai_reply.replace(json_str, "").strip()
#                             clean_reply += "\n\n(System: Order saved successfully! ✅)"
#                         except:
#                             pass

#                     # 3. Send Reply to User
#                     send_message(sender_id, clean_reply)
                    
#         return "ok", 200
#     return "ok", 200

# def send_message(recipient_id, text):
#     """Sends a message back to the user via Facebook Graph API"""
#     params = {"access_token": PAGE_ACCESS_TOKEN}
#     headers = {"Content-Type": "application/json"}
#     data = json.dumps({
#         "recipient": {"id": recipient_id},
#         "message": {"text": text}
#     })
#     r = requests.post("https://graph.facebook.com/v18.0/me/messages", params=params, headers=headers, data=data)

# if __name__ == '__main__':
#     app.run(port=5000, debug=True)

import os
import json
import requests
from flask import Flask, request
from openai import OpenAI
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# --- CONFIGURATION ---
DEEPSEEK_API_KEY = "sk-f43fe0642f3f4337b4ea7235c9fe5b8e" # 🔴 PASTE KEY HERE
PAGE_ACCESS_TOKEN = "EAAMCt1EzGVEBQFmFD14sZBeOekgDPpBVU9EIaifXAeicXr6TdLV66kL4cnTYyjrGeAmsrph3XI6Jrnb4bAI5RZCrZASlv3TQ2YXb489thbZAgHxbwCFwzT3sZBrmNuES4wSv1SpKeyWf5ikNZBkB0TpOGIcKhZBjIWmNE3USyZAy3ZANy8JZAPEDWoSRuB11ZAAKgGZBYiQLnO2bslG5R1vpL5ZCGkeJkYwZDZD" # 🔴 PASTE TOKEN HERE
VERIFY_TOKEN = "mahi2004"

# --- GOOGLE SHEETS SETUP ---
SHEET_NAME = "Orders_Sheet"

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

# --- MEMORY STORAGE ---
# This dictionary will hold the chat history: { 'user_id': [message1, message2...] }
user_histories = {}
SYSTEM_PROMPT = """
You are a sales bot for 'Hiamso Algérie'.
Goal: Sell products and get these 3 details: Name, Phone, Address.

CRITICAL RULES:
1. Do not stop asking until you have Name, Phone, AND Address.
2. WHEN YOU HAVE ALL 3:
   - DO NOT say "Thank you" or "Order complete".
   - DO NOT generate a summary text.
   - ONLY output this exact JSON string:
   {"ORDER_COMPLETE": true, "name": "...", "phone": "...", "address": "...", "product": "..."}
"""
# --- GOOGLE SHEETS FUNCTION ---
# Replace this with the URL you copied in Step 2
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbypBK1c1T4lW74Jy92SMU-vEL0TNY_ZyZH1f74DdmRCeXnKIgLxwoJn6PxNE7soNQZi/exec"

def save_order_to_sheet(order_data):
    try:
        # Prepare the data for the Apps Script
        payload = {
            "name": order_data.get("name"),
            "phone": order_data.get("phone"),
            "address": order_data.get("address"),
            "product": order_data.get("product")
        }
        
        # Send a POST request to the Apps Script URL
        response = requests.post(SCRIPT_URL, json=payload)
        
        if response.status_code == 200:
            print("✅ Order Saved via Apps Script!")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False

# --- AI RESPONSE WITH MEMORY ---
def get_ai_response(user_id, user_message):
    # 1. Create history if this is a new user
    if user_id not in user_histories:
        user_histories[user_id] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
    
    # 2. Add the user's new message to history
    user_histories[user_id].append({"role": "user", "content": user_message})
    
    # 3. Keep history short (last 10 messages) to save money/speed
    if len(user_histories[user_id]) > 12:
        # Keep system prompt + last 10 messages
        user_histories[user_id] = [user_histories[user_id][0]] + user_histories[user_id][-10:]

    # 4. Send the FULL history to DeepSeek
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=user_histories[user_id], 
            temperature=0.3 
        )
        ai_reply = response.choices[0].message.content
        
        # 5. Add AI's reply to history so it remembers what it said
        user_histories[user_id].append({"role": "assistant", "content": ai_reply})
        
        return ai_reply
    except Exception as e:
        print(f"AI Error: {e}")
        return "System error. Please try again."

# --- WEBHOOK ---
@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge"), 200
        return "Verification token mismatch", 403
    return "Hello world", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if data['object'] == 'page':
        for entry in data['entry']:
            for event in entry['messaging']:
                if 'message' in event and 'text' in event['message']:
                    sender_id = event['sender']['id']
                    user_text = event['message']['text']
                    
                    # Get response using the MEMORY function
                    ai_text = get_ai_response(sender_id, user_text)
                    
                    # Check for JSON trigger
                    clean_text = ai_text
                    if "ORDER_COMPLETE" in ai_text:
                        try:
                            # Extract JSON part
                            start = ai_text.find('{')
                            end = ai_text.rfind('}') + 1
                            json_str = ai_text[start:end]
                            order_data = json.loads(json_str)
                            
                            # Save to Sheets
                            save_order_to_sheet(order_data)
                            
                            # Remove JSON from the message sent to user
                            clean_text = ai_text.replace(json_str, "").strip()
                            clean_text += "\n✅ (Order Confirmed & Saved!)"
                        except:
                            print("JSON Parsing Failed")

                    send_message(sender_id, clean_text)
        return "ok", 200
    return "ok", 200

def send_message(recipient_id, text):
    params = {"access_token": PAGE_ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}
    data = json.dumps({
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    })
    requests.post("https://graph.facebook.com/v18.0/me/messages", params=params, headers=headers, data=data)

# if __name__ == '__main__':
#     app.run(port=5000, debug=True)
# OLD:
# if __name__ == '__main__':
#    app.run(port=5000, debug=True)

# NEW:
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)