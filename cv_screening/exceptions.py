from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import Throttled


def custom_exception_handler(exc, context):
    """
    Custom exception handler to provide better error responses,
    especially for throttled requests.
    """
    response = exception_handler(exc, context)
    
    if isinstance(exc, Throttled):
        # Customize throttle exception response
        custom_response_data = {
            'status': 'error',
            'type': 'rate_limit_exceeded',
            'message': exc.detail,
            'retry_after': exc.wait(),
        }
        
        return Response(
            custom_response_data,
            status=status.HTTP_429_TOO_MANY_REQUESTS,
            headers={'Retry-After': str(exc.wait())}
        )
    
    if response is not None:
        # Standardize all error responses
        if 'detail' in response.data:
            response.data = {
                'status': 'error',
                'message': str(response.data['detail']),
                'code': response.status_code,
            }
    
    return response
