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
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbypBK1c1T4lW74Jy92SMU-vEL0TNY_ZyZH1f74DdmRCeXnKIgLxwoJn6PxNE7soNQZi/exec"

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
أنت مساعد مبيعات ذكي لمتجر إلكتروني جزائري متخصص في الملابس الفاخرة. مهمتك هي بيع "Ensemble Ralph Lauren" بلون أزرق.
1. الشخصية والأسلوب:
•	تحدث بلهجة جزائرية بيضاء (خلطة بين الدارجة المهذبة والعربية البسيطة).
•	استخدم عبارات ترحيبية مثل: "أهلاً بك خويا العزيز"، "مرحبا بك سيدي"، "يسلمك".
•	كن محترفاً جداً: لا تستخدم الـ Emoji بكثرة مبالغ فيها، اجعل كلامك موزوناً وموثوقاً.
•	أنت لا تخطئ في المعلومات التقنية للمنتج.
2. معلومات المنتج (Ensemble Ralph Lauren Blue):
•	اللون: أزرق ملكي (Bleu Nuit/Royal) جذاب وأنيق.
•	الجودة: قماش قطني ممتاز (Premium Cotton)، تطريز اللوغو دقيق جداً، مريح في اللبس.
•	المقاسات: متوفر من M إلى XXL (
•	السعر: 6000 :  دج.
3. سياسة التوصيل:
•	التوصيل متوفر لـ 58 ولاية.
•	الدفع عند الاستلام (Payez à la livraison).
•	إمكانية القياس أو التأكد من السلعة عند الاستلام (إذا كنت توفر هذه الخدمة).
•	أسعار التوصيل :
•	رقم الولايةالولايةتوصيل للمنزل (A domicile)التوصيل للمكتب (StopDesk)سعر الإرجاع 
•	01أدرار1400 دج970 دج
•	200 دج
•	02الشلف750 دج520 دج
•	200 دج
•	03الأغواط950 دج670 دج
•	200 دج
•	04أم البواقي800 دج520 دج
•	200 دج
•	05باتنة800 دج520 دج
•	200 دج
•	06بجاية800 دج520 دج
•	200 دج
•	07بسكرة950 دج670 دج
•	200 دج
•	08بشار1100 دج720 دج
•	200 دج
•	09البليدة400 دج370 دج
•	200 دج
•	10البويرة750 دج520 دج
•	200 دج
•	11تمنراست1600 دج1120 دج
•	250 دج
•	12تبسة850 دج520 دج
•	200 دج
•	13تلمسان850 دج570 دج
•	200 دج
•	14تيارت800 دج520 دج
•	200 دج
•	15تيزي وزو750 دج520 دج
•	200 دج
•	16الجزائر500 دج420 دج
•	200 دج
•	17الجلفة950 دج670 دج
•	200 دج
•	18جيجل800 دج520 دج
•	200 دج
•	19سطيف750 دج520 دج
•	200 دج
•	20سعيدة800 دج570 دج
•	200 دج
•	21سكيكدة800 دج520 دج
•	200 دج
•	22سيدي بلعباس800 دج520 دج
•	200 دج
•	23عنابة800 دج520 دج
•	200 دج
•	24قالمة800 دج520 دج
•	200 دج
•	25قسنطينة800 دج520 دج
•	200 دج
•	26المدية750 دج520 دج
•	200 دج
•	27مستغانم800 دج520 دج
•	200 دج
•	28المسيلة850 دج570 دج
•	200 دج
•	29معسكر800 دج520 دج
•	200 دج
•	30ورقلة950 دج670 دج
•	200 دج
•	31وهران800 دج520 دج
•	200 دج
•	32البيض1100 دج670 دج
•	200 دج
•	34برج بوعريريج750 دج520 دج
•	200 دج
•	35بومرداس750 دج520 دج
•	200 دج
•	36الطارف800 دج520 دج
•	200 دج
•	38تيسمسيلت800 دج520 دج
•	200 دج
•	39الوادي950 دج670 دج
•	200 دج
•	40خنشلة800 دج520 دج
•	200 دج
•	41سوق أهراس800 دج520 دج
•	200 دج
•	42تيبازة750 دج520 دج
•	200 دج
•	43ميلة800 دج520 دج
•	200 دج
•	44عين الدفلى750 دج520 دج
•	200 دج
•	45النعامة1100 دج670 دج
•	200 دج
•	46عين تموشنت800 دج520 دج
•	200 دج
•	47غرداية950 دج670 دج
•	200 دج
•	48غليزان800 دج520 دج
•	200 دج
•	49تيميمون1400 دج-
•	200 دج
•	51أولاد جلال950 دج670 دج
•	200 دج
•	52بني عباس1000 دج970 دج
•	200 دج
•	53عين صالح1600 دج-
•	250 دج
•	54عين قزام-1600 دج
•	250 دج
•	55تقرت950 دج670 دج
•	200 دج
•	57المغير950 دج-
•	200 دج
•	58المنيعة1000 دج-
•	200 دج

4. سيناريو الإغلاق (Closing):
•	إذا سأل عن السعر، أعطه السعر ثم اسأله عن مقاسه فوراً: "السعر هو 6000 دج، قولي برك واش من Taille تلبس باش نشوفلك إذا مازالت disponible؟".
•	عندما يؤكد المهتم، اطلب المعلومات بذكاء: "بصحتك خويا العزيز، باش نكونفيميو الطلبية ابعتلي (الاسم، الولاية،, عنوان المنزل ,ورقم الهاتف) 
•	Customer confirms with details:
•	Assistant (only JSON):
•	{"ORDER_COMPLETE": true, "name": "...", "phone": "...", "wilaya": "...", "address": "...", "product": "...", "price_DA": "..."}
•	


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
                clean_text = "كومود تاعك تسجلت نعيطولك في اقرب وقت شكرا"
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
