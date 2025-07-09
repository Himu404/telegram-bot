import asyncio
import random
import json
import os
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
def load_json(filename, default):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

TOKEN = "7581444201:AAGtmBgB3gMKRSYu4VU-dzN9ak7v6DC2Dt8"
ADMIN_ID = 1970583799
MIN_ORDER_QUANTITY = 5 # <-- Minimum Order Quantity


def load_orders():
    return load_json("orders.json", {})

def save_orders(orders):
    save_json("orders.json", orders)

def load_pending():
    return set(load_json("pending_orders.json", []))

def save_pending(pending):
    save_json("pending_orders.json", list(pending))

def load_order_map():
    return load_json("order_map.json", {})

def save_order_map(order_map):
    save_json("order_map.json", order_map)

def load_products():
    # If you want dynamic stock saving:
    return load_json("products.json", {
        "fb_id": {"name": "New FB ID", "price": 7, "stock": 10},
        "fb_bm": {"name": "FB BM", "price": 8, "stock": 10},
        "fb_boost": {"name": "FB Boost"},
        "insta": {"name": "Insta ID"},
        "otp_service": {"name": "OTP Service"},
    })

def save_products(products):
    save_json("products.json", products)

async def save_all(user_orders, pending_orders, order_id_to_user):
    save_orders(user_orders)
    save_pending(pending_orders)
    save_order_map(order_id_to_user)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id

    # Save user info to users.txt
    user_info = f"{user_id} | @{user.username or 'NoUsername'} | {user.first_name or ''} {user.last_name or ''} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    try:
        with open("users.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
        if not any(str(user_id) in line for line in lines):
            with open("users.txt", "a", encoding="utf-8") as f:
                f.write(user_info)
    except FileNotFoundError:
        with open("users.txt", "a", encoding="utf-8") as f:
            f.write(user_info)

    # Continue original logic
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
    data = query.data

    if data in ["fb_id", "fb_bm"]:
        products = load_products()
        orders = load_orders()
        product = products[data]
        stock = product.get("stock", None)

        context.user_data["temp_order"] = {
            "product": product["name"],
            "price": product["price"],
            "product_key": data,
        }

        
        stock_msg = f"\n📦 Stock available: {stock}" if stock is not None else ""
        await query.message.reply_text(
            f"✨ You selected {product['name']}.\n💰 Price: {product['price']} Taka per ID.{stock_msg}\n\n🔢 How many IDs would you like to purchase?"
        )
        print(f"[{datetime.now()}] User {user_id} selected product '{product['name']}'.")
    else:
        await query.message.reply_text(
            f"✅ Yes, {products[data]['name']} is available.\nবিস্তারিত জানার জন্য যোগাযোগ করুন @Himu404 এর সাথে।"
        )
        print(f"[{datetime.now()}] User {user_id} checked availability of '{products[data]['name']}'.")


async def quantity_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    text = update.message.text.strip()

    # Load products fresh
    products = load_products()

    # Retrieve temporary order from context.user_data
    temp_order = context.user_data.get("temp_order")
    if not temp_order or "product" not in temp_order:
        # User hasn't selected product yet
        return

    if not text.isdigit():
        await update.message.reply_text("Please enter a valid number.")
        return

    quantity = int(text)
    if quantity < MIN_ORDER_QUANTITY:
        await update.message.reply_text(f"Minimum order is {MIN_ORDER_QUANTITY} pieces.")
        return

    product_key = temp_order.get("product_key")
    if product_key in products and "stock" in products[product_key]:
        available_stock = products[product_key]["stock"]
        if quantity > available_stock:
            await update.message.reply_text(
                f"❌ Sorry, only {available_stock} {products[product_key]['name']} are available in stock.\nPlease enter a lower quantity."
            )
            return

    total = temp_order["price"] * quantity
    order_id = f"ORD{random.randint(1000, 9999)}"

    # Update temp_order with quantity, total, and order_id
    temp_order.update({
        "quantity": quantity,
        "total": total,
        "order_id": order_id,
    })

    # Save back to context.user_data
    context.user_data["temp_order"] = temp_order

    payment_instructions = (
        "💳 Payment Instructions:\n\n"
        "📱 Send Money via:\n"
        "Bkash / Nagad / Rocket ➤ 01647253544\n\n"
        "🧾 Reference:\n"
        f"Use Order ID: `{order_id}` as reference\n\n"
        "📸 After Payment:\n"
        "Send a screenshot of your payment for confirmation."
    )

    await update.message.reply_text(
        f"Order ID: `{order_id}` (copy on tap)\n"
        f"Product: {temp_order['product']}\n"
        f"Quantity: {quantity}\n"
        f"Total Price: {total} Taka\n\n"
        + payment_instructions,
        parse_mode='Markdown'
    )

    print(f"[{datetime.now()}] User {user_id} placed temporary order {order_id} for {quantity} x {temp_order['product']} (Total: {total} Taka).")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return

    message = " ".join(context.args)

    # Read user data from file
    try:
        with open("users.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        await update.message.reply_text("❌ No users found.")
        return

    count = 0
    for line in lines:
        parts = line.strip().split("|")
        if not parts or len(parts) < 1:
            continue
        try:
            user_id = int(parts[0].strip())
            await context.bot.send_message(chat_id=user_id, text=message)
            count += 1
            await asyncio.sleep(0.1)  # small delay to avoid rate limiting
        except Exception as e:
            print(f"Failed to send message to {user_id}: {e}")

    await update.message.reply_text(f"✅ Broadcast sent to {count} users.")

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    photo = update.message.photo[-1]

    # Load persistent data fresh from JSON
    user_orders = load_json("orders.json", {})
    pending_orders = set(load_json("pending_orders.json", []))
    order_id_to_user = load_json("order_map.json", {})
    products = load_json("products.json", {})  # Assuming you keep products in JSON too; if not, use global products dict.

    # Instead of checking global RAM, check if user has temp order in context.user_data
    temp_order = context.user_data.get("temp_order")
    if not temp_order or "order_id" not in temp_order:
        await update.message.reply_text("No order found. Please /start and place an order first.")
        return

    order_id = temp_order["order_id"]
    product_key = temp_order.get("product_key", None)
    quantity = temp_order.get("quantity", 0)

    # Add the finalized order permanently to user_orders
    user_orders[str(user_id)] = temp_order

    # Add to pending orders
    pending_orders.add(order_id)
    order_id_to_user[order_id] = user_id

    # Reduce stock if applicable
    if product_key in products and "stock" in products[product_key]:
        products[product_key]["stock"] -= quantity
        if products[product_key]["stock"] < 0:
            products[product_key]["stock"] = 0

    # Save all updates to JSON files
    save_json("orders.json", user_orders)
    save_json("pending_orders.json", list(pending_orders))
    save_json("order_map.json", order_id_to_user)
    save_json("products.json", products)  # Save updated stock if products.json used

    caption = (
        f"New payment proof received:\n"
        f"User: @{update.message.from_user.username or 'No Username'} ({user_id})\n"
        f"Order ID: `{order_id}`\n"
        f"Product: {temp_order['product']}\n"
        f"Quantity: {quantity}\n"
        f"Total Amount: {temp_order['total']} Taka\n"
        f"📦 Remaining stock: {products[product_key]['stock'] if product_key in products else 'N/A'}"
    )

    await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo.file_id, caption=caption, parse_mode='Markdown')
    await update.message.reply_text("✅ Thanks for the payment proof! Please wait for verification.")

    print(f"[{datetime.now()}] Payment proof received for order {order_id} from user {user_id}.")

    # Optionally clear the temp order in user_data after finalizing
    context.user_data.pop("temp_order", None)

async def deliver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != ADMIN_ID:
        return

    # Load fresh data from disk
    user_orders = load_orders()
    pending_orders = load_pending()
    order_id_to_user = load_order_map()

    try:
        order_id = context.args[0]
        delivery_msg = " ".join(context.args[1:])
        user_id = order_id_to_user.get(order_id)

        if user_id and str(user_id) in user_orders and user_orders[str(user_id)].get("order_id") == order_id:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"✅ Your order `{order_id}` has been delivered!\n\n{delivery_msg}\n\nThank you for ordering!",
                parse_mode='Markdown'
            )

            # Remove order from pending list
            pending_orders.discard(order_id)

            # Save updates
            save_pending(pending_orders)

            await update.message.reply_text(f"✅ Delivered order `{order_id}`", parse_mode='Markdown')
            print(f"[{datetime.now()}] Admin delivered order {order_id} to user {user_id}.")
        else:
            await update.message.reply_text("❌ Order ID not found.")
            print(f"[{datetime.now()}] Admin tried to deliver unknown order ID {order_id}.")
    except Exception as e:
        await update.message.reply_text("Usage: /deliver <order_id> <message>")
        print(f"[{datetime.now()}] Admin failed to deliver due to error: {e}")


async def pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != ADMIN_ID:
        return

    try:
        # Load fresh data from disk
        pending_orders_set = set(load_json("pending_orders.json", []))
        order_id_to_user_map = load_json("order_map.json", {})
        user_orders_map = load_json("orders.json", {})

        if not pending_orders_set:
            await update.message.reply_text("❌ No pending orders.")
            print(f"[{datetime.now()}] Admin checked pending orders: none found.")
            return

        messages = []
        current_msg = "*⏳ Pending Orders:*\n"

        for oid in pending_orders_set:
            uid = order_id_to_user_map.get(oid, "Unknown")
            order = user_orders_map.get(str(uid), {})

            line = (
                f"\n━━━━━━━━━━━━━━\n"
                f"📦 Order ID: `{oid}`\n"
                f"👤 User ID: `{uid}`\n"
                f"🛍 Product: {order.get('product', 'N/A')}\n"
                f"🔢 Quantity: {order.get('quantity', 'N/A')}\n"
                f"💰 Total: {order.get('total', 'N/A')} Taka\n"
            )

            if len(current_msg + line) > 3500:
                messages.append(current_msg)
                current_msg = "*⏳ Continued Pending Orders:*\n"

            current_msg += line

        messages.append(current_msg)

        for msg in messages:
            await update.message.reply_text(msg, parse_mode='Markdown')

        print(f"[{datetime.now()}] Admin viewed {len(pending_orders_set)} pending orders.")

    except Exception as e:
        await update.message.reply_text("❌ Error retrieving pending orders.")
        print(f"[{datetime.now()}] Error loading pending orders: {e}")


async def orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != ADMIN_ID:
        return

    try:
        user_orders = load_orders()  # Load latest orders

        if not user_orders:
            await update.message.reply_text("❌ No orders found.")
            print(f"[{datetime.now()}] Admin checked all orders: none found.")
            return

        messages = []
        current_msg = "*📦 All Orders:*\n"

        for uid, order in user_orders.items():
            order_text = (
                f"\n━━━━━━━━━━━━━━\n"
                f"📦 Order ID: `{order.get('order_id', 'N/A')}`\n"
                f"👤 User ID: `{uid}`\n"
                f"📦 Product: {order.get('product', 'N/A')}\n"
                f"🔢 Quantity: {order.get('quantity', 'N/A')}\n"
                f"💰 Total: {order.get('total', 'N/A')} Taka\n"
            )

            if len(current_msg + order_text) > 3500:
                messages.append(current_msg)
                current_msg = "*📦 Continued Orders:*\n"

            current_msg += order_text

        messages.append(current_msg)

        for msg in messages:
            await update.message.reply_text(msg, parse_mode='Markdown')

        print(f"[{datetime.now()}] Admin viewed all orders.")
    
    except Exception as e:
        await update.message.reply_text("❌ Error while retrieving orders.")
        print(f"[{datetime.now()}] Error retrieving orders: {e}")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != ADMIN_ID:
        return

    # Load latest data
    user_orders = load_orders()
    pending_orders = load_pending()
    order_id_to_user = load_order_map()
    products = load_products()

    try:
        order_id = context.args[0]
        user_id = order_id_to_user.get(order_id)
        user_id_str = str(user_id)

        if user_id and user_id_str in user_orders and user_orders[user_id_str].get("order_id") == order_id:
            order = user_orders[user_id_str]
            product_key = order.get("product_key", None)
            quantity = order.get("quantity", 0)

            # Restock the product if applicable
            if product_key in products and "stock" in products[product_key]:
                products[product_key]["stock"] += quantity

            # Remove order data
            user_orders.pop(user_id_str, None)
            pending_orders.discard(order_id)
            order_id_to_user.pop(order_id, None)

            # Save changes
            save_orders(user_orders)
            save_pending(pending_orders)
            save_order_map(order_id_to_user)
            save_products(products)

            # Notify both admin and user
            await context.bot.send_message(
                chat_id=user_id,
                text=f"❌ Your order `{order_id}` has been canceled by admin.",
                parse_mode='Markdown'
            )
            await update.message.reply_text(f"✅ Order `{order_id}` canceled.", parse_mode='Markdown')

            print(f"[{datetime.now()}] Admin canceled order {order_id} for user {user_id}.")
        else:
            await update.message.reply_text("❌ Order ID not found.")
            print(f"[{datetime.now()}] Admin tried to cancel unknown order ID {order_id}.")
    except Exception as e:
        await update.message.reply_text("Usage: /cancel <order_id>")
        print(f"[{datetime.now()}] Admin failed to cancel due to error: {e}")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != ADMIN_ID:
        return

    try:
        # Load fresh data
        user_orders = load_orders()
        pending_orders = load_pending()
        products = load_products()

        total_orders = len(user_orders)
        pending = len(pending_orders)
        total_revenue = sum(order.get("total", 0) for order in user_orders.values())

        msg = (
            f"📊 *Sales Statistics:*\n"
            f"🧾 Total Orders: {total_orders}\n"
            f"🕒 Pending Orders: {pending}\n"
            f"💰 Total Revenue: {total_revenue} Taka\n\n"
            f"📦 *Current Stock Levels:*\n"
        )

        for key, product in products.items():
            if "stock" in product:
                msg += f"- {product['name']}: {product['stock']}\n"

        await update.message.reply_text(msg, parse_mode='Markdown')
        print(f"[{datetime.now()}] Admin checked sales stats.")
    
    except Exception as e:
        await update.message.reply_text("❌ Failed to load stats.")
        print(f"[{datetime.now()}] Error while showing stats: {e}")



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
