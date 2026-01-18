from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import db_helper
import generic_helper
import time

app = FastAPI()

# store active user orders
in_progress_orders = {}


@app.post("/webhook")
async def handle_request(request: Request):

    try:
        payload = await request.json()

        # -------- Extract safely --------
        query_result = payload.get("queryResult", {})

        intent = query_result.get("intent", {}).get("displayName")
        parameters = query_result.get("parameters", {})
        output_contexts = query_result.get("outputContexts", [])

        if not intent:
            return JSONResponse(content={
                "fulfillmentText": "Sorry, I could not detect your intent."
            })

        if not output_contexts:
            return JSONResponse(content={
                "fulfillmentText": "Session not found. Please try again."
            })

        session_id = generic_helper.extract_session_id(
            output_contexts[0]["name"]
        )

        # -------- Intent mapping --------
        intent_handler_dict = {
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
        # Never crash → always respond
        return JSONResponse(content={
            "fulfillmentText": "Internal server error occurred. Please try again later.",
            "error": str(e)
        })


# ==========================
# DB SAVE FUNCTION
# ==========================
def save_to_db(order: dict):
    next_order_id = db_helper.get_next_order_id()

    # Demo / cloud mode fallback
    if not next_order_id:
        next_order_id = int(time.time()) % 100000  # unique demo order id

    for food_item, quantity in order.items():
        code = db_helper.insert_order_item(food_item, quantity, next_order_id)

        if code == -1:
            return -1

    db_helper.insert_order_tracking(next_order_id, "in progress")

    return next_order_id



# ==========================
# COMPLETE ORDER
# ==========================
def complete_order(_: dict, session_id: str):
    print("🔥 COMPLETE ORDER HIT 🔥", session_id)
    if session_id not in in_progress_orders:
        return JSONResponse(content={
            "fulfillmentText": "I cannot find your order. Please place a new order."
        })

    order = in_progress_orders[session_id]

    order_id = save_to_db(order)

    if order_id == -1:
        fulfillment_text = "Sorry! We failed to process your order due to backend error. Please try again."
    else:
        total = db_helper.get_total_order_price(order_id)

        fulfillment_text = (
            f"Awesome! Your order has been placed successfully 🎉\n"
            f"Order ID: {order_id}\n"
            f"Total Amount: {total}\n"
            f"You can pay at delivery 😊"
        )

    del in_progress_orders[session_id]

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })


# ==========================
# ADD TO ORDER
# ==========================
def add_to_order(parameters: dict, session_id: str):

    food_items = parameters.get("food-item", [])
    quantities = parameters.get("number", [])

    if len(food_items) != len(quantities):
        return JSONResponse(content={
            "fulfillmentText": "Please provide food items with correct quantities."
        })

    new_items = dict(zip(food_items, quantities))

    if session_id in in_progress_orders:
        in_progress_orders[session_id].update(new_items)
    else:
        in_progress_orders[session_id] = new_items

    order_str = generic_helper.get_str_from_food_dict(
        in_progress_orders[session_id]
    )

    return JSONResponse(content={
        "fulfillmentText": f"So far you ordered: {order_str}. Do you want anything else?"
    })


# ==========================
# REMOVE FROM ORDER
# ==========================
def remove_from_order(parameters: dict, session_id: str):

    if session_id not in in_progress_orders:
        return JSONResponse(content={
            "fulfillmentText": "I cannot find your order. Please place a new one."
        })

    food_items = parameters.get("food-item", [])
    current_order = in_progress_orders[session_id]

    removed = []
    not_found = []

    for item in food_items:
        if item in current_order:
            removed.append(item)
            del current_order[item]
        else:
            not_found.append(item)

    fulfillment_text = ""

    if removed:
        fulfillment_text += f"Removed: {', '.join(removed)}. "

    if not_found:
        fulfillment_text += f"{', '.join(not_found)} not found in your order. "

    if not current_order:
        fulfillment_text += "Your order is now empty."
    else:
        remaining = generic_helper.get_str_from_food_dict(current_order)
        fulfillment_text += f"Remaining items: {remaining}"

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })


# ==========================
# TRACK ORDER
# ==========================
def track_order(parameters: dict, session_id: str):
    try:
        order_id = int(parameters.get('order_id') or parameters.get('number'))
        order_status = db_helper.get_order_status(order_id)

        if order_status:
            fulfillment_text = f"The order status for order id: {order_id} is: {order_status}"
        else:
            fulfillment_text = f"No order found with order id: {order_id}"

    except Exception as e:
        print("TRACK ORDER ERROR:", e)
        fulfillment_text = "Sorry, something went wrong while checking your order."

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })

