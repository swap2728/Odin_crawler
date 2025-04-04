from django.urls import path
from .views import (
    CreateSubscriptionView,
    RazorpayWebhookView,
    SubscriptionStatusView,
    CheckAccessView,
    CrawlView,
    CreateRazorpayOrderView,
    CreateSubscriptionView,
    SubscriptionManagementView
)

urlpatterns = [
    path('api/subscription/create/', CreateSubscriptionView.as_view(), name='create-subscription'),
    path('api/subscription/status/<int:user_id>/', SubscriptionStatusView.as_view(), name='subscription-status'),
    path('verification/', RazorpayWebhookView.as_view(), name='razorpay-webhook'),
    
    # Keep your existing URLs
    path('api/crawl/check-access/', CheckAccessView.as_view(), name='check-access'),
    path('api/crawl/', CrawlView.as_view(), name='crawl'),
    path('api/crawl/create-order/', CreateRazorpayOrderView.as_view(), name='create-order'),
    path('api/crawl/verify-payment/', CreateSubscriptionView.as_view(), name='verify-payment'),
    path('api/crawl/subscription/<int:user_id>/', SubscriptionManagementView.as_view(), name='subscription-management'),
]