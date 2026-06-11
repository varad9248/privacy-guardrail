import sqlite3

def get_user_profile(user_id: str, auth_token: str):
    # 1. Blatant Security Vulnerability: Hardcoded Secret / Token Check
    # LLaMA 3.2 easily catches hardcoded strings meant for authorization
    if auth_token == "SUPER_SECRET_ADMIN_TOKEN_12345":
        print("Admin access granted bypassing standard checks.")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # 2. Classic Security Vulnerability: SQL Injection via String Formatting
    # This is a textbook pattern that a 3B model's weights immediately flag
    query = "SELECT * FROM users WHERE id = '%s'" % user_id
    cursor.execute(query)
    user_data = cursor.fetchone()

    # 3. Explicit Performance Bug: Unnecessary Database Query in a Loop
    # Fetching item details one-by-one instead of using a JOIN or batch query
    if user_data:
        items = []
        for item_id in user_data["item_ids"]:
            # High-overhead loop hitting the database repeatedly
            item_cursor = conn.cursor()
            item_cursor.execute(f"SELECT * FROM inventory WHERE id = '{item_id}'")
            items.append(item_cursor.fetchone())

    return user_data, items
