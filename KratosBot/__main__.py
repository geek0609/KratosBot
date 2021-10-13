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
    print ("Finding out Admins....")
    for admin in update.effective_chat.get_administrators():
        print(admin.user.id)
        admins.append(admin.user.id)
        if bot.id == admin.user.id:
            BOT_ADMIN = True
            if admin.can_delete_messages:
                BOT_CAN_DELETE=True
            if admin.can_restrict_members:
                BOT_CAN_MUTE=True

    if update.effective_chat.type == "supergroup" and not update.effective_user.id in admins \
            and BOT_ADMIN and BOT_CAN_DELETE:
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


filter_all = Filters.photo
handler = MessageHandler(filter_all, photo_filter, run_async=True)
dispatcher.add_handler(handler, )

updater.start_polling()
