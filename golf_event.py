import os
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
import stripe
import requests

load_dotenv()

app = Flask(__name__, static_folder='.', static_url_path='')

# Stripe config
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
stripe.api_key = STRIPE_SECRET_KEY

# PayPal config
PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID')
PAYPAL_SECRET = os.getenv('PAYPAL_SECRET')
PAYPAL_API_BASE = 'https://api-m.sandbox.paypal.com'  # Use sandbox for testing

def get_paypal_access_token():
    auth = (PAYPAL_CLIENT_ID, PAYPAL_SECRET)
    headers = {'Accept': 'application/json', 'Accept-Language': 'en_US'}
    data = {'grant_type': 'client_credentials'}
    resp = requests.post(f'{PAYPAL_API_BASE}/v1/oauth2/token', headers=headers, data=data, auth=auth)
    resp.raise_for_status()
    return resp.json()['access_token']

@app.route('/create-stripe-payment-intent', methods=['POST'])
def create_stripe_payment_intent():
    data = request.json
    try:
        intent = stripe.PaymentIntent.create(
            amount=int(float(data['amount']) * 100),  # amount in cents
            currency='usd',
            payment_method_types=['card'],
            description='Website Payment',
        )
        return jsonify({'clientSecret': intent['client_secret']})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/create-paypal-order', methods=['POST'])
def create_paypal_order():
    data = request.json
    access_token = get_paypal_access_token()
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    order_data = {
        'intent': 'CAPTURE',
        'purchase_units': [{
            'amount': {
                'currency_code': 'USD',
                'value': str(data['amount'])
            }
        }]
    }
    resp = requests.post(f'{PAYPAL_API_BASE}/v2/checkout/orders', headers=headers, json=order_data)
    if resp.status_code != 201:
        return jsonify({'error': resp.text}), 400
    return jsonify(resp.json())

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/')
def root():
    return send_from_directory('.', 'houses.html')

if __name__ == '__main__':
    app.run(debug=True)