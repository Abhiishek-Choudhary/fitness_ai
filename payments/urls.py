from django.urls import path
from .views import (
    PlanListView,
    CreateOrderView,
    VerifyPaymentView,
    SubscriptionStatusView,
    PaymentHistoryView,
    RazorpayWebhookView,
)

urlpatterns = [
    path('plans/', PlanListView.as_view(), name='plan-list'),
    path('create-order/', CreateOrderView.as_view(), name='create-order'),
    path('verify/', VerifyPaymentView.as_view(), name='verify-payment'),
    path('subscription/', SubscriptionStatusView.as_view(), name='subscription-status'),
    path('history/', PaymentHistoryView.as_view(), name='payment-history'),
    path('webhook/', RazorpayWebhookView.as_view(), name='razorpay-webhook'),
]
