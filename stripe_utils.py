import os
import stripe
from database import add_credits, record_transaction

stripe.api_key = os.getenv("STRIPE_API_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
DOMAIN = "http://localhost:8000" # Update this for production

def get_payment_link(line_user_id):
    # Use the static Payment Link provided by the user
    # We append client_reference_id so we know who paid
    base_url = "https://buy.stripe.com/fZu5kC7kK1vJ3CF7HY" # Note: User provided fZu5kC7kK1vJ3CF7HY8AE00 but usually these are shorter or have query params. 
    # Actually, for Payment Links, we pass client_reference_id as a query param.
    # URL: https://buy.stripe.com/fZu5kC7kK1vJ3CF7HY?client_reference_id={line_user_id}
    
    payment_link = "https://buy.stripe.com/fZu5kC7kK1vJ3CF7HY8AE00"
    return f"{payment_link}?client_reference_id={line_user_id}"

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
