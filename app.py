import eventlet
eventlet.monkey_patch()

from flask import Flask, request, jsonify, render_template, redirect, url_for
import uuid
import requests
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)

# 🌐 Your Render Base URL
 RENDER_BASE_URL = "https://your-app-name.onrender.com"
 # Replace this with your actual Render URL

# --- Dummy DBs ---
items_db = {
    "23 59 C1 D9": {"name": "Lays", "price": 10},
    "B3 C5 A8 D9": {"name": "Dairy Milk", "price": 20},
    "93 31 14 DA": {"name": "Maggi Noodles", "price": 15},
    "EE B0 3A 03": {"name": "Parle-G", "price": 5}
}

user_db = {
    "A4 8D BD 02": {"name": "Aditya Raj", "phone": "919399043621"},
    "D9 1A 8C 3F": {"name": "Sumit Agarwall", "phone": "919425110671"}
}

carts = {}
orders = {
    "test1234": {
        "cart": [{"name": "Test Product", "price": 99, "qty": 1}],
        "total": 99,
        "paid": False,
        "user_uid": "A4 8D BD 02"
    }
}

# WhatsApp API Credentials
WHATSAPP_INSTANCE = "instance115734"
WHATSAPP_TOKEN = "uv28o77ilcil63dr"

def send_whatsapp(message, phone):
    url = f"https://api.ultramsg.com/{WHATSAPP_INSTANCE}/messages/chat"
    data = {
        "token": WHATSAPP_TOKEN,
        "to": phone,
        "body": message
    }
    requests.post(url, data=data)

# --- Routes ---

@app.route("/")
def home():
    return redirect(url_for("dashboard"))

@app.route("/dashboard")
def dashboard():
    all_data = []
    for user_uid, cart in carts.items():
        total = sum(i["price"] * i["qty"] for i in cart)
        item_count = len(cart)
        all_data.append({
            "user_uid": user_uid,
            "items": cart,
            "total_cost": total,
            "item_count": item_count
        })
    return render_template("dashboard.html", data=all_data)

@app.route("/get_item", methods=["POST"])
def get_item():
    data = request.json
    item_uid = data.get("item_uid")
    item = items_db.get(item_uid)
    if item:
        return jsonify(item)
    return jsonify({"error": "Item not found"}), 404

@app.route("/add_item", methods=["POST"])
def add_item():
    data = request.json
    user_uid = data["user_uid"]
    item_uid = data["item_uid"]
    item = items_db.get(item_uid)

    if not item:
        return jsonify({"error": "Item not found"}), 404

    carts.setdefault(user_uid, [])
    for i in carts[user_uid]:
        if i["name"] == item["name"]:
            i["qty"] += 1
            break
    else:
        carts[user_uid].append({"name": item["name"], "price": item["price"], "qty": 1})

    return jsonify({"status": "added", "item": item})

@app.route("/remove_item", methods=["POST"])
def remove_item():
    data = request.json
    user_uid = data["user_uid"]
    item_uid = data["item_uid"]
    item = items_db.get(item_uid)

    if not item or user_uid not in carts:
        return jsonify({"error": "Not found"}), 404

    for i in carts[user_uid]:
        if i["name"] == item["name"]:
            i["qty"] -= 1
            if i["qty"] <= 0:
                carts[user_uid].remove(i)
            break

    return jsonify({"status": "removed"})

@app.route("/generate_bill", methods=["POST"])
def generate_bill():
    data = request.json
    user_uid = data["user_uid"]
    cart = carts.get(user_uid, [])

    if not cart:
        return jsonify({"error": "Cart is empty"}), 400

    bill_id = str(uuid.uuid4())[:8]
    total = sum(i["price"] * i["qty"] for i in cart)
    orders[bill_id] = {
        "cart": cart.copy(),
        "total": total,
        "paid": False,
        "user_uid": user_uid
    }

    user = user_db.get(user_uid)
    if user:
        message = f"🧾 Smart Cart Bill\nBill ID: {bill_id}\nUser: {user['name']}\n"
        for item in cart:
            message += f"{item['name']} x{item['qty']} = ₹{item['price'] * item['qty']}\n"
        message += f"Total: ₹{total}\n👉 Pay Now: {RENDER_BASE_URL}/payment/{bill_id}"
        send_whatsapp(message, user["phone"])

    carts[user_uid] = []
    return jsonify({"status": "bill_generated", "total": total})

@app.route("/payment/<bill_id>")
def payment_page(bill_id):
    order = orders.get(bill_id)
    if not order:
        return "Invalid Bill ID"
    return f"""
    <h2>Pay ₹{order['total']}</h2>
    <form action="/mark_paid/{bill_id}" method="post">
        <button type="submit">Pay Now</button>
    </form>
    """

@app.route("/mark_paid/<bill_id>", methods=["POST"])
def mark_paid(bill_id):
    if bill_id in orders:
        orders[bill_id]["paid"] = True
        user_uid = orders[bill_id]["user_uid"]
        user = user_db.get(user_uid)
        if user:
            send_whatsapp(
                f"✅ Payment Received for Bill {bill_id}. Thank you!\nView acknowledgment: {RENDER_BASE_URL}/acknowledgment/{bill_id}",
                user["phone"]
            )
        return "Payment successful!"
    return "Invalid Bill ID"

@app.route("/acknowledgment/<bill_id>")
def acknowledgment(bill_id):
    order = orders.get(bill_id)
    if not order:
        return "Invalid Bill ID"
    user = user_db.get(order["user_uid"])
    return render_template("acknowledgment.html", user=user, total=order["total"])

# --- Start App ---
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
