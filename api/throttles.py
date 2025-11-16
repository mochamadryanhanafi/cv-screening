from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class UploadThrottle(UserRateThrottle):
    """Rate limiting for file uploads (scope: 'upload')."""
    scope = 'upload'


class EvaluateThrottle(UserRateThrottle):
    """Rate limiting for evaluation requests (scope: 'evaluate')."""
    scope = 'evaluate'


class ResultThrottle(UserRateThrottle):
    """Rate limiting for checking evaluation results (scope: 'result')."""
    scope = 'result'


class TokenObtainThrottle(AnonRateThrottle):
    """Rate limiting for token generation (scope: 'token_obtain')."""
    scope = 'token_obtain'


class AdminThrottle(UserRateThrottle):
    """Rate limiting for admin endpoints (scope: 'admin')."""
    scope = 'admin'


class DefaultThrottle(UserRateThrottle):
    """Default rate limiting for authenticated endpoints (scope: 'default')."""
    scope = 'default'


class AnonDefaultThrottle(AnonRateThrottle):
    """Default rate limiting for anonymous endpoints (scope: 'anon')."""
    scope = 'anon'
