import os
import sys
from fastapi import FastAPI, Request, HTTPException, Header
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FollowEvent
from dotenv import load_dotenv

# Add parent dir to path to import other modules if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import init_db, get_user, create_user, add_credits, decrement_credit
from image_gen import generate_thumbnail
from stripe_utils import create_checkout_session, handle_stripe_webhook

load_dotenv()

app = FastAPI()

# LINE Bot Setup
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Initialize DB
init_db()

@app.post("/callback")
async def callback(request: Request, x_line_signature: str = Header(None)):
    body = await request.body()
    try:
        handler.handle(body.decode("utf-8"), x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    return "OK"

@handler.add(FollowEvent)
def handle_follow(event):
    user_id = event.source.user_id
    create_user(user_id)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="登録ありがとうございます！\nYouTubeサムネイル生成Botです。\n\n作りたいサムネイルのイメージを文章で送ってください。\n\n初回は1回無料で生成できます。\nその後は10回980円で追加できます。")
    )

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_text = event.message.text
    
    user = get_user(user_id)
    if not user:
        create_user(user_id)
        user = get_user(user_id)
    
    if user["credits"] > 0:
        # Generate Image
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="画像を生成しています...少々お待ちください（約10-20秒）")
        )
        
        try:
            image_path = generate_thumbnail(user_text)
            # TODO: Upload image to a public URL so LINE can display it
            # For now, we will just say it's done and maybe send a link if we had storage
            # Since we are local, we might need ngrok for the image URL or Imgur API
            
            decrement_credit(user_id)
            remaining = user["credits"] - 1
            
            line_bot_api.push_message(
                user_id,
                TextSendMessage(text=f"生成完了！\n残りクレジット: {remaining}")
            )
            # Send Image Message here (requires public URL)
            
        except Exception as e:
            line_bot_api.push_message(
                user_id,
                TextSendMessage(text=f"エラーが発生しました: {str(e)}")
            )
    else:
        # Payment Link
        checkout_url = create_checkout_session(user_id)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"クレジットが不足しています。\nこちらからチャージしてください（980円/10回）:\n{checkout_url}")
        )

@app.post("/stripe_webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        handle_stripe_webhook(payload, sig_header)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return "OK"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
