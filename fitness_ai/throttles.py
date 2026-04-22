from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class AIEndpointUserThrottle(UserRateThrottle):
    scope = 'ai_endpoint'


class AIEndpointAnonThrottle(AnonRateThrottle):
    scope = 'ai_endpoint'
