import uuid
import logging
import json
from django.utils import timezone
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from dateutil.relativedelta import relativedelta

from .models import Plan, RazorpayOrder, Payment, UserSubscription
from .serializers import (
    PlanSerializer, CreateOrderSerializer, VerifyPaymentSerializer,
    UserSubscriptionSerializer, PaymentHistorySerializer,
)
from . import razorpay_client

logger = logging.getLogger(__name__)


class PlanListView(APIView):
    """GET /api/payments/plans/ — list all active plans (public)."""
    permission_classes = [AllowAny]

    def get(self, request):
        plans = Plan.objects.filter(is_active=True)
        return Response(PlanSerializer(plans, many=True).data)


class CreateOrderView(APIView):
    """POST /api/payments/create-order/ — create Razorpay order for a plan."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan = Plan.objects.get(id=serializer.validated_data['plan_id'])
        receipt = f"rcpt_{request.user.id}_{uuid.uuid4().hex[:10]}"

        try:
            rz_order = razorpay_client.create_order(
                amount_paise=plan.price_paise,
                currency='INR',
                receipt=receipt,
                notes={
                    'user_id': str(request.user.id),
                    'user_email': request.user.email,
                    'plan_name': plan.name,
                },
            )
        except Exception as e:
            logger.error(f"Razorpay order creation failed: {e}")
            return Response(
                {'error': 'Payment gateway error. Please try again.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        RazorpayOrder.objects.create(
            user=request.user,
            plan=plan,
            razorpay_order_id=rz_order['id'],
            amount_paise=plan.price_paise,
            receipt=receipt,
            status='created',
        )

        return Response({
            'order_id': rz_order['id'],
            'amount': plan.price_paise,
            'currency': 'INR',
            'key_id': settings.RAZORPAY_KEY_ID,
            'plan': PlanSerializer(plan).data,
            'prefill': {
                'name': request.user.get_full_name() or request.user.username,
                'email': request.user.email,
            },
            'description': f"FitnessAI — {plan.name}",
            'theme_color': '#6366f1',
        })


class VerifyPaymentView(APIView):
    """POST /api/payments/verify/ — verify signature and activate subscription."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = VerifyPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        rz_order_id = data['razorpay_order_id']
        rz_payment_id = data['razorpay_payment_id']
        rz_signature = data['razorpay_signature']

        try:
            order = RazorpayOrder.objects.get(
                razorpay_order_id=rz_order_id,
                user=request.user,
            )
        except RazorpayOrder.DoesNotExist:
            return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

        if order.status == 'paid':
            return Response({'error': 'Order already processed.'}, status=status.HTTP_400_BAD_REQUEST)

        # Verify signature
        valid = razorpay_client.verify_payment_signature(rz_order_id, rz_payment_id, rz_signature)
        if not valid:
            order.status = 'failed'
            order.save()
            return Response({'error': 'Invalid payment signature.'}, status=status.HTTP_400_BAD_REQUEST)

        order.status = 'paid'
        order.save()

        payment = Payment.objects.create(
            order=order,
            user=request.user,
            razorpay_payment_id=rz_payment_id,
            razorpay_signature=rz_signature,
            status='captured',
        )

        # Deactivate any existing active subscriptions
        UserSubscription.objects.filter(user=request.user, status='active').update(status='cancelled')

        # Calculate expiry
        now = timezone.now()
        plan = order.plan
        if plan.billing_cycle == 'monthly':
            expires_at = now + relativedelta(months=1)
        elif plan.billing_cycle == 'yearly':
            expires_at = now + relativedelta(years=1)
        else:
            expires_at = None  # lifetime

        subscription = UserSubscription.objects.create(
            user=request.user,
            plan=plan,
            payment=payment,
            status='active',
            starts_at=now,
            expires_at=expires_at,
        )

        return Response({
            'success': True,
            'message': f'Payment verified. {plan.name} activated!',
            'subscription': UserSubscriptionSerializer(subscription).data,
        }, status=status.HTTP_201_CREATED)


class SubscriptionStatusView(APIView):
    """GET /api/payments/subscription/ — current user's active subscription."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sub = (
            UserSubscription.objects
            .filter(user=request.user, status='active')
            .select_related('plan')
            .order_by('-created_at')
            .first()
        )

        if not sub or not sub.is_valid:
            # Return free plan info
            free_plan = Plan.objects.filter(tier='free').first()
            return Response({
                'has_active_subscription': False,
                'plan': PlanSerializer(free_plan).data if free_plan else None,
                'subscription': None,
            })

        return Response({
            'has_active_subscription': True,
            'plan': PlanSerializer(sub.plan).data,
            'subscription': UserSubscriptionSerializer(sub).data,
        })


class PaymentHistoryView(APIView):
    """GET /api/payments/history/ — user's payment history."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payments = (
            Payment.objects
            .filter(user=request.user)
            .select_related('order__plan')
            .order_by('-created_at')
        )
        return Response(PaymentHistorySerializer(payments, many=True).data)


@method_decorator(csrf_exempt, name='dispatch')
class RazorpayWebhookView(APIView):
    """POST /api/payments/webhook/ — Razorpay webhook handler."""
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        webhook_secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', '')
        signature = request.headers.get('X-Razorpay-Signature', '')

        if webhook_secret and signature:
            valid = razorpay_client.verify_webhook_signature(
                request.body, signature, webhook_secret
            )
            if not valid:
                return Response({'error': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return Response({'error': 'Invalid JSON'}, status=status.HTTP_400_BAD_REQUEST)

        event = payload.get('event')

        if event == 'payment.failed':
            payment_entity = payload.get('payload', {}).get('payment', {}).get('entity', {})
            order_id = payment_entity.get('order_id')
            try:
                order = RazorpayOrder.objects.get(razorpay_order_id=order_id)
                order.status = 'failed'
                order.save()
            except RazorpayOrder.DoesNotExist:
                pass

        return Response({'status': 'ok'})
