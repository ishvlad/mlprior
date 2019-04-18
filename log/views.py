from django.http import JsonResponse
from .models import LogModel

def request_testcase(request):
    return JsonResponse({})


def exception_testcase(request):
    raise Exception


def logging(request):
    # if request.method != 'POST':
    #     return

    # MODES = (
    #     (0, 'other'),
    #     (1, 'append'),
    #     (2, 'change'),
    #     (3, 'delete'),
    #     (4, 'move')
    # )

    entry = LogModel()
    entry.user = request.user
    entry.source_url = request.POST.get('source_url')
    entry.action = request.POST.get('action')
    entry.args = request.POST.get('args')
    entry.save()

    print('inside!!')
