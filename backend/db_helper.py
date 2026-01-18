import mysql.connector

try:
    cnx = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Neer@9876",
        database="pandeyji_eatery"
    )
    print("Database connected")

except Exception as e:
    print("Database connection skipped (Demo mode):", e)
    cnx = None

def insert_order_item(food_item, quantity, order_id):
    if cnx is None:
        print("Demo mode: insert_order_item skipped")
        return 1   # pretend success for demo

    try:
        cursor = cnx.cursor()
        cursor.callproc("insert_order_item", (food_item, quantity, order_id))
        cnx.commit()
        cursor.close()
        return 1

    except mysql.connector.Error as err:
        print("DB Error:", err)
        cnx.rollback()
        return -1

def insert_order_tracking(order_id, status):
    if cnx is None:
        print("Demo mode: insert_order_tracking skipped")
        return

    cursor = cnx.cursor()
    query = "INSERT INTO order_tracking (order_id, status) VALUES (%s, %s)"
    cursor.execute(query, (order_id, status))
    cnx.commit()
    cursor.close()

def get_total_order_price(order_id):
    if cnx is None:
        print("Demo mode: returning dummy price")
        return 250  # dummy amount for demo

    cursor = cnx.cursor()
    cursor.execute("SELECT get_total_order_price(%s)", (order_id,))
    result = cursor.fetchone()[0]
    cursor.close()
    return result

def get_next_order_id():
    if cnx is None:
        print("Demo mode: returning dummy order_id")
        return 1

    cursor = cnx.cursor()
    cursor.execute("SELECT MAX(order_id) FROM orders")
    result = cursor.fetchone()[0]
    cursor.close()

    return 1 if result is None else result + 1

def get_order_status(order_id):
    if cnx is None:
        print("Demo mode: returning dummy status")
        return "Order received"

    cursor = cnx.cursor()
    cursor.execute(
        "SELECT status FROM order_tracking WHERE order_id = %s",
        (order_id,)
    )

    result = cursor.fetchone()
    cursor.close()
    return result[0] if result else None

if __name__ == "__main__":
    print(get_next_order_id())
