import os
import cv2
import numpy as np
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from PIL import Image, ImageDraw, ImageFont
import io

TOKEN = os.getenv("TOKEN")
COMPANY_NAME = "Авито"

TOP_MARGIN = 80
BOTTOM_MARGIN = 120
SIDE_MARGIN = 60

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    image_bytes = await file.download_as_bytearray()

    img = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(img, cv2.IMREAD_COLOR)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    if not contours:
        await update.message.reply_text("❌ Штрихкод не найден")
        return

    x, y, w, h = cv2.boundingRect(contours[0])

    barcode_crop = img[
        max(0, y - 20): y + h + 20,
        max(0, x - SIDE_MARGIN): x + w + SIDE_MARGIN
    ]

    barcode_img = Image.fromarray(cv2.cvtColor(barcode_crop, cv2.COLOR_BGR2RGB))

    canvas_width = barcode_img.width
    canvas_height = (
        TOP_MARGIN +
        barcode_img.height +
        70 +
        45 +
        BOTTOM_MARGIN
    )

    final_img = Image.new("RGB", (canvas_width, canvas_height), "white")
    final_img.paste(barcode_img, (0, TOP_MARGIN))

    draw = ImageDraw.Draw(final_img)

    try:
        font_num = ImageFont.truetype("arial.ttf", 36)
        font_name = ImageFont.truetype("arial.ttf", 30)
    except:
        font_num = font_name = ImageFont.load_default()

    text_number = "503 837 3905"  # если надо — потом автоматизируем
    y_text = TOP_MARGIN + barcode_img.height + 15

    draw.text((canvas_width // 2 - 100, y_text), text_number, fill="black", font=font_num)
    draw.text((canvas_width // 2 - 40, y_text + 40), COMPANY_NAME, fill="black", font=font_name)

    bio = io.BytesIO()
    bio.name = "barcode_ready.png"
    final_img.save(bio, "PNG")
    bio.seek(0)

    await update.message.reply_photo(photo=bio)

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.run_polling()
