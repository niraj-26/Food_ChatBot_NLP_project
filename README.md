
# 🍔 Pandeyji_Eatery – AI Based Fast Food Chatbot 🍟

Pandeyji_Eatery is an AI-powered food ordering chatbot system designed for a Fast Food Restaurant.  
This chatbot allows customers to:

- Place food orders using conversation
- Add or remove food items
- Confirm orders
- Track their order status using Order ID

This chatbot works like a **virtual waiter** and provides an easy and interactive ordering experience.

---

## 📌 Objectives
✔️ Make food ordering simple and intelligent  
✔️ Store customer orders in database  
✔️ Provide real-time order tracking  
✔️ Create a smart automation solution for a fast food shop

---

## 🧠 Technologies Used
- Dialogflow ES → AI chatbot
- FastAPI (Python) → Backend Webhook
- MySQL → Database
- HTML + CSS → Frontend Website
- ngrok → HTTPS tunneling for webhook

---

## 📂 Directory Structure
```
backend/           → FastAPI backend code
db/                → MySQL database dump (import using MySQL Workbench)
dialogflow_assets/ → Training phrases & intents for Dialogflow
frontend/          → Website files
```

---

## 🛠 Install Required Modules
```bash
pip install mysql-connector
pip install "fastapi[all]"
```

OR simply run:
```bash
pip install -r backend/requirements.txt
```

---

## ▶ Start FastAPI Backend Server
```bash
cd backend
uvicorn main:app --reload
```

---

## 🌍 Enable HTTPS Tunneling using ngrok
Download ngrok → https://ngrok.com/download

Run:
```bash
ngrok http 8000
```

Copy the HTTPS URL shown.

Note: ngrok session can expire, restart if needed.

---

## 🔗 Connect Dialogflow Webhook
Dialogflow Console → Fulfillment → Webhook

Paste:
```
https://YOUR-NGROK-URL/
```

Enable Webhook ✔ Save ✔

Enable webhook in:
- order.add  
- order.remove  
- order.complete  
- track.order (ongoing-tracking)

---

## 🖥️ Run Frontend Website
```bash
python -m http.server 8080
```

Open in browser:
```
http://localhost:8080/home.html
```

⚠️ Do NOT open HTML directly.

---

## 🧪 Chatbot Usage Example
```
User: hi
User: I want to order food
User: add 2 pizzas and 1 samosa
User: that's all
Bot: Order placed successfully. Your order ID is 44
User: track my order
Bot: Please enter order ID
User: 44
Bot: Your order is in progress
```

---

## ⚠️ Important Notes
- Keep FastAPI running
- Keep ngrok running
- Update webhook if ngrok URL changes
- MySQL server must be running

---

## 🎉 Project Successfully Works When
✔ Website chatbot works  
✔ Orders stored in DB  
✔ Order ID generated  
✔ Order tracking works  


