from decimal import Decimal
import razorpay
import json
import logging
import requests
import hashlib
import hmac

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone
from django.conf import settings
from rest_framework.views import APIView

from .models import UserSubscription
from .scraper import scrape_page_content, search_web

logger = logging.getLogger(__name__)

# -------------------------------
# ✅ Razorpay Service
# -------------------------------
class RazorpayService:
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    @staticmethod
    def verify_payment(payment_id, order_id, signature):
        try:
            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            RazorpayService.client.utility.verify_payment_signature(params_dict)
            return True
        except razorpay.errors.SignatureVerificationError:
            return False

    @staticmethod
    def create_subscription(user_id, email):
        try:
            subscription = RazorpayService.client.subscription.create({
                "plan_id": settings.RAZORPAY_PLAN_ID,
                "total_count": 12,  # 1 year subscription
                "customer_notify": 1,
                "notes": {
                    "user_id": user_id,
                    "email": email
                }
            })
            return subscription
        except Exception as e:
            logger.error(f"Subscription creation failed: {str(e)}")
            raise

# -------------------------------
# ✅ Webhook Handler
# -------------------------------
@method_decorator(csrf_exempt, name='dispatch')
class RazorpayWebhookView(View):
    def post(self, request, *args, **kwargs):
        try:
            payload = request.body.decode('utf-8')
            received_signature = request.headers.get('X-Razorpay-Signature')
            
            expected_signature = hmac.new(
                key=settings.RAZORPAY_WEBHOOK_SECRET.encode('utf-8'),
                msg=payload.encode('utf-8'),
                digestmod=hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(received_signature, expected_signature):
                logger.error("Webhook signature verification failed")
                return JsonResponse({'status': 'error', 'message': 'Invalid signature'}, status=400)

            event = json.loads(payload)
            logger.info(f"Webhook event: {event.get('event')}")

            # Handle subscription events
            if event.get('event') in ['subscription.charged', 'payment.captured']:
                payment = event.get('payload', {}).get('payment', {}).get('entity', {})
                subscription_id = payment.get('subscription_id')
                user_id = payment.get('notes', {}).get('user_id')
                
                if user_id and subscription_id:
                    try:
                        user_sub = UserSubscription.objects.get(user_id=user_id)
                        user_sub.status = 'active'
                        user_sub.subscription_id = subscription_id
                        user_sub.save()
                        logger.info(f"Subscription activated for user {user_id}")
                    except UserSubscription.DoesNotExist:
                        logger.error(f"User subscription not found for user_id: {user_id}")
                        # Create new subscription if not exists
                        UserSubscription.objects.create(
                            user_id=user_id,
                            status='active',
                            subscription_id=subscription_id,
                            trial_end=timezone.now() + timezone.timedelta(days=365)
                        )
            
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

# -------------------------------
# ✅ Subscription Views
# -------------------------------
@method_decorator(csrf_exempt, name='dispatch')
class CreateSubscriptionView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body.decode("utf-8"))
            user_id = data.get("user_id")
            email = data.get("email", "user@odin.com")
            
            if not user_id:
                return JsonResponse({'success': False, 'message': 'User ID required'}, status=400)

            subscription = RazorpayService.create_subscription(user_id, email)
            
            return JsonResponse({
                'success': True,
                'subscription_id': subscription.get('id'),
                'status': subscription.get('status'),
                'subscription_link': settings.RAZORPAY_SUBSCRIPTION_LINK,
                'redirect_url': f"{settings.RAZORPAY_SUBSCRIPTION_LINK}?subscription_id={subscription.get('id')}"
            })

        except Exception as e:
            logger.error(f"Subscription error: {str(e)}")
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class SubscriptionStatusView(APIView):
    def get(self, request, user_id):
        try:
            sub = UserSubscription.objects.get(user_id=user_id)
            return JsonResponse({
                'status': sub.status,
                'subscription_id': sub.subscription_id,
                'is_active': sub.is_valid(),
                'trial_end': sub.trial_end.isoformat() if sub.trial_end else None
            })
        except UserSubscription.DoesNotExist:
            return JsonResponse({'error': 'No subscription found'}, status=404)

# ... [Keep all your existing views like CheckAccessView, CrawlView, etc.] ...

# -------------------------------
# ✅ Check Access View (Updated)
# -------------------------------
@method_decorator(csrf_exempt, name='dispatch')
class CheckAccessView(View):
    def get(self, request, *args, **kwargs):
        try:
            user_id = int(request.GET.get('user_id'))
        except (TypeError, ValueError):
            return JsonResponse({'access': False, 'reason': 'Invalid user_id'}, status=400)

        try:
            # Set default trial_end for new users
            user_sub, created = UserSubscription.objects.get_or_create(
                user_id=user_id,
                defaults={
                    'status': 'trial',
                    'trial_end': timezone.now() + timezone.timedelta(days=3)
                }
            )

            # Check if trial has expired
            if user_sub.status == 'trial' and user_sub.trial_end < timezone.now():
                user_sub.status = 'expired'
                user_sub.save()
                return JsonResponse({
                    'access': False,
                    'is_trial': False,
                    'reason': 'trial_expired',
                    'message': 'Your trial has expired. Please subscribe to continue.'
                })

            if user_sub.is_valid():
                return JsonResponse({
                    'access': True,
                    'is_trial': user_sub.status == 'trial',
                    'trial_ends': user_sub.trial_end.isoformat() if user_sub.status == 'trial' else None,
                    'status': user_sub.status
                })

            return JsonResponse({
                'access': False,
                'reason': 'subscription_required',
                'message': 'Please subscribe to access Odin Crawler'
            })

        except Exception as e:
            logger.error(f"Error in CheckAccessView: {str(e)}")
            return JsonResponse({'access': False, 'reason': 'internal_error'}, status=500)
# -------------------------------
# ✅ Subscription Management View
# -------------------------------
@method_decorator(csrf_exempt, name='dispatch')
class SubscriptionManagementView(APIView):
    def get(self, request, user_id):
        try:
            sub = UserSubscription.objects.get(user_id=user_id)
            return JsonResponse({
                'status': sub.status,
                'plan': 'premium',
                'start_date': sub.created_at.isoformat(),
                'trial_end': sub.trial_end.isoformat() if sub.status == 'trial' else None,
                'is_active': sub.is_valid()
            })
        except UserSubscription.DoesNotExist:
            return JsonResponse({'error': 'No subscription found'}, status=404)

# -------------------------------
# ✅ CrawlView with Trial Enforcement
# -------------------------------
@method_decorator(csrf_exempt, name='dispatch')
class CrawlView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body.decode("utf-8"))
            user_id = data.get("user_id")
            if not user_id:
                return JsonResponse({"status": "error", "error": "Missing user_id"}, status=400)

            try:
                user_sub = UserSubscription.objects.get(user_id=int(user_id))
            except UserSubscription.DoesNotExist:
                return JsonResponse({"status": "error", "error": "User not registered"}, status=400)
            
            if not user_sub.is_valid():
                return JsonResponse({
                    "status": "error", 
                    "error": "Trial expired or no valid subscription.",
                    "requires_payment": True
                }, status=403)

            if "keyword" in data and data["keyword"].strip():
                keyword = data["keyword"].strip()
                links = search_web(keyword)

                # Apply limits based on subscription status
                if user_sub.status == 'trial':
                    extracted_data = {"links": links[:20]}  # Trial limit
                else:
                    extracted_data = {"links": links}       # Full access

                title = f"Results for keyword: {keyword}"

            elif "url" in data and data["url"].strip():
                url = data["url"].strip()
                extracted_data = scrape_page_content(url)
                title = f"Results for URL: {url}"

            else:
                return JsonResponse({
                    "status": "error", 
                    "error": "Please provide a keyword or URL."
                }, status=400)

            if not extracted_data:
                return JsonResponse({
                    "status": "error", 
                    "error": "No data extracted."
                }, status=400)

            return JsonResponse({
                "status": "success", 
                "title": title, 
                **extracted_data
            }, status=200)

        except json.JSONDecodeError as e:
            logger.error("JSON Decode Error: %s", str(e))
            return JsonResponse({
                "status": "error", 
                "error": "Invalid JSON format"
            }, status=400)
        except Exception as e:
            logger.error("Unexpected Error: %s", str(e))
            return JsonResponse({
                "status": "error", 
                "error": str(e)
            }, status=500)
        
@method_decorator(csrf_exempt, name='dispatch')
class CreateRazorpayOrderView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body.decode("utf-8"))
            user_id = data.get("user_id")
            amount = data.get("amount", 0.012)  # Default amount ₹1
            
            if not user_id:
                return JsonResponse({'success': False, 'message': 'User ID required'}, status=400)

            # Create Razorpay order
            order = RazorpayService.client.order.create({
                'amount': int(float(amount) * 100),  # Convert to paise
                'currency': 'INR',
                'receipt': f'order_{user_id}_{int(time.time())}',
                'notes': {
                    'user_id': user_id
                }
            })

            return JsonResponse({
                'success': True,
                'order_id': order.get('id'),
                'amount': order.get('amount'),
                'currency': order.get('currency'),
                'key': settings.RAZORPAY_KEY_ID
            })

        except Exception as e:
            logger.error(f"Order creation error: {str(e)}")
            return JsonResponse({'success': False, 'message': str(e)}, status=500)        