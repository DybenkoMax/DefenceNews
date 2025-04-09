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

# Функція для парсингу новини
def parse_news(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Витягуємо заголовок
    title = soup.find('h1').text.strip() if soup.find('h1') else "Без заголовка"
    
    # Витягуємо текст (перший параграф)
    text = soup.find('p').text.strip() if soup.find('p') else "Текст відсутній"
    
    # Витягуємо перше зображення
    image = soup.find('img')
    image_url = image['src'] if image and 'src' in image.attrs else None
    
    return title, text, image_url

# Функція для адаптації новини
def adapt_news(title, text):
    adapted_text = f"⚡️ {title.upper()} ⚡️\n\nОсь що сталося: {text}.\nТримайте руку на пульсі з @UA_Defence!"
    return adapted_text

# Обробка повідомлень з посиланням
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
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

if name == '__main__':
    main()
