import os
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

API_TOKEN = os.environ.get('BOT_TOKEN')
GROUP_ID = int(os.environ.get('GROUP_ID', '-1002592952684'))

bot = telebot.TeleBot(API_TOKEN)

wait_for_question = {}
user_to_group_message = {}
group_message_to_user = {}

def user_link(user):
    name = user.first_name or "Пользователь"
    if user.last_name:
        name += f" {user.last_name}"
    return f"[{name}](tg://user?id={user.id})"

def get_support_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("✉️ Задать вопрос поддержке"))
    return markup

def send_to_group(from_user, text=None, photo=None, document=None, audio=None, video=None, voice=None, caption=None):
    author = user_link(from_user)
    prefix = f"❓ Вопрос от {author}:\n"
    if text:
        sent = bot.send_message(GROUP_ID, f"{prefix}{text}", parse_mode="Markdown")
        return sent
    elif photo:
        sent = bot.send_photo(GROUP_ID, photo, caption=(f"{prefix}{caption}" if caption else prefix), parse_mode="Markdown")
        return sent
    elif document:
        sent = bot.send_document(GROUP_ID, document, caption=(f"{prefix}{caption}" if caption else prefix), parse_mode="Markdown")
        return sent
    elif audio:
        sent = bot.send_audio(GROUP_ID, audio, caption=(f"{prefix}{caption}" if caption else prefix), parse_mode="Markdown")
        return sent
    elif video:
        sent = bot.send_video(GROUP_ID, video, caption=(f"{prefix}{caption}" if caption else prefix), parse_mode="Markdown")
        return sent
    elif voice:
        sent = bot.send_voice(GROUP_ID, voice, caption=(f"{prefix}{caption}" if caption else prefix), parse_mode="Markdown")
        return sent
    return None

@bot.message_handler(func=lambda m: m.chat.type == "private" and m.text == "✉️ Задать вопрос поддержке", content_types=['text'])
def ask_support_start(message):
    wait_for_question[message.from_user.id] = True
    bot.send_message(
        message.chat.id,
        "Пожалуйста, отправьте свой вопрос (можно приложить медиа). После этого кнопка появится снова.",
        reply_markup=ReplyKeyboardRemove()
    )

def process_question(message, *, media_type=None):
    uid = message.from_user.id
    if not wait_for_question.get(uid):
        bot.send_message(
            message.chat.id,
            "Чтобы задать вопрос поддержке, нажмите кнопку ниже.",
            reply_markup=get_support_keyboard()
        )
        return
    wait_for_question[uid] = False
    sent = None
    if media_type == 'text':
        sent = send_to_group(message.from_user, text=message.text)
    elif media_type == 'photo':
        sent = send_to_group(message.from_user, photo=message.photo[-1].file_id, caption=message.caption)
    elif media_type == 'document':
        sent = send_to_group(message.from_user, document=message.document.file_id, caption=message.caption)
    elif media_type == 'audio':
        sent = send_to_group(message.from_user, audio=message.audio.file_id, caption=message.caption)
    elif media_type == 'video':
        sent = send_to_group(message.from_user, video=message.video.file_id, caption=message.caption)
    elif media_type == 'voice':
        sent = send_to_group(message.from_user, voice=message.voice.file_id, caption=message.caption)
    if sent:
        user_to_group_message[uid] = sent.message_id
        group_message_to_user[sent.message_id] = uid
        bot.send_message(
            message.chat.id,
            "Ваш вопрос передан в поддержку. Чтобы задать следующий вопрос, нажмите кнопку ниже.",
            reply_markup=get_support_keyboard()
        )
    else:
        bot.send_message(
            message.chat.id,
            "Не удалось отправить вопрос. Попробуйте снова.",
            reply_markup=get_support_keyboard()
        )

@bot.message_handler(func=lambda m: m.chat.type == "private", content_types=['text'])
def from_user_private_text(message):
    if message.text == "✉️ Задать вопрос поддержке":
        ask_support_start(message)
    else:
        process_question(message, media_type='text')

@bot.message_handler(func=lambda m: m.chat.type == "private", content_types=['photo'])
def from_user_private_photo(message):
    process_question(message, media_type='photo')

@bot.message_handler(func=lambda m: m.chat.type == "private", content_types=['document'])
def from_user_private_document(message):
    process_question(message, media_type='document')

@bot.message_handler(func=lambda m: m.chat.type == "private", content_types=['audio'])
def from_user_private_audio(message):
    process_question(message, media_type='audio')

@bot.message_handler(func=lambda m: m.chat.type == "private", content_types=['video'])
def from_user_private_video(message):
    process_question(message, media_type='video')

@bot.message_handler(func=lambda m: m.chat.type == "private", content_types=['voice'])
def from_user_private_voice(message):
    process_question(message, media_type='voice')

@bot.message_handler(func=lambda m: m.chat.id == GROUP_ID and m.reply_to_message is not None, content_types=['text', 'photo', 'document', 'audio', 'video', 'voice'])
def from_group_reply(message):
    reply_msg = message.reply_to_message
    user_id = group_message_to_user.get(reply_msg.message_id)
    if user_id:
        try:
            if message.text:
                bot.send_message(user_id, f"💬 Ответ на ваш вопрос:\n\n{message.text}", reply_markup=get_support_keyboard())
            elif message.photo:
                bot.send_photo(user_id, message.photo[-1].file_id, caption=f"💬 Ответ на ваш вопрос:\n\n{message.caption or ''}", reply_markup=get_support_keyboard())
            elif message.document:
                bot.send_document(user_id, message.document.file_id, caption=f"💬 Ответ на ваш вопрос:\n\n{message.caption or ''}", reply_markup=get_support_keyboard())
            elif message.audio:
                bot.send_audio(user_id, message.audio.file_id, caption=f"💬 Ответ на ваш вопрос:\n\n{message.caption or ''}", reply_markup=get_support_keyboard())
            elif message.video:
                bot.send_video(user_id, message.video.file_id, caption=f"💬 Ответ на ваш вопрос:\n\n{message.caption or ''}", reply_markup=get_support_keyboard())
            elif message.voice:
                bot.send_voice(user_id, message.voice.file_id, caption=f"💬 Ответ на ваш вопрос:\n\n{message.caption or ''}", reply_markup=get_support_keyboard())
        except Exception:
            bot.send_message(message.chat.id, "❗ Не удалось отправить ответ пользователю — возможно, он не начинал диалог с ботом.", reply_to_message_id=message.message_id)

if __name__ == '__main__':
    print("Бот запущен!")
    bot.polling(none_stop=True)