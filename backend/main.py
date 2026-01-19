from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import os
import time

import db_helper
import generic_helper

app = FastAPI()

# =====================================================
# FRONTEND (WEBSITE) SETUP
# =====================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

# Serve static files (css + images)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
async def serve_home():
    """Serve website in browser"""
    with open(os.path.join(FRONTEND_DIR, "home.html"), "r", encoding="utf-8") as f:
        return f.read()


# =====================================================
# IN-MEMORY ORDER STORE
# =====================================================
in_progress_orders = {}


# =====================================================
# DIALOGFLOW WEBHOOK (POST ONLY)
# =====================================================
@app.post("/webhook")
async def handle_request(request: Request):
    try:
        payload = await request.json()

        query_result = payload.get("queryResult", {})
        intent = query_result.get("intent", {}).get("displayName")
        parameters = query_result.get("parameters", {})
        output_contexts = query_result.get("outputContexts", [])

        if not intent:
            return JSONResponse(content={
                "fulfillmentText": "Sorry, I could not detect your intent."
            })

        # Extract session_id safely
        session_id = None
        for ctx in output_contexts:
            if "sessions" in ctx.get("name", ""):
                session_id = generic_helper.extract_session_id(ctx["name"])
                break

        if not session_id:
            return JSONResponse(content={
                "fulfillmentText": "Session not found. Please try again."
            })

        # Intent → function mapping (names MUST match Dialogflow)
        intent_handler_dict = {
            "new.order": start_new_order,
            "order.add - context: ongoing-order": add_to_order,
            "order.remove - context: ongoing-order": remove_from_order,
            "order.complete - context: ongoing-order": complete_order,
            "track.order - context: ongoing-tracking": track_order
        }

        if intent not in intent_handler_dict:
            return JSONResponse(content={
                "fulfillmentText": f"Sorry, I don't understand this request: {intent}"
            })

        return intent_handler_dict[intent](parameters, session_id)

    except Exception as e:
        print("WEBHOOK ERROR:", e)
        return JSONResponse(content={
            "fulfillmentText": "Internal server error occurred. Please try again later."
        })


# =====================================================
# NEW ORDER
# =====================================================
def start_new_order(_: dict, session_id: str):
    in_progress_orders[session_id] = {}
    return JSONResponse(content={
        "fulfillmentText": (
            "🛒 Starting a new order!\n"
            "You can say things like:\n"
            "• I want 2 pizzas\n"
            "• Add 1 pav bhaji"
        )
    })


# =====================================================
# SAVE ORDER (DB / DEMO MODE)
# =====================================================
def save_to_db(order: dict):
    next_order_id = db_helper.get_next_order_id()

    # Cloud / demo fallback
    if not next_order_id:
        next_order_id = int(time.time()) % 100000

    for food_item, quantity in order.items():
        code = db_helper.insert_order_item(food_item, quantity, next_order_id)
        if code == -1:
            return -1

    db_helper.insert_order_tracking(next_order_id, "in progress")
    return next_order_id


# =====================================================
# COMPLETE ORDER
# =====================================================
def complete_order(_: dict, session_id: str):
    if session_id not in in_progress_orders:
        return JSONResponse(content={
            "fulfillmentText": "I cannot find your order. Please place a new order."
        })

    order = in_progress_orders[session_id]
    order_id = save_to_db(order)

    if order_id == -1:
        text = "❌ Failed to place order. Please try again."
    else:
        total = db_helper.get_total_order_price(order_id)
        text = (
            f"🎉 Order placed successfully!\n"
            f"🆔 Order ID: {order_id}\n"
            f"💰 Total: ₹{total}\n"
            f"🚚 Pay on delivery"
        )

    del in_progress_orders[session_id]
    return JSONResponse(content={"fulfillmentText": text})


# =====================================================
# ADD TO ORDER
# =====================================================
def add_to_order(parameters: dict, session_id: str):
    food_items = parameters.get("food-item", [])
    quantities = parameters.get("number", [])

    if len(food_items) != len(quantities):
        return JSONResponse(content={
            "fulfillmentText": "Please provide correct quantities."
        })

    items = dict(zip(food_items, quantities))
    in_progress_orders.setdefault(session_id, {}).update(items)

    order_str = generic_helper.get_str_from_food_dict(
        in_progress_orders[session_id]
    )

    return JSONResponse(content={
        "fulfillmentText": f"So far you ordered: {order_str}. Anything else?"
    })


# =====================================================
# REMOVE FROM ORDER
# =====================================================
def remove_from_order(parameters: dict, session_id: str):
    if session_id not in in_progress_orders:
        return JSONResponse(content={
            "fulfillmentText": "No active order found."
        })

    food_items = parameters.get("food-item", [])
    order = in_progress_orders[session_id]

    for item in food_items:
        order.pop(item, None)

    if not order:
        return JSONResponse(content={
            "fulfillmentText": "Your order is now empty."
        })

    remaining = generic_helper.get_str_from_food_dict(order)
    return JSONResponse(content={
        "fulfillmentText": f"Remaining items: {remaining}"
    })


# =====================================================
# TRACK ORDER
# =====================================================
def track_order(parameters: dict, session_id: str):
    try:
        order_id = int(parameters.get("order_id") or parameters.get("number"))
        status = db_helper.get_order_status(order_id)

        if status:
            text = f"📦 Order {order_id} status: {status}"
        else:
            text = f"No order found with ID {order_id}"

    except Exception:
        text = "Please provide a valid order ID."

    return JSONResponse(content={"fulfillmentText": text})
