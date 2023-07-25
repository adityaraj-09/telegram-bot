from flask import Flask
from threading import Thread
import telegram_bot

app = Flask(__name__)

@app.route('/')
def home():
    file=open("./telegram_bot.py").read()
    return exec(file)

def run():
  app.run(host='0.0.0.0',port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()