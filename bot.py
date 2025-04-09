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
        response.raise_for_status()  # Перевіряємо, чи запит успішний
        
        # Логуємо тип вмісту для діагностики
        content_type = response.headers.get('content-type', 'невідомий')
        if 'text/html' not in content_type:
            raise Exception(f"Неправильний тип вмісту: {content_type}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Витягуємо заголовок
        title = soup.find('h1').text.strip() if soup.find('h1') else "Без заголовка"
        
        # Витягуємо текст (перший параграф)
        text = soup.find('p').text.strip() if soup.find('p') else "Текст відсутній"
        
        # Витягуємо перше зображення
        image = soup.find('img')
        image_url = image['src'] if image and 'src' in image.attrs else None
        
        # Перевіряємо, чи URL зображення абсолютний
        if image_url and not image_url.startswith('http'):
            from urllib.parse import urljoin
            image_url = urljoin(url, image_url)
        
        return title, text, image_url
    except requests.exceptions.RequestException as e:
        raise Exception(f"Помилка запиту до сайту: {str(e)}")
    except Exception as e:
        raise Exception(f"Помилка парсингу: {str(e)}")

# Функція для адаптації новини
def adapt_news(title, text):
    adapted_text = f"⚡️ {title.upper()} ⚡️\n\nОсь що сталося: {text}.\nТримайте руку на пульсі з @UA_Defence!"
    return adapted_text

# Обробка повідомлень з посиланням
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    # Перевірка на Facebook-посилання
    if "facebook.com" in url.lower():
        await update.message.reply_text("Парсинг посилань із Facebook не підтримується через обмеження доступу.")
        return
    
    try:
        # Парсимо новину
        title, text, image_url = parse_news(url)
        
        # Адаптуємо текст
        adapted_message = adapt_news(title, text)
        
        # Надсилаємо в канал
        if image_url:
            await bot.send_photo(chat_id=CHANNEL_ID, photo=image_url, caption=adapted_message)
        else:
            await bot.send_message(chat_id=CHANNEL_ID, text=adapted_message)
        
        # Повідомляємо користувача
        await update.message.reply_text("Новину опубліковано на @UA_Defence!")
    except Exception as e:
        await update.message.reply_text(f"Помилка: {str(e)}")

# Старт бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Надішли мені посилання на новину, і я опублікую її на @UA_Defence у своєму стилі!")

# Головна функція
def main():
    # Ініціалізація Application
    application = Application.builder().token(TOKEN).build()
    
    # Команда /start
    application.add_handler(CommandHandler("start", start))
    
    # Обробка текстових повідомлень (посилань)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    
    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
