from requests import Response


def _error(error):
    return Response({
        'success': False,
        'error': error
    })


def _success():
    return Response({
        'success': True
    })
