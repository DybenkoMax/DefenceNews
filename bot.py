import requests
from bs4 import BeautifulSoup
import telegram
import facebook
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Токен вашого бота
TOKEN = "7765035282:AAE-389fgYGvbuxLhTc6suUzHDwad6nb0IA"
# ID каналу
CHANNEL_ID = "@UA_Defence"
# Довготривалий токен доступу до Facebook Graph API
FB_ACCESS_TOKEN = "561800113604160|EPehld3ho74dBE0NsJTIr6UEfwg"

# Ініціалізація бота та Facebook API
bot = telegram.Bot(token=TOKEN)
graph = facebook.GraphAPI(access_token=FB_ACCESS_TOKEN)

# Заголовки для імітації браузера
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Функція для парсингу звичайних сайтів
def parse_web_news(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
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
                image_url = None
        
        return title, text, image_url
    except Exception as e:
        raise Exception(f"Помилка парсингу сайту: {str(e)}")

# Функція для парсингу постів із Facebook
def parse_facebook_post(url):
    try:
        # Витягуємо ID поста з URL
        post_id = url.split("posts/")[1].split("?")[0] if "posts/" in url else url.split("/")[-1]
        post = graph.get_object(id=post_id, fields='message,full_picture,created_time')
        
        title = "Новина з Facebook"
        text = post.get('message', 'Текст відсутній')
        image_url = post.get('full_picture', None)
        
        return title, text, image_url
    except facebook.GraphAPIError as e:
        raise Exception(f"Помилка Facebook API: {str(e)}")
    except Exception as e:
        raise Exception(f"Помилка парсингу Facebook: {str(e)}")

# Функція для аналізу та створення висновків
def analyze_content(title, text):
    analysis = ""
    if "війна" in title.lower() or "війна" in text.lower():
        analysis += "Тема пов'язана з війною. Рекомендується перевірити джерела.\n"
    if len(text) < 200:
        analysis += "Текст короткий. Додайте більше деталей.\n"
    else:
        analysis += "Текст інформативний. Виділіть ключові моменти.\n"
    analysis += "Висновок: Подія потребує контексту для читачів."
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
    print(f"Помилка: {str(error)}")
    if update:
        await update.message.reply_text(f"Виникла помилка: {str(error)}")

# Обробка посилань
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    try:
        if "facebook.com" in url.lower():
            title, text, image_url = parse_facebook_post(url)
        else:
            title, text, image_url = parse_web_news(url)
        
        post, img = prepare_post(title, text, image_url, url)
        context.user_data['post'] = post
        context.user_data['image_url'] = img
        context.user_data['url'] = url
        
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
        if "facebook.com" in url.lower():
            title, text, image_url = parse_facebook_post(url)
        else:
            title, text, image_url = parse_web_news(url)
        new_post, img = prepare_post(title, text, image_url, url)
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
        await bot.send_message(chat_id=query.message.chat_id, text="Пропозицію перероблено.")
    
    elif query.data == "edit":
        await query.edit_message_text(text="Надішліть відредагований текст поста.")
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
        await update.message.reply_text("Оновлений пост готовий.")

# Старт бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Надішли мені посилання на новину (включаючи Facebook), і я підготую пост!")

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
