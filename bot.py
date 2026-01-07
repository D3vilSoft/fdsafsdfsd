from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from pyzbar import pyzbar
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io

TOKEN = os.getenv("TOKEN")

COMPANY_NAME = "Авито"

# Печатные отступы (меняй при необходимости)
TOP_MARGIN = 80
BOTTOM_MARGIN = 120
SIDE_MARGIN = 60

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    image_bytes = await file.download_as_bytearray()

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img_np = np.array(img)

    barcodes = pyzbar.decode(img_np)
    if not barcodes:
        await update.message.reply_text("❌ Штрихкод не найден")
        return

    barcode = barcodes[0]
    x, y, w, h = barcode.rect
    code = barcode.data.decode("utf-8")

    # Вырезаем штрихкод с запасом
    barcode_crop = img_np[
        max(0, y - 20): y + h + 20,
        max(0, x - SIDE_MARGIN): x + w + SIDE_MARGIN
    ]

    barcode_img = Image.fromarray(barcode_crop)

    # Белый холст под печать
    canvas_width = barcode_img.width
    canvas_height = (
        TOP_MARGIN +
        barcode_img.height +
        70 +   # номер
        45 +   # компания
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

    # Формат номера как у Авито
    formatted = " ".join([code[i:i+3] for i in range(0, len(code), 3)])

    y_text = TOP_MARGIN + barcode_img.height + 15

    num_w = draw.textlength(formatted, font=font_num)
    name_w = draw.textlength(COMPANY_NAME, font=font_name)

    draw.text(((canvas_width - num_w) // 2, y_text),
              formatted, fill="black", font=font_num)

    draw.text(((canvas_width - name_w) // 2, y_text + 40),
              COMPANY_NAME, fill="black", font=font_name)

    bio = io.BytesIO()
    bio.name = "barcode_print_ready.png"
    final_img.save(bio, "PNG")
    bio.seek(0)

    await update.message.reply_photo(photo=bio)

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.run_polling()

