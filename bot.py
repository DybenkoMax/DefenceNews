import requests
from bs4 import BeautifulSoup
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Токен вашого бота
TOKEN = "7765035282:AAE-389fgYGvbuxLhTc6suUzHDwad6nb0IA"
# ID каналу (можна отримати через @username_to_id_bot)
CHANNEL_ID = "@UA_Defence"

# Ініціалізація бота
bot = telegram.Bot(token=TOKEN)

# Функція для парсингу новини
def parse_news(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Витягуємо заголовок (може залежати від структури сайту)
    title = soup.find('h1').text.strip() if soup.find('h1') else "Без заголовка"
    
    # Витягуємо текст (перший параграф як приклад)
    text = soup.find('p').text.strip() if soup.find('p') else "Текст відсутній"
    
    # Витягуємо перше зображення
    image = soup.find('img')
    image_url = image['src'] if image and 'src' in image.attrs else None
    
    return title, text, image_url

# Функція для адаптації новини у вашому стилі
def adapt_news(title, text):
    # Приклад адаптації: додаємо емоційний тон і ваш стиль
    adapted_text = f"⚡️ {title.upper()} ⚡️\n\nОсь що сталося: {text}.\nТримайте руку на пульсі з @UA_Defence!"
    return adapted_text

# Обробка повідомлень з посиланням
def handle_link(update, context):
    url = update.message.text
    try:
        # Парсимо новину
        title, text, image_url = parse_news(url)
        
        # Адаптуємо текст
        adapted_message = adapt_news(title, text)
        
        # Надсилаємо в канал
        if image_url:
            bot.send_photo(chat_id=CHANNEL_ID, photo=image_url, caption=adapted_message)
        else:
            bot.send_message(chat_id=CHANNEL_ID, text=adapted_message)
        
        # Повідомляємо користувача про успіх
        update.message.reply_text("Новину опубліковано на @UA_Defence!")
    except Exception as e:
        update.message.reply_text(f"Помилка: {str(e)}")

# Старт бота
def start(update, context):
    update.message.reply_text("Надішли мені посилання на новину, і я опублікую її на @UA_Defence у своєму стилі!")

# Головна функція
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    # Команда /start
    dp.add_handler(CommandHandler("start", start))
    
    # Обробка всіх текстових повідомлень (посилань)
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_link))
    
    # Запуск бота
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
