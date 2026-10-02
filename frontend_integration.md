# Frontend Integration Notes

Backend security hardening changed some API behaviour. This lists only what the
frontend has to react to. Base URL stays `https://fitness-ai-qa9m.onrender.com`.

## 1. Authentication is now required by default

DRF previously defaulted to `AllowAny`, so any endpoint that forgot to declare
permissions was public. The default is now `IsAuthenticated`. Endpoints that
changed from public to authenticated:

| Method | Endpoint | Notes |
|---|---|---|
| POST | `/api/calories/estimate/` | Food photo calorie estimate |
| POST | `/posture/pushup/upload/` | Push-up image upload |
| POST | `/posture/analyze/<session_id>/` | Posture analysis |
| POST | `/workout/api/enriched-workout/` | Workout plan enrichment |
| GET | `/api/gyms/<id>/members/` | Gym member list |
| GET | `/api/gyms/<id>/campaigns/list/` | Now **gym owner only** — returns an empty list for everyone else |

Send the access token on all of these:

```
Authorization: Bearer <access_token>
```

A missing or expired token returns `401` with `{"detail": "..."}`. If you have a
screen that called any of the above anonymously (for example a calorie demo
before login), it must now sit behind the login gate or prompt for sign-in.

### Still public

No token needed, unchanged:

- `POST /api/accounts/signup/`, `POST /api/accounts/login/`, `POST /api/accounts/token/refresh/`
- `GET /api/gyms/`, `GET /api/gyms/nearby/`, `GET /api/gyms/<id>/`
- `GET /api/payments/plans/`
- `GET` on the feed: `/api/feed/`, `/api/feed/trending/`, `/api/feed/categories/`,
  `/api/feed/creators/<username>/`, `/api/feed/posts/`, `/api/feed/posts/<id>/`,
  `/api/feed/posts/<id>/comments/`
- `GET` on community: `/api/community/activity-types/`, `/api/community/events/`,
  `/api/community/events/<id>/`, `/api/community/events/<id>/attendees/`,
  `/api/community/groups/`, `/api/community/groups/<id>/`,
  `/api/community/groups/<id>/members/`

On the feed and community routes it is only the reads that are public — `POST`,
`PATCH` and `DELETE` on the same paths still need a token, as do all of the
`mine/`, `saved/`, `following/`, `connections/` and `location/` routes.

## 2. `email` removed from user objects

User emails were being exposed to anyone who could read a gym. The nested user
object no longer includes `email`. Affected responses:

- `GET /api/gyms/<id>/` → `owner`
- `GET /api/gyms/<id>/members/` → `user`
- `GET /api/gyms/<id>/conversations/` → `user`

Before:

```json
{ "id": 4, "username": "rahul", "email": "rahul@example.com", "name": "Rahul S" }
```

After:

```json
{ "id": 4, "username": "rahul", "name": "Rahul S" }
```

Use `name` (falls back to `username`) for display. If you need a gym's public
contact address, read the gym's own `email` field rather than `owner.email` —
that one is intended to be public and is unchanged.

## 3. AI error responses are now generic

AI endpoints used to return the raw exception text, which leaked internals and
was not user-presentable. They now return a fixed message with the same `500`
status, for example:

```json
{ "error": "Could not analyse that photo. Please try again." }
```

Show the `error` string directly — it is now safe and user-facing. Don't try to
pattern-match on it; the wording may change. Report-generation failures
similarly return a neutral sentence instead of an exception string in the report
body.

## 4. No change needed, but worth knowing

- **Token lifetimes** are unchanged: access 60 min, refresh 1 day, rotation with
  blacklist. Keep refreshing via `/api/accounts/token/refresh/`.
- **CORS** is unchanged. `localhost:3000`, `localhost:5173`, and any
  `https://fitness-frontend-*.vercel.app` origin are allowed, with credentials.
- **HTTPS redirect and HSTS** are now on in production. Always call `https://`
  URLs; an `http://` call gets a redirect, which turns a POST into a wasted
  round trip.
- **Pagination** is unchanged (`PAGE_SIZE` 20) on endpoints that already paginated.
  `/api/gyms/` still returns an unpaginated `{count, results}` object.

## 5. AI endpoints can take longer and fail differently

AI calls now fall back across backends (extra Gemini keys, then an OmniRoute
gateway if one is configured) when a backend is out of quota or overloaded. The
request contract is unchanged, but the timing profile is not.

- **Raise client timeouts to at least 90s** on `POST /api/calories/estimate/`,
  `POST /api/fitness/ai-plan/`, `POST /api/fitness/ai-plan/regenerate/`,
  `POST /posture/analyze/<session_id>/`, `POST /workout/api/enriched-workout/`
  and `POST /api/reports/generate/`. A normal call is a few seconds; a call that
  falls through backends is additive. A 30s timeout will now abort requests that
  would have succeeded.
- **Show a progress state, not a spinner with no text.** These are the slowest
  calls in the product. "Building your plan…" beats an indefinite spinner.
- **Quality varies between calls.** A fallback backend may return a shorter or
  less detailed plan for identical input. Don't cache a plan assuming it is
  reproducible, and don't diff two responses to detect "changes".
- Posture feedback already degrades gracefully: if every AI backend fails it
  returns solid rule-based coaching text instead of an error, so treat a `200`
  as success without checking for AI-specific markers.

When every backend is exhausted you still get `500` with the same generic shape
as section 3 — `{"error": "..."}`. Display the `error` string and offer a retry;
a retry minutes later often succeeds because quotas are windowed.

## 6. Content feed now returns real videos

`YOUTUBE_API_KEY` is configured, so `/api/feed/` endpoints that were returning
empty result sets will now return populated YouTube content. If any UI has an
"empty feed" placeholder that was effectively permanent, it will stop appearing —
make sure the populated state renders correctly, including thumbnails.

## Checklist

- [ ] Attach `Authorization: Bearer` to the six endpoints in section 1
- [ ] Remove any UI that reads `owner.email` / `user.email` from gym responses
- [ ] Confirm anonymous users can no longer reach the calorie/posture/workout AI screens
- [ ] Verify all API base URLs use `https://`
- [ ] Raise AI endpoint timeouts to 90s and add progress copy
- [ ] Check the feed renders correctly now that it returns real videos
