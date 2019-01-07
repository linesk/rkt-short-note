import os
import sys
from flask import Flask, request, abort
from flask_pymongo import PyMongo

from linebot import (LineBotApi, WebhookHandler)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
)

app = Flask(__name__)

# get channel_secret and channel_access_token from your environment variable
MONGODB_URI = os.getenv('MONGODB_URI', None)
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if MONGODB_URI is None:
    print('Specify MONGODB_URI as environment variable.')
    sys.exit(1)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)
app.config["MONGO_URI"] = MONGODB_URI
mongo = PyMongo(app)


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


shortnotes = mongo.db.shortnotes


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.message.text.startswith('>บันทึก'):
        message = event.message.text.replace('>บันทึก ', 'ทำการบันทึกแล้ว')
        from datetime import datetime
        import re
        shortnote = {
            'topic': re.search('^หัวข้อ: .*', event.message.text),
            'content': re.search('^เนื้อหา: .*', event.message.text),
            'date_modified': datetime.now()
        }
        shortnote_id = shortnotes.insert_one(shortnote).inserted_id
        message = f'''ทำการบันทึกแล้ว
        หัวข้อ: {shortnote['topic']}
        เนื้อหา: {shortnote['content']}
        แก้ไข้ล่าสุดเมื่อ: {shortnote['date_modified']}
        id: {shortnote_id.str}
        '''

    elif event.message.text.startswith('>สะท้อน'):
        message = event.message.text.replace('>สะท้อน', '')
    else:
        message = 'ลองใหม่นะครับคำ สั่งได้แก่ >บันทึก, >สะท้อน'

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))


if __name__ == "__main__":
    app.run()