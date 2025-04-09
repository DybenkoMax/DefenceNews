import requests
from bs4 import BeautifulSoup
import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

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
        text = soup.find('p').text.strip() if soup.find('p') else "Текст відсутній"
        image = soup.find('img')
        image_url = image['src'] if image and 'src' in image.attrs else None
        
        if image_url:
            from urllib.parse import urljoin
            # Перетворюємо відносний URL на абсолютний
            image_url = urljoin(url, image_url)
            # Перевіряємо доступність зображення
            img_response = requests.head(image_url, headers=HEADERS, timeout=5)
            if img_response.status_code != 200 or 'image' not in img_response.headers.get('content-type', ''):
                print(f"Недоступне або невалідне зображення: {image_url}")
                image_url = None
        
        print(f"Parsed image_url: {image_url}")  # Логування для дебагу
        return title, text, image_url
    except requests.exceptions.RequestException as e:
        raise Exception(f"Помилка запиту до сайту: {str(e)}")
    except Exception as e:
        raise Exception(f"Помилка парсингу: {str(e)}")

# Функція для адаптації новини
def adapt_news(title, text):
    adapted_text = f"⚡️ {title.upper()} ⚡️\n\nОсь що сталося: {text}.\nТримайте руку на пульсі з @UA_Defence!"
    return adapted_text

# Обробка помилок
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    error = context.error
    error_msg = f"Виникла помилка: {str(error)}"
    print(error_msg)  # Логування в консоль
    if update:
        await update.message.reply_text(error_msg)

# Обробка повідомлень з посиланням
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "facebook.com" in url.lower():
        await update.message.reply_text("Парсинг посилань із Facebook не підтримується через обмеження доступу.")
        return
    
    try:
        title, text, image_url = parse_news(url)
        adapted_message = adapt_news(title, text)
        
        # Надсилаємо в канал
        if image_url:
            print(f"Спроба надіслати фото: {image_url}")
            await bot.send_photo(chat_id=CHANNEL_ID, photo=image_url, caption=adapted_message)
        else:
            print("Зображення відсутнє, надсилаємо лише текст")
            await bot.send_message(chat_id=CHANNEL_ID, text=adapted_message)
        
        await update.message.reply_text("Новину опубліковано на @UA_Defence!")
    except Exception as e:
        await update.message.reply_text(f"Помилка: {str(e)}")

# Старт бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Надішли мені посилання на новину, і я опублікую її на @UA_Defence у своєму стилі!")

# Головна функція
def main():
    application = Application.builder().token(TOKEN).build()
    
    application.add_error_handler(error_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    
    print("Бот запущений...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
