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

# Функція для парсингу веб-новин
def parse_web_news(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        content_type = response.headers.get('content-type', 'невідомий')
        print(f"Content-Type для {url}: {content_type}")
        if 'text/html' not in content_type.lower():
            raise Exception(f"Неправильний тип вмісту: {content_type}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Витягуємо заголовок
        title = soup.find('h1').text.strip() if soup.find('h1') else "Без заголовка"
        
        # Шукаємо основний контент статті (наприклад, у <article> або <div class="content">)
        article = soup.find('article') or soup.find('div', class_=['content', 'article', 'post-content'])
        if article:
            paragraphs = article.find_all('p', recursive=False)  # Тільки прямі <p> у блоці
        else:
            paragraphs = soup.find_all('p')  # Усі <p>, якщо немає чіткого блоку
        
        text = " ".join(p.text.strip() for p in paragraphs if p.text.strip()) if paragraphs else "Текст відсутній"
        
        # Витягуємо перше зображення
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
    except Exception as e:
        raise Exception(f"Помилка парсингу сайту: {str(e)}")

# Функція для аналізу та створення висновків
def analyze_content(title, text):
    analysis = ""
    if any(keyword in title.lower() or keyword in text.lower() for keyword in ["війна", "конфлікт", "бойові дії"]):
        analysis += "Тема стосується конфлікту. Перевірте факти та додайте контекст.\n"
    if len(text) < 300:
        analysis += "Текст короткий. Рекомендується розширити деталі.\n"
    else:
        analysis += "Текст ґрунтовний. Виділіть ключові моменти для читачів.\n"
    analysis += "Погляд редакції: Подія вимагає уваги аудиторії та чіткого викладу."
    return analysis

# Функція для адаптації поста у стилі новинного каналу
def prepare_post(title, text, image_url, url):
    analysis = analyze_content(title, text)
    # Спеціальна стилістика
    post = (
        f"⚡️ ТЕРМІНОВО: {title.upper()} ⚡️\n\n"
        f"🔥 ЩО ВІДБУЛОСЯ: {text[:600]}... Читайте деталі за посиланням!\n\n"
        f"📌 НАШ ПОГЛЯД:\n{analysis}\n\n"
        f"🌐 Джерело: {url}\n"
        f"👉 Слідкуйте за новинами з @UA_Defence!"
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
    url = update.message.text.strip()
    print(f"Отримано URL: {url}")
    
    try:
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
