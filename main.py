import os
import sys
from fastapi import FastAPI, Request, HTTPException, Header
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FollowEvent
from dotenv import load_dotenv

# Add parent dir to path to import other modules if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import init_db, get_user, create_user, add_credits, decrement_credit, set_pending_prompt, get_pending_prompt, clear_pending_prompt

# ... (imports)

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

        if user["credits"] > 0:
            # Generate Image
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"「{pending_prompt}」で画像を生成しています...少々お待ちください（約10-20秒）")
            )
            
            try:
                image_path = generate_thumbnail(pending_prompt)
                # TODO: Upload image to a public URL so LINE can display it
                
                decrement_credit(user_id) # This also clears pending_prompt
                remaining = user["credits"] - 1
                
                line_bot_api.push_message(
                    user_id,
                    TextSendMessage(text=f"生成完了！\n残りクレジット: {remaining}")
                )
                
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
