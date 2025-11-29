import os
import sys
from fastapi import FastAPI, Request, HTTPException, Header
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FollowEvent, ImageSendMessage
from dotenv import load_dotenv

#
# Add parent dir to path to import other modules if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import init_db, get_user, create_user, add_credits, decrement_credit, set_pending_prompt, get_pending_prompt, clear_pending_prompt
from image_gen import generate_thumbnail
from stripe_utils import handle_stripe_webhook, get_payment_link
from gcs_utils import upload_to_gcs

load_dotenv()

# Setup Google Credentials for GCS (Service Account)
creds_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
if creds_json:
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp:
        temp.write(creds_json)
        temp_path = temp.name
    
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_path
    print(f"Loaded Service Account credentials to {temp_path}")

from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Mount static directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

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

@app.post("/stripe_webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        handle_stripe_webhook(payload, sig_header)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
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
    user_text = event.message.text.strip()
    
    user = get_user(user_id)
    if not user:
        create_user(user_id)
        user = get_user(user_id)
    
    # 1. Handle Confirmation "はい"
    if user_text == "はい":
        pending_prompt = get_pending_prompt(user_id)
        if not pending_prompt:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="生成する内容が見つかりません。先に作りたい画像のイメージを送ってください。")
            )
            return

        # Credit Check
        print(f"User {user_id} credits before: {user['credits']}")
        if user["credits"] <= 0:
            payment_link = get_payment_link(user_id)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"チケットが不足しています。\nこちらから購入してください（10回分 980円）:\n{payment_link}")
            )
            return

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"「{pending_prompt}」で画像を生成しています...少々お待ちください（約10-20秒）")
        )
        
        try:
            image_path = generate_thumbnail(pending_prompt)
            
            # Upload to Google Cloud Storage
            image_url = upload_to_gcs(image_path)
            print(f"Upload result URL: {image_url}")
            
            if image_url:
                decrement_credit(user_id) # Enable credit deduction
                print(f"Decremented credit for {user_id}")
                
                # Check new balance
                updated_user = get_user(user_id)
                print(f"User {user_id} credits after: {updated_user['credits']}")
                
                clear_pending_prompt(user_id)
                
                # Send Image and Text (Use Push Message)
                line_bot_api.push_message(
                    user_id,
                    [
                        TextSendMessage(text=f"生成完了！\n残りチケット: {updated_user['credits']}枚"),
                        ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)
                    ]
                )
            else:
                print("Upload failed, credit not deducted.")
                line_bot_api.push_message(
                    user_id,
                    TextSendMessage(text="画像のアップロードに失敗しました。")
                )
            
        except Exception as e:
            line_bot_api.push_message(
                user_id,
                TextSendMessage(text=f"エラーが発生しました: {str(e)}")
            )
            
    # 2. Handle Cancellation "いいえ"
    elif user_text == "いいえ":
        clear_pending_prompt(user_id)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="キャンセルしました。")
        )

    # 3. Handle New Prompt
    else:
        set_pending_prompt(user_id, user_text)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"「{user_text}」\nこの内容で画像を生成しますか？\n(はい/いいえ)")
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
