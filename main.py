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
