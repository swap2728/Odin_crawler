from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import UserSubscription
import json
import requests

@csrf_exempt
def paypal_webhook(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    
    headers = request.headers
    body = request.body.decode('utf-8')
    body_json = json.loads(body)

    # Step 1: Verify webhook signature via PayPal API
    verification_url = "https://api-m.paypal.com/v1/notifications/verify-webhook-signature"

    verify_payload = {
        "auth_algo": headers.get('PAYPAL-AUTH-ALGO'),
        "cert_url": headers.get('PAYPAL-CERT-URL'),
        "transmission_id": headers.get('PAYPAL-TRANSMISSION-ID'),
        "transmission_sig": headers.get('PAYPAL-TRANSMISSION-SIG'),
        "transmission_time": headers.get('PAYPAL-TRANSMISSION-TIME'),
        "webhook_id": settings.PAYPAL_WEBHOOK_ID,
        "webhook_event": body_json
    }

    # Get access token
    auth_response = requests.post(
        "https://api-m.paypal.com/v1/oauth2/token",
        headers={"Accept": "application/json"},
        data={"grant_type": "client_credentials"},
        auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET)
    )

    if auth_response.status_code != 200:
        return JsonResponse({'status': 'error', 'message': 'Failed to get PayPal access token'}, status=500)

    access_token = auth_response.json().get('access_token')

    # Verify signature
    verify_response = requests.post(
        verification_url,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        },
        json=verify_payload
    )

    if verify_response.status_code != 200 or verify_response.json().get('verification_status') != 'SUCCESS':
        return JsonResponse({'status': 'error', 'message': 'Invalid webhook signature'}, status=400)

    # Step 2: Process the event
    event_type = body_json.get('event_type')
    resource = body_json.get('resource', {})
    subscription_id = resource.get('id')

    if not subscription_id:
        return JsonResponse({'status': 'error', 'message': 'No subscription ID'}, status=400)

    try:
        user_sub = UserSubscription.objects.get(subscription_id=subscription_id)

        # 🔥 Prevent trial from resetting active subscription
        if event_type == 'BILLING.SUBSCRIPTION.TRIAL_STARTED' and user_sub.status == 'active':
            return JsonResponse({'status': 'ignored', 'message': 'Ignoring trial start for active subscription'})

        if event_type in ['BILLING.SUBSCRIPTION.ACTIVATED', 'BILLING.SUBSCRIPTION.CREATED']:
            user_sub.status = 'active'
        elif event_type in ['BILLING.SUBSCRIPTION.CANCELLED', 'BILLING.SUBSCRIPTION.EXPIRED']:
            user_sub.status = 'cancelled' if event_type == 'BILLING.SUBSCRIPTION.CANCELLED' else 'expired'
        elif event_type == 'BILLING.SUBSCRIPTION.TRIAL_STARTED':
            user_sub.status = 'trial'

        user_sub.save()
        return JsonResponse({'status': 'success'})

    except UserSubscription.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Subscription not found'}, status=404)
