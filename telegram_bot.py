

import telebot
import requests,json
import random
from keep_alive import keep_alive

import firebase_admin
from firebase_admin import credentials
from firebase_admin import  db
from firebase_admin import storage

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred,{
    "databaseURL":"https://faceattendance-a1720-default-rtdb.firebaseio.com/",
    "storageBucket":"faceattendance-a1720.appspot.com"
})


bot = telebot.TeleBot("6370945377:AAGKbRNqeVIGxmIHC8EWufJ63pAnYrqnIdo")

@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    bot.reply_to(message, "what are you looking for?")

def get_products():
    response = requests.get("https://aditya-impact.onrender.com/api/products")
    json_data = json.loads(response.text)
    image = random.choice(json_data)["image"]
    name=json_data[0]["title"]
    return [image,name]

def get_quote():
    response = requests.get("https://zenquotes.io/api/quotes")
    json_data = json.loads(response.text)
    quote = json_data[0]['q'] + "-" + json_data[0]['a']+"\n"+ json_data[0]['q'] + "-" + json_data[0]['a']
    return quote

def get_img():
    response = requests.get("https://zenquotes.io/api/image")

    return response

@bot.message_handler(commands=["quotes"])
def send_quote(message):
    quote=get_quote()
    bot.send_message(message.chat.id,text=quote)

@bot.message_handler(commands=["image"])
def send_quoteImg(message):
    quote=get_img()
    bot.send_photo(message.chat.id,photo=quote)


@bot.message_handler(content_types=["photo"])
def upload(message):
    photo_id=message.photo[-1].file_id
    file_info=bot.get_file_url(photo_id)
    file=bot.get_file(photo_id)
    downloaded_file=bot.download_file(file.file_path)
    bucket = storage.bucket()

    with open("image.jpg","wb") as new_file:
        new_file.write(downloaded_file)
        blob = bucket.blob(photo_id+".jpg")
        blob.upload_from_filename("image.jpg")
        blob.make_public()
        bot.send_message(message.chat.id,text=blob.public_url)




@bot.message_handler(commands=["product"])
def send_image(message):
    data=get_products()
    bot.send_photo(message.chat.id,data[0])

@bot.message_handler(commands=["poll"])
def poll(message):
    bot.send_poll(chat_id=message.chat.id, options=["India","China","USA","Russia"],
                  question="which is the boggest country by area?")

@bot.message_handler(commands=["title"])
def set_title(message):
    bot.set_chat_title(chat_id=message.chat.id,title="Chat-Bot")




keep_alive()
bot.infinity_polling()