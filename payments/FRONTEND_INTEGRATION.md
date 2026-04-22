# Razorpay Frontend Integration Guide

## Step 1 — Add Razorpay Script to your HTML

```html
<!-- public/index.html -->
<script src="https://checkout.razorpay.com/v1/checkout.js"></script>
```

Or load it dynamically in React:

```js
// utils/loadRazorpay.js
export function loadRazorpay() {
  return new Promise((resolve) => {
    if (window.Razorpay) return resolve(true);
    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
  });
}
```

---

## Step 2 — Fetch Plans (public, no auth needed)

```js
// GET /api/payments/plans/
const res = await fetch('http://localhost:8000/api/payments/plans/');
const plans = await res.json();
// plans = [{ id, name, tier, billing_cycle, price_inr, features, is_popular, ... }]
```

---

## Step 3 — Complete Checkout Flow

```js
// hooks/useRazorpay.js
import { loadRazorpay } from '../utils/loadRazorpay';

export async function initiatePayment({ planId, accessToken }) {
  const loaded = await loadRazorpay();
  if (!loaded) throw new Error('Razorpay SDK failed to load.');

  // 1. Create order on backend
  const orderRes = await fetch('http://localhost:8000/api/payments/create-order/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ plan_id: planId }),
  });

  if (!orderRes.ok) throw new Error('Failed to create order');
  const order = await orderRes.json();

  // 2. Open Razorpay Checkout modal
  return new Promise((resolve, reject) => {
    const rzp = new window.Razorpay({
      key: order.key_id,
      amount: order.amount,
      currency: order.currency,
      name: 'FitnessAI',
      description: order.description,
      order_id: order.order_id,
      prefill: order.prefill,
      theme: { color: order.theme_color },

      handler: async function (response) {
        // 3. Verify payment on backend
        const verifyRes = await fetch('http://localhost:8000/api/payments/verify/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${accessToken}`,
          },
          body: JSON.stringify({
            razorpay_order_id: response.razorpay_order_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature: response.razorpay_signature,
          }),
        });

        if (verifyRes.ok) {
          const data = await verifyRes.json();
          resolve(data); // { success: true, message, subscription }
        } else {
          reject(new Error('Payment verification failed'));
        }
      },

      modal: {
        ondismiss: () => reject(new Error('Payment cancelled')),
      },
    });

    rzp.open();
  });
}
```

---

## Step 4 — Pricing Page Component (React)

```jsx
// pages/Pricing.jsx
import { useState, useEffect } from 'react';
import { initiatePayment } from '../hooks/useRazorpay';

export default function Pricing() {
  const [plans, setPlans] = useState([]);
  const [cycle, setCycle] = useState('monthly'); // 'monthly' | 'yearly'
  const [loading, setLoading] = useState(null);

  useEffect(() => {
    fetch('http://localhost:8000/api/payments/plans/')
      .then(r => r.json())
      .then(setPlans);
  }, []);

  const displayed = plans.filter(p => p.billing_cycle === cycle || p.tier === 'free');

  async function handleBuy(planId) {
    const token = localStorage.getItem('access_token');
    setLoading(planId);
    try {
      const result = await initiatePayment({ planId, accessToken: token });
      alert(result.message); // replace with toast
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(null);
    }
  }

  return (
    <div>
      {/* Billing toggle */}
      <div>
        <button onClick={() => setCycle('monthly')}>Monthly</button>
        <button onClick={() => setCycle('yearly')}>Yearly (Save 25%)</button>
      </div>

      {/* Plan cards */}
      <div style={{ display: 'flex', gap: 24 }}>
        {displayed.map(plan => (
          <div key={plan.id} style={{ border: plan.is_popular ? '2px solid #6366f1' : '1px solid #ccc', padding: 24, borderRadius: 12 }}>
            {plan.is_popular && <span>Most Popular</span>}
            <h2>{plan.name}</h2>
            <p style={{ fontSize: 32, fontWeight: 700 }}>
              {plan.price_inr === 0 ? 'Free' : `₹${plan.price_inr}`}
            </p>
            <p>{plan.description}</p>
            <ul>
              {plan.features.map((f, i) => <li key={i}>✓ {f}</li>)}
            </ul>
            {plan.price_inr === 0 ? (
              <button disabled>Current Plan</button>
            ) : (
              <button onClick={() => handleBuy(plan.id)} disabled={loading === plan.id}>
                {loading === plan.id ? 'Processing...' : 'Get Started'}
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## Step 5 — Check Subscription Status

```js
// On app load — check what plan the user is on
const res = await fetch('http://localhost:8000/api/payments/subscription/', {
  headers: { Authorization: `Bearer ${accessToken}` },
});
const { has_active_subscription, plan, subscription } = await res.json();
// plan.tier = 'free' | 'pro' | 'elite'
// subscription.expires_at = ISO datetime or null (lifetime)
```

---

## Step 6 — Payment History

```js
const res = await fetch('http://localhost:8000/api/payments/history/', {
  headers: { Authorization: `Bearer ${accessToken}` },
});
const history = await res.json();
// [{ razorpay_payment_id, plan_name, billing_cycle, amount_inr, status, created_at }]
```

---

## API Reference

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/payments/plans/` | No | List all plans |
| POST | `/api/payments/create-order/` | Yes | Create Razorpay order |
| POST | `/api/payments/verify/` | Yes | Verify payment & activate sub |
| GET | `/api/payments/subscription/` | Yes | Current subscription status |
| GET | `/api/payments/history/` | Yes | Payment history |
| POST | `/api/payments/webhook/` | No | Razorpay webhook (server-side) |

### POST `/api/payments/create-order/`
**Body:** `{ "plan_id": 2 }`

**Response:**
```json
{
  "order_id": "order_xxxxxxxxxxxx",
  "amount": 99900,
  "currency": "INR",
  "key_id": "rzp_test_xxx",
  "plan": { ... },
  "prefill": { "name": "...", "email": "..." },
  "description": "FitnessAI — Pro Monthly",
  "theme_color": "#6366f1"
}
```

### POST `/api/payments/verify/`
**Body:**
```json
{
  "razorpay_order_id": "order_xxx",
  "razorpay_payment_id": "pay_xxx",
  "razorpay_signature": "signature_xxx"
}
```

---

## Setup — Add Your Razorpay Keys

In `.env`:
```
RAZORPAY_KEY_ID=rzp_test_YOUR_KEY_ID
RAZORPAY_KEY_SECRET=YOUR_KEY_SECRET
RAZORPAY_WEBHOOK_SECRET=YOUR_WEBHOOK_SECRET   # optional, for webhook validation
```

Get keys from: https://dashboard.razorpay.com/app/keys
