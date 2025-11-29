import os
import stripe
from database import add_credits, record_transaction

stripe.api_key = os.getenv("STRIPE_API_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
DOMAIN = "http://localhost:8000" # Update this for production

def create_checkout_session(line_user_id):
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'jpy',
                        'product_data': {
                            'name': 'サムネイル生成クレジット (10回分)',
                        },
                        'unit_amount': 980,
                    },
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=DOMAIN + '/success',
            cancel_url=DOMAIN + '/cancel',
            client_reference_id=line_user_id,
            metadata={
                'line_user_id': line_user_id
            }
        )
        return checkout_session.url
    except Exception as e:
        print(f"Stripe Error: {e}")
        return None

def handle_stripe_webhook(payload, sig_header):
    event = None
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        raise Exception("Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise Exception("Invalid signature")

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        line_user_id = session.get('client_reference_id')
        
        if line_user_id:
            # Add 10 credits
            add_credits(line_user_id, 10)
            record_transaction(session['id'], line_user_id, 980, 10, 'completed')
            print(f"Credits added for user {line_user_id}")
