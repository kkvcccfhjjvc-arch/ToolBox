from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔤 Font & Text", callback_data="lab_text"),
            InlineKeyboardButton("🎛️ Audio Lab", callback_data="lab_audio"),
        ],
        [
            InlineKeyboardButton("🖼️ Image Lab", callback_data="lab_image"),
            InlineKeyboardButton("📄 PDF Lab", callback_data="lab_pdf"),
        ],
        [
            InlineKeyboardButton("📦 File Lab", callback_data="lab_file"),
            InlineKeyboardButton("🎬 Video Lab", callback_data="lab_video"),
        ],
        [
            InlineKeyboardButton("🔲 QR & Barcode", callback_data="lab_qr"),
            InlineKeyboardButton("🌐 Web Lab", callback_data="lab_web"),
        ],
        [
            InlineKeyboardButton("🛠️ Developer Lab", callback_data="lab_dev"),
            InlineKeyboardButton("🧮 Utility Lab", callback_data="lab_util"),
        ]
    ])
