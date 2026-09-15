from telegram import ReplyKeyboardMarkup, KeyboardButton


def main_menu():
    return ReplyKeyboardMarkup(
        [
            [
                KeyboardButton("🔤 Font & Text"),
                KeyboardButton("🎛️ Audio Lab"),
            ],
            [
                KeyboardButton("🖼️ Image Lab"),
                KeyboardButton("📄 PDF Lab"),
            ],
            [
                KeyboardButton("📦 File Lab"),
                KeyboardButton("🎬 Video Lab"),
            ],
            [
                KeyboardButton("🔲 QR & Barcode"),
                KeyboardButton("🌐 Web Lab"),
            ],
            [
                KeyboardButton("🛠️ Developer Lab"),
                KeyboardButton("🧮 Utility Lab"),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )
