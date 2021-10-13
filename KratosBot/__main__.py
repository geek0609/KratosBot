import datetime
import os
import random
import time
from telegram import *
from telegram.ext import *
import requests
import json
import cv2
import pytesseract
import numpy as np

# Only for Windows
if os.name == 'nt':
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

BOT_API = os.environ.get("BOT_KEY")
TOLERANCE = 1000
bot = Bot(BOT_API)
timeout = 120
updater = Updater(BOT_API, use_context=True, workers=128)
dispatcher = updater.dispatcher

# This contains list of words which the bot will look for
# If the total score is equal to or greater than the TOLERANCE, then the message would be deleted

banned_database = [
    {
        "word": "eth",
        "score": 100
    },
    {
        "word": "money",
        "score": 100
    },
    {
        "word": "bitcoin",
        "score": 1000
    },
    {
        "word": "bitcain",
        "score": 1000
    },
    {
        "word": "credit",
        "score": 100
    },
    {
        "word": "btc",
        "score": 750
    },
    {
        "word": "elon musk",
        "score": 500
    },
    {
        "word": "elon",
        "score": 500
    },
    {
        "word": "musk",
        "score": 500
    },
    {
        "word": "coins",
        "score": 100
    },
    {
        "word": "giving back",
        "score": 1000
    },
    {
        "word": "give back",
        "score": 1000
    },
    {
        "word": "enjoy",
        "score": 100
    },
    {
        "word": "fans",
        "score": 100
    },
]


def check_for_banned(words):
    words = str(words).lower()
    sus = 0
    for word in banned_database:
        if word["word"] in words:
            sus += word["score"]
    return sus


def auto_delete(message_sent, update):
    if update.effective_chat.type == "supergroup" or update.effective_chat.type == "group":
        time.sleep(timeout)
        bot.deleteMessage(update.effective_chat.id, message_sent.message_id)
        bot.deleteMessage(update.effective_chat.id, update.message.message_id)


def photo_filter(update: Update, context: CallbackContext):
    print(update.effective_message)
    picture = bot.get_file(update.effective_message.photo[-1].file_id)
    downloaded_picture = File.download(picture)
    print(downloaded_picture)
    img = cv2.imread(downloaded_picture)
    # gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    # gray, img_bin = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    # gray = cv2.bitwise_not(img_bin)
    # kernel = np.ones((2, 1), np.uint8)
    # img = cv2.erode(gray, kernel, iterations=1)
    # img = cv2.dilate(img, kernel, iterations=1)
    output = pytesseract.image_to_string(img)
    print(output)
    admins = []
    BOT_CAN_DELETE = False
    BOT_ADMIN = False
    BOT_CAN_MUTE = False
    print("Finding out Admins....")
    for admin in update.effective_chat.get_administrators():
        print(admin.user.id)
        admins.append(admin.user.id)
        if bot.id == admin.user.id:
            BOT_ADMIN = True
            if admin.can_delete_messages:
                BOT_CAN_DELETE = True
            if admin.can_restrict_members:
                BOT_CAN_MUTE = True

    if (update.effective_chat.type == "supergroup" or update.effective_chat.type == "group") \
            and not update.effective_user.id in admins and BOT_ADMIN and BOT_CAN_DELETE:
        if check_for_banned(output) >= TOLERANCE:

            muteText = ""

            if BOT_CAN_MUTE:
                bot.restrictChatMember(user_id=update.effective_user.id,
                                       chat_id=update.effective_chat.id,
                                       permissions=ChatPermissions(False, False, False, False, False, False, False,
                                                                   False),
                                       until_date=datetime.datetime.now().timestamp() + 86400)
                muteText = "\nMuted user " + str(update.effective_user.id) + " for a day"

            bot.send_message(chat_id=update.effective_chat.id,
                             text="This message is detected to be a spam\nIt got a "
                                  "suspicious rating of " + str(check_for_banned(output)) +
                                  "\nMaximum tolerance is " + str(TOLERANCE) +
                                  "\n\nMessage will be deleted in few seconds" + muteText,
                             reply_to_message_id=update.effective_message.message_id)
            time.sleep(5)
            bot.deleteMessage(message_id=update.effective_message.message_id, chat_id=update.effective_chat.id)
    os.remove(downloaded_picture)


def startKratos(update: Update, context: CallbackContext):
    message_sent = bot.send_message(chat_id=update.effective_chat.id,
                     text="I am running, ready to mute them scammers!",
                     reply_to_message_id=update.effective_message.message_id)
    auto_delete(message_sent, update)


def helpKratos(update: Update, context: CallbackContext):
    message_sent = bot.send_message(chat_id=update.effective_chat.id,
                                    text="Just put me into a group and give me permissions to do my work.\n" +
                                         "I will begin reading every photo (no photo is stored anywhere, "
                                         "it is instantly deleted " +
                                         "once the text recognition is done) and look for keywords such as "
                                         "\"bitcoin\", \"btc\", " +
                                         "\"money\" and give them scores accordingly. For example, \"bitcoin\" has a "
                                         "high " +
                                         "possibility to be a scam message, hence it is given a score of 1000 while "
                                         "words like " +
                                         "money may not always mean a scam message, hence it is given a score of 100. "
                                         "Anything over " +
                                         "1000 score is considered a scam and action is instantly taken. For now I am "
                                         "made to delete" +
                                         " the suspected scammers message and mute them for 1 day. \n\n" +
                                         "also I am an open source project, read my code at "
                                         "https://github.com/geek0609/KratosBot ",
                                    reply_to_message_id=update.effective_message.message_id)
    auto_delete(message_sent, update)


filter_handler = MessageHandler(Filters.photo, photo_filter, run_async=True)
start_command = CommandHandler("startkratos", startKratos, run_async=True)
help_command = CommandHandler("helpkratos", helpKratos, run_async=True)

dispatcher.add_handler(filter_handler, )
dispatcher.add_handler(start_command)
dispatcher.add_handler(help_command)
updater.start_polling()
