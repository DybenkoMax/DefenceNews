import requests
from bs4 import BeautifulSoup
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Токен вашого бота
TOKEN = "7765035282:AAE-389fgYGvbuxLhTc6suUzHDwad6nb0IA"
# ID каналу
CHANNEL_ID = "@UA_Defence"

# Ініціалізація бота
bot = telegram.Bot(token=TOKEN)

# Заголовки для імітації браузера
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Функція для парсингу новини
def parse_news(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        content_type = response.headers.get('content-type', 'невідомий')
        if 'text/html' not in content_type:
            raise Exception(f"Неправильний тип вмісту: {content_type}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = soup.find('h1').text.strip() if soup.find('h1') else "Без заголовка"
        paragraphs = soup.find_all('p')
        text = " ".join(p.text.strip() for p in paragraphs[:3]) if paragraphs else "Текст відсутній"
        image = soup.find('img')
        image_url = image['src'] if image and 'src' in image.attrs else None
        
        if image_url:
            from urllib.parse import urljoin
            image_url = urljoin(url, image_url)
            img_response = requests.head(image_url, headers=HEADERS, timeout=5)
            if img_response.status_code != 200 or 'image' not in img_response.headers.get('content-type', ''):
                print(f"Недоступне зображення: {image_url}")
                image_url = None
        
        print(f"Parsed: title={title}, text={text[:100]}..., image_url={image_url}")
        return title, text, image_url
    except requests.exceptions.RequestException as e:
        raise Exception(f"Помилка запиту до сайту: {str(e)}")
    except Exception as e:
        raise Exception(f"Помилка парсингу: {str(e)}")

# Функція для аналізу та створення висновків
def analyze_content(title, text):
    analysis = ""
    if "війна" in title.lower() or "війна" in text.lower():
        analysis += "Тема пов'язана з війною. Рекомендується звернути увагу на достовірність джерел та емоційний вплив на читачів.\n"
    if len(text) < 200:
        analysis += "Текст дуже короткий. Можливо, варто додати більше деталей для повноти картини.\n"
    else:
        analysis += "Текст достатньо інформативний. Рекомендується виділити ключові моменти.\n"
    analysis += "Моє бачення: Подія потребує додаткового контексту для читачів каналу."
    return analysis

# Функція для підготовки поста
def prepare_post(title, text, image_url, url):
    analysis = analyze_content(title, text)
    post = (
        f"⚡️ {title.upper()} ⚡️\n\n"
        f"Ось що сталося: {text[:500]}...\n\n"
        f"Висновки та рекомендації:\n{analysis}\n\n"
        f"Джерело: {url}\n"
        f"Тримайте руку на пульсі з @UA_Defence!"
    )
    return post, image_url

# Обробка помилок
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    error = context.error
    error_msg = f"Виникла помилка: {str(error)}"
    print(error_msg)
    if update:
        await update.message.reply_text(error_msg)

# Обробка посилань
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "facebook.com" in url.lower():
        await update.message.reply_text("Парсинг посилань із Facebook не підтримується через обмеження доступу.")
        return
    
    try:
        title, text, image_url = parse_news(url)
        post, img = prepare_post(title, text, image_url, url)
        
        # Зберігаємо дані в контексті для подальшого використання
        context.user_data['post'] = post
        context.user_data['image_url'] = img
        context.user_data['url'] = url
        
        # Кнопки для підтвердження
        keyboard = [
            [InlineKeyboardButton("Опублікувати", callback_data="publish")],
            [InlineKeyboardButton("Переробити", callback_data="rework"),
             InlineKeyboardButton("Редагувати вручну", callback_data="edit")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if img:
            await bot.send_photo(chat_id=update.effective_chat.id, photo=img, caption=post, reply_markup=reply_markup)
        else:
            await bot.send_message(chat_id=update.effective_chat.id, text=post, reply_markup=reply_markup)
        
    except Exception as e:
        await update.message.reply_text(f"Помилка: {str(e)}")

# Обробка кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "publish":
        post = context.user_data.get('post')
        image_url = context.user_data.get('image_url')
        if image_url:
            await bot.send_photo(chat_id=CHANNEL_ID, photo=image_url, caption=post)
        else:
            await bot.send_message(chat_id=CHANNEL_ID, text=post)
        await query.edit_message_text(text="Новину опубліковано на @UA_Defence!")
    
    elif query.data == "rework":
        url = context.user_data.get('url')
        title, text, image_url = parse_news(url)
        new_post, img = prepare_post(title, text, image_url, url)  # Нова версія поста
        context.user_data['post'] = new_post
        context.user_data['image_url'] = img
        
        keyboard = [
            [InlineKeyboardButton("Опублікувати", callback_data="publish")],
            [InlineKeyboardButton("Переробити", callback_data="rework"),
             InlineKeyboardButton("Редагувати вручну", callback_data="edit")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if img:
            await query.edit_message_caption(caption=new_post, reply_markup=reply_markup)
        else:
            await query.edit_message_text(text=new_post, reply_markup=reply_markup)
        await bot.send_message(chat_id=query.message.chat_id, text="Пропозицію перероблено. Перегляньте та виберіть дію.")
    
    elif query.data == "edit":
        await query.edit_message_text(text="Надішліть відредагований текст поста у відповідь на це повідомлення.")
        context.user_data['awaiting_edit'] = True

# Обробка редагованого тексту
async def handle_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('awaiting_edit'):
        edited_post = update.message.text
        context.user_data['post'] = edited_post
        context.user_data['awaiting_edit'] = False
        
        keyboard = [
            [InlineKeyboardButton("Опублікувати", callback_data="publish")],
            [InlineKeyboardButton("Переробити", callback_data="rework"),
             InlineKeyboardButton("Редагувати ще", callback_data="edit")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        image_url = context.user_data.get('image_url')
        if image_url:
            await bot.send_photo(chat_id=update.effective_chat.id, photo=image_url, caption=edited_post, reply_markup=reply_markup)
        else:
            await bot.send_message(chat_id=update.effective_chat.id, text=edited_post, reply_markup=reply_markup)
        await update.message.reply_text("Оновлений пост готовий. Виберіть дію.")

# Старт бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Надішли мені посилання на новину, і я підготую пост для @UA_Defence!")

# Головна функція
def main():
    application = Application.builder().token(TOKEN).build()
    
    application.add_error_handler(error_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit))
    
    print("Бот запущений...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
