import asyncio
import random
import uuid
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import requests

BIN_ID = "686fe8f653c4bd1d12bb6418"
API_KEY = "$2a$10$m5tAtqR6cSmnACZA5ZB1T.TsS0ZqFqR424hVjVxZiARemYfx7PsJ2"
BASE_URL = f"https://api.jsonbin.io/v3/b/{BIN_ID}"
HEADERS = {
    "X-Master-Key": API_KEY,
    "Content-Type": "application/json"
}

TOKEN = "7581444201:AAGtmBgB3gMKRSYu4VU-dzN9ak7v6DC2Dt8"
ADMIN_ID = 1970583799
MIN_ORDER_QUANTITY = 5 # <-- Minimum Order Quantity

def fetch_data():
    try:
        resp = requests.get(BASE_URL, headers=HEADERS)
        if resp.status_code == 200:
            return resp.json().get("record", {})
    except Exception as e:
        print("Error fetching JSONBin data:", e)
    return {}

def save_data(data):
    try:
        resp = requests.put(BASE_URL, headers=HEADERS, json=data)
        return resp.status_code == 200
    except Exception as e:
        print("Error saving JSONBin data:", e)
    return False

def generate_order_id():
    return "ORD" + uuid.uuid4().hex[:8].upper()

def load_users():
    try:
        response = requests.get(BASE_URL, headers=HEADERS)
        if response.status_code == 200:
            return response.json().get("record", {}).get("users", [])
    except Exception as e:
        print("Error loading users:", e)
    return []


def save_user(user_id, username, first_name, last_name):
    try:
        # Fetch current full data
        response = requests.get(BASE_URL, headers=HEADERS)
        if response.status_code != 200:
            print("Error fetching data before saving user")
            return

        data = response.json().get("record", {})
        users = data.get("users", [])

        user_str = f"{user_id} | @{username or 'NoUsername'} | {first_name or ''} {last_name or ''}"

        # Prevent duplicate
        if not any(str(user_id) in u for u in users):
            users.append(user_str)
            data["users"] = users

            # Save back entire updated data
            put_resp = requests.put(BASE_URL, headers=HEADERS, json=data)
            if put_resp.status_code == 200:
                print(f"✅ Saved: {user_str}")
            else:
                print(f"Failed to save user data, status: {put_resp.status_code}")

    except Exception as e:
        print("Error saving user:", e)

def fetch_jsonbin_data():
    try:
        response = requests.get(BASE_URL, headers=HEADERS)
        if response.status_code == 200:
            return response.json().get('record', {})
    except Exception as e:
        print("Error fetching JSONBin data:", e)
    return {}

def save_jsonbin_data(data):
    try:
        response = requests.put(BASE_URL, headers=HEADERS, json=data)
        return response.status_code == 200
    except Exception as e:
        print("Error saving JSONBin data:", e)
    return False


# MAIN START FUNCTION
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id

    # ✅ Save user to JSONBin.io instead of a text file
    save_user(user.id, user.username, user.first_name, user.last_name)

    keyboard = [
        [InlineKeyboardButton("🧾 New FB ID", callback_data="fb_id")],
        [InlineKeyboardButton("💼 FB BM", callback_data="fb_bm")],
        [InlineKeyboardButton("🚫 FB Boost", callback_data="fb_boost")],
        [InlineKeyboardButton("🚫 Insta ID", callback_data="insta")],
        [InlineKeyboardButton("🔐 OTP Service", callback_data="otp_service")],
    ]

    if user_id == ADMIN_ID:
        admin_text = (
            "👋 Welcome Admin!\n\n"
            "Here are your commands:\n"
            "/start - Show this message\n"
            "/deliver <order_id> <message> - Deliver an order\n"
            "/pending - Show pending orders\n"
            "/orders - Show all orders\n"
            "/cancel <order_id> - Cancel an order\n"
            "/stats - Show sales statistics\n"
            "/broadcast <message> - Send message to all users\n\n"
            "For customers, these are the available products:"
        )
        await update.message.reply_text(admin_text, parse_mode='Markdown')
        await update.message.reply_text("Choose a service below:", reply_markup=InlineKeyboardMarkup(keyboard))
        print(f"[{datetime.now()}] Admin {user_id} started the bot.")
    else:
        await update.message.reply_text(
            "👋 Welcome to @IDBazarOfficialBot!\n📢 Our official channel: @thresholdhelp\n💬 For support, contact: @Himu404\n\nChoose a service below:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        print(f"[{datetime.now()}] User {user_id} started the bot.")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data_key = query.data

    # ✅ Fetch dynamic product data from JSONBin
    data = fetch_data()
    products = data.get("products", {})

    if data_key in products:
        product = products[data_key]
        product_name = product.get("name", "Unnamed")
        price = product.get("price", 0)
        stock = product.get("stock")

        # Save temporary order info in user context
        context.user_data["temp_order"] = {
            "product": product_name,
            "price": price,
            "product_key": data_key,
        }

        stock_msg = f"\n📦 Stock available: {stock}" if stock is not None else ""
        await query.message.reply_text(
            f"✨ You selected {product_name}.\n💰 Price: {price} Taka per ID.{stock_msg}\n\n🔢 How many IDs would you like to purchase?"
        )
        print(f"[{datetime.now()}] User {user_id} selected product '{product_name}'.")

    else:
        # If product is static fallback or non-priced
        static_names = {
            "fb_boost": "FB Boost",
            "insta": "Insta ID",
            "otp_service": "OTP Service"
        }
        name = static_names.get(data_key, "Unknown Product")
        await query.message.reply_text(
            f"✅ Yes, {name} is available.\nবিস্তারিত জানার জন্য যোগাযোগ করুন @Himu404 এর সাথে।"
        )
        print(f"[{datetime.now()}] User {user_id} checked availability of '{name}'.")

async def quantity_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    text = update.message.text.strip()

    temp_order = context.user_data.get("temp_order")
    if not temp_order or "product" not in temp_order:
        return  # No product selected yet

    if not text.isdigit():
        await update.message.reply_text("❌ Please enter a valid number.")
        return

    quantity = int(text)
    if quantity < MIN_ORDER_QUANTITY:
        await update.message.reply_text(f"⚠️ Minimum order is {MIN_ORDER_QUANTITY} pieces.")
        return

    data = fetch_data()
    products = data.get("products", {})

    product_key = temp_order.get("product_key")
    product = products.get(product_key)
    if not product:
        await update.message.reply_text("❌ Product not found.")
        return

    stock = product.get("stock")
    if stock is not None and quantity > stock:
        await update.message.reply_text(
            f"❌ Only {stock} {product['name']} available.\nPlease enter a lower quantity."
        )
        return

    total = product["price"] * quantity
    order_id = generate_order_id()

    temp_order.update({
        "quantity": quantity,
        "total": total,
        "order_id": order_id,
    })
    context.user_data["temp_order"] = temp_order  # save back

    payment_instructions = (
        "💳 *Payment Instructions:*\n\n"
        "📱 Send Money via:\n"
        "`Bkash / Nagad / Rocket` ➤ `01647253544`\n\n"
        "🧾 *Reference:* Use Order ID as reference\n"
        f"`{order_id}`\n\n"
        "📸 *After Payment:* Send a screenshot here for confirmation."
    )

    await update.message.reply_text(
        f"*Order Summary:*\n"
        f"🆔 Order ID: `{order_id}`\n"
        f"📦 Product: {product['name']}\n"
        f"🔢 Quantity: {quantity}\n"
        f"💰 Total: {total} Taka\n\n" + payment_instructions,
        parse_mode='Markdown'
    )

    print(f"[{datetime.now()}] User {user_id} placed temp order {order_id} for {quantity} x {product['name']} (Total: {total} Taka).")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return

    message = " ".join(context.args)

    # Fetch user list from jsonbin
    try:
        response = requests.get(BASE_URL, headers=HEADERS)
        if response.status_code != 200:
            await update.message.reply_text("❌ Failed to fetch user list from database.")
            return
        data = response.json()
        users = data['record'].get('users', [])
    except Exception as e:
        await update.message.reply_text(f"❌ Error loading users: {e}")
        return

    if not users:
        await update.message.reply_text("❌ No users found in database.")
        return

    count = 0
    failed = 0

    for line in users:
        try:
            user_id_str = line.split("|")[0].strip()
            user_id = int(user_id_str)
            await context.bot.send_message(chat_id=user_id, text=message)
            count += 1
            await asyncio.sleep(0.1)  # avoid rate limits
        except Exception as e:
            failed += 1
            print(f"❌ Failed to send to {user_id_str}: {e}")

    await update.message.reply_text(
        f"✅ Broadcast sent to {count} users.\n❌ Failed to send to {failed} users."
    )


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    photo = update.message.photo[-1]

    temp_order = context.user_data.get("temp_order")
    if not temp_order or "order_id" not in temp_order:
        await update.message.reply_text("❌ No order found. Please /start and place an order first.")
        return

    data = fetch_data()
    orders = data.get("orders", [])
    products = data.get("products", {})

    order_id = temp_order["order_id"]
    product = temp_order.get("product", "N/A")
    product_key = temp_order.get("product_key")
    quantity = temp_order.get("quantity", 0)
    total = temp_order.get("total", 0)

    # Decrease stock after payment proof received
    if product_key in products and "stock" in products[product_key]:
        products[product_key]["stock"] -= quantity
        if products[product_key]["stock"] < 0:
            products[product_key]["stock"] = 0  # avoid negative stock

    final_order = {
        "user_id": user_id,
        "username": update.message.from_user.username or "No Username",
        "order_id": order_id,
        "product": product,
        "product_key": product_key,
        "quantity": quantity,
        "total": total,
        "status": "pending",
        "timestamp": datetime.now().isoformat(),
    }
    orders.append(final_order)

    # Save updated data
    data["orders"] = orders
    data["products"] = products

    if save_data(data):
        print(f"✅ Order saved for user {user_id}: {order_id}")
    else:
        await update.message.reply_text("⚠️ Error saving your order. Please contact admin.")
        return

    caption = (
        f"📩 *New Payment Proof Received*\n"
        f"👤 User: @{final_order['username']} (`{user_id}`)\n"
        f"🆔 Order ID: `{order_id}`\n"
        f"📦 Product: {product}\n"
        f"🔢 Quantity: {quantity}\n"
        f"💰 Total: {total} Taka"
    )
    await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo.file_id, caption=caption, parse_mode='Markdown')
    await update.message.reply_text("✅ Thanks for the payment proof! Your order is under review.")
    context.user_data.pop("temp_order", None)

async def deliver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != ADMIN_ID:
        return

    if len(context.args) < 2:
        await update.message.reply_text("❌ Usage: /deliver <order_id> <message>")
        return

    order_id = context.args[0]
    delivery_msg = " ".join(context.args[1:])

    try:
        # Fetch full data from JSONBin
        response = requests.get(BASE_URL, headers=HEADERS)
        if response.status_code != 200:
            await update.message.reply_text("❌ Failed to fetch orders from database.")
            return

        data = response.json().get("record", {})
        orders = data.get("orders", [])

        # Find the order by ID
        order_found = next((o for o in orders if o.get("order_id") == order_id), None)

        if not order_found:
            await update.message.reply_text("❌ Order ID not found.")
            return

        status = order_found.get("status", "pending")
        if status == "delivered":
            await update.message.reply_text("⚠️ This order has already been delivered.")
            return
        elif status == "canceled":
            await update.message.reply_text("⚠️ This order has been canceled and cannot be delivered.")
            return

        # Send message to the user
        user_id = order_found.get("user_id")
        await context.bot.send_message(
            chat_id=user_id,
            text=f"✅ Your order `{order_id}` has been delivered!\n\n{delivery_msg}\n\nThank you for ordering!",
            parse_mode='Markdown'
        )

        # Update order status
        order_found["status"] = "delivered"
        order_found["delivered_at"] = datetime.now().isoformat()

        # Save full updated data
        data["orders"] = orders
        save = requests.put(BASE_URL, headers=HEADERS, json=data)
        if save.status_code != 200:
            await update.message.reply_text("⚠️ Delivered, but failed to update database.")
            return

        await update.message.reply_text(f"✅ Order `{order_id}` marked as delivered.", parse_mode='Markdown')
        print(f"[{datetime.now()}] Admin marked order {order_id} as delivered.")

    except Exception as e:
        await update.message.reply_text("❌ An unexpected error occurred while delivering.")
        print(f"[{datetime.now()}] Error in deliver(): {e}")

async def pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != ADMIN_ID:
        return

    try:
        # Fetch orders from JSONBin
        response = requests.get(BASE_URL, headers=HEADERS)
        if response.status_code != 200:
            await update.message.reply_text("❌ Failed to load orders from database.")
            return

        data = response.json()
        orders = data['record'].get('orders', [])

        # Filter only pending orders
        pending_orders = [order for order in orders if order.get("status", "pending") == "pending"]

        if not pending_orders:
            await update.message.reply_text("✅ No pending orders found.")
            print(f"[{datetime.now()}] Admin checked pending orders: none found.")
            return

        print(f"[{datetime.now()}] Admin viewed {len(pending_orders)} pending orders.")

        # Prepare response chunks (within Telegram limit)
        messages = []
        current_msg = "*⏳ Pending Orders:*\n"

        for order in pending_orders:
            order_text = (
                f"\n━━━━━━━━━━━━━━\n"
                f"📦 Order ID: `{order.get('order_id', 'N/A')}`\n"
                f"👤 User ID: `{order.get('user_id', 'N/A')}`\n"
                f"🛍 Product: {order.get('product', 'N/A')}\n"
                f"🔢 Quantity: {order.get('quantity', 'N/A')}\n"
                f"💰 Total: {order.get('total', 'N/A')} Taka\n"
            )

            if len(current_msg + order_text) > 3500:
                messages.append(current_msg)
                current_msg = "*⏳ Continued Pending Orders:*\n"

            current_msg += order_text

        messages.append(current_msg)

        # Send the messages
        for msg in messages:
            await update.message.reply_text(msg, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text("❌ Error retrieving pending orders.")
        print(f"[{datetime.now()}] Error loading pending orders: {e}")

async def orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != ADMIN_ID:
        return

    try:
        # Load orders from JSONBin.io
        response = requests.get(BASE_URL, headers=HEADERS)
        if response.status_code != 200:
            await update.message.reply_text("❌ Failed to fetch orders.")
            return

        data = response.json()
        orders = data['record'].get('orders', [])

        if not orders:
            await update.message.reply_text("❌ No orders found.")
            print(f"[{datetime.now()}] Admin checked all orders: none found.")
            return

        print(f"[{datetime.now()}] Admin is viewing {len(orders)} orders...")

        messages = []
        current_msg = "*📦 All Orders:*\n"

        for order in orders:
            order_id = order.get('order_id', 'N/A')
            user_id = order.get('user_id', 'N/A')
            username = order.get('username', 'NoUsername')
            product = order.get('product', 'N/A')
            quantity = order.get('quantity', 'N/A')
            total = order.get('total', 'N/A')
            status = order.get('status', 'pending')
            timestamp = order.get('timestamp', '')

            # Format date
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    timestamp_str = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    timestamp_str = timestamp
            else:
                timestamp_str = "N/A"

            order_text = (
                f"\n━━━━━━━━━━━━━━\n"
                f"🆔 Order ID: `{order_id}`\n"
                f"👤 User: @{username} (`{user_id}`)\n"
                f"📦 Product: {product}\n"
                f"🔢 Quantity: {quantity}\n"
                f"💰 Total: {total} Taka\n"
                f"📌 Status: {status.capitalize()}\n"
                f"🕒 Time: {timestamp_str}\n"
            )

            if len(current_msg + order_text) > 3500:
                messages.append(current_msg)
                current_msg = "*📦 Continued Orders:*\n"

            current_msg += order_text

        messages.append(current_msg)

        for msg in messages:
            await update.message.reply_text(msg, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text("❌ Error while retrieving orders.")
        print(f"[{datetime.now()}] Error retrieving orders: {e}")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != ADMIN_ID:
        return

    if not context.args or len(context.args) < 1:
        await update.message.reply_text("❗ Usage: /cancel <order_id>")
        return

    order_id = context.args[0]

    try:
        # Fetch full data from JSONBin
        response = requests.get(BASE_URL, headers=HEADERS)
        if response.status_code != 200:
            await update.message.reply_text("❌ Failed to load order data.")
            return

        data = response.json().get('record', {})
        orders = data.get('orders', [])
        products = data.get('products', {})

        for order in orders:
            if order.get("order_id") == order_id:
                if order.get("status") != "pending":
                    await update.message.reply_text("⚠️ This order is not pending and cannot be canceled.")
                    return

                user_id = order.get("user_id")
                username = order.get("username", "NoUsername")
                product_key = order.get("product_key")
                quantity = order.get("quantity", 0)

                # Restock product if it has stock
                if product_key in products and "stock" in products[product_key]:
                    products[product_key]["stock"] += quantity

                # Update order status
                order["status"] = "canceled"
                order["canceled_at"] = datetime.now().isoformat()

                # Notify user
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"❌ Your order `{order_id}` has been *canceled* by admin.",
                    parse_mode='Markdown'
                )

                # Confirm to admin
                await update.message.reply_text(
                    f"✅ Order `{order_id}` has been canceled and stock updated.",
                    parse_mode='Markdown'
                )

                # Save back full updated data
                data["orders"] = orders
                data["products"] = products
                save = requests.put(BASE_URL, headers=HEADERS, json=data)

                if save.status_code != 200:
                    await update.message.reply_text("⚠️ Canceled but failed to update JSONBin.")
                else:
                    print(f"[{datetime.now()}] Order {order_id} canceled by admin (@{username}, ID: {user_id})")

                return  # Exit after successful cancel

        # If not found
        await update.message.reply_text("❌ Order ID not found or already canceled.")

    except Exception as e:
        await update.message.reply_text("❌ An error occurred during cancellation.")
        print(f"[{datetime.now()}] Error in cancel(): {e}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != ADMIN_ID:
        return

    try:
        # Fetch data from JSONBin
        response = requests.get(BASE_URL, headers=HEADERS)
        if response.status_code != 200:
            await update.message.reply_text("❌ Failed to load data from database.")
            return

        data = response.json()
        orders = data['record'].get('orders', [])
        products = data['record'].get('products', {})

        # Order statistics
        total_orders = len(orders)
        pending_orders = [o for o in orders if o.get("status", "pending") == "pending"]
        delivered_orders = [o for o in orders if o.get("status") == "delivered"]
        canceled_orders = [o for o in orders if o.get("status") == "canceled"]

        total_pending = len(pending_orders)
        total_delivered = len(delivered_orders)
        total_canceled = len(canceled_orders)
        total_revenue = sum(o.get("total", 0) for o in delivered_orders)

        # Start message
        msg = (
            f"📊 *Sales Statistics:*\n"
            f"🧾 Total Orders: {total_orders}\n"
            f"🕒 Pending Orders: {total_pending}\n"
            f"✅ Delivered Orders: {total_delivered}\n"
            f"❌ Canceled Orders: {total_canceled}\n"
            f"💰 Total Revenue: {total_revenue:,} Taka\n\n"
            f"📦 *Current Stock Levels:*\n"
        )

        if products:
            for key in sorted(products):
                product = products[key]
                stock = product.get("stock")
                name = product.get("name", "Unnamed")
                if stock is not None:
                    msg += f"- {name}: {stock} in stock\n"
        else:
            msg += "_No product stock data available._"

        await update.message.reply_text(msg, parse_mode='Markdown')
        print(f"[{datetime.now()}] Admin viewed sales statistics.")

    except Exception as e:
        await update.message.reply_text("❌ Failed to retrieve statistics.")
        print(f"[{datetime.now()}] Error in stats(): {e}")


if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, quantity_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(CommandHandler("deliver", deliver))
    app.add_handler(CommandHandler("pending", pending))
    app.add_handler(CommandHandler("orders", orders))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("stats", stats))

    print(f"[{datetime.now()}] Bot started...")
    app.run_polling()
