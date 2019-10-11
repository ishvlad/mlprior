# Create your views here.
import datetime

from django.views.generic import TemplateView
from rest_framework import status, permissions
from rest_framework.generics import RetrieveUpdateAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import FileUploadParser
from rest_framework.response import Response
from rest_framework.views import APIView

# from core.forms import FeedbackForm
from core.exceptions import ProfileDoesNotExist
from core.models import Profile, Feedback, PremiumSubscription, RequestDemo
from utils.http import _success, _error
from utils.mixpanel import MixPanel, MixPanel_actions
from .renderers import UserJSONRenderer, ProfileJSONRenderer
from .serializers import LoginSerializer, RegistrationSerializer, UserSerializer, ProfileSerializer, \
    SubscriptionSerializer, FileSerializer


class RegistrationAPIView(APIView):
    # Allow any user (authenticated or not) to hit this endpoint.
    permission_classes = (AllowAny,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = RegistrationSerializer

    def post(self, request):
        user = request.data.get('user', {})

        # The create serializer, validate serializer, save serializer pattern
        # below is common and you will see it a lot throughout this course and
        # your own work later on. Get familiar with it.
        serializer = self.serializer_class(data=user)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LoginAPIView(APIView):
    permission_classes = (AllowAny,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = LoginSerializer

    def post(self, request):
        user = request.data.get('user', {})

        # Notice here that we do not call `serializer.save()` like we did for
        # the registration endpoint. This is because we don't  have
        # anything to save. Instead, the `validate` method on our serializer
        # handles everything we need.
        serializer = self.serializer_class(data=user)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class UserRetrieveUpdateAPIView(RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = UserSerializer

    def retrieve(self, request, *args, **kwargs):
        # There is nothing to validate or save here. Instead, we just want the
        # serializer to handle turning our `User` object into something that
        # can be JSONified and sent to the client.
        serializer = self.serializer_class(request.user)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):

        user_data = request.data.get('user', {})

        serializer_data = {
            'email': user_data.get('email', request.user.email),

            'profile': {
                'first_name': user_data.get('first_name', request.user.profile.first_name),
                'second_name': user_data.get('second_name', request.user.profile.second_name),
            }
        }

        # Here is that serialize, validate, save pattern we talked about
        # before.
        serializer = self.serializer_class(
            request.user, data=serializer_data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)


class ProfileRetrieveAPIView(RetrieveAPIView):
    permission_classes = (AllowAny,)
    renderer_classes = (ProfileJSONRenderer,)
    serializer_class = ProfileSerializer

    def retrieve(self, request, *args, **kwargs):
        if request.user.is_anonymous:
            return _error('The user should be logged in')

        serializer = self.serializer_class(request.user.profile)

        return Response(serializer.data, status=status.HTTP_200_OK)


class SubscriptionAPI(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = SubscriptionSerializer

    def get(self, request):
        if request.user.is_anonymous:
            return _error('The user should be logged in')

        if not request.user.subscription:
            return Response({
                'premium': False,
            })

        return Response({
            'premium': True,
            'endDate': request.user.subscription.end_date,
            'dailyMail': request.user.subscription.is_daily_mail,
            'weeklyMail': request.user.subscription.is_weekly_mail,
        })

    def put(self, request):
        print(request.data)
        if request.user.is_anonymous:
            return _error('The user should be logged in')

        if not request.user.subscription:
            return _error('There is no subscription')

        subscription = PremiumSubscription.objects.get(user=request.user)
        subscription.is_daily_mail = request.data.get('dailyMail')
        subscription.is_weekly_mail = request.data.get('weeklyMail')

        subscription.save()

        return _success()

    def post(self, request):
        if request.user.is_anonymous:
            return _error('The user should be logged in')

        start_date = datetime.date.today()

        subscription, is_created = PremiumSubscription.objects.get_or_create(user=request.user)

        subscription.is_active = True
        subscription.is_trial = True
        subscription.start_date = start_date
        subscription.end_date = start_date + datetime.timedelta(days=14)

        subscription.save()

        return _success()


class MixPanelAPI(APIView):
    permission_classes = [
        permissions.AllowAny
    ]

    def post(self, request):
        mp = MixPanel(request.user)

        action = request.data.get('action', None)
        if action is None:
            return Response(status=400, data={
                "info": "ERROR",
                "message": "Action could not be None"
            })

        valid_actions = [v for k, v in MixPanel_actions.__dict__.items() if not k.startswith('__')]
        if action not in valid_actions:
            return Response(status=400, data={
                "info": "ERROR",
                "message": "Action is not valid"
            })

        properties = request.data
        del properties['action']

        if len(properties) == 0:
            mp.track(action)
        else:
            mp.track(action, properties)

        return _success()


class FeedbackAPI(APIView):
    permission_classes = [
        permissions.AllowAny
    ]

    def post(self, request):
        # read params
        type = request.data.get('type', 0)
        name = request.data.get('name', None)
        email = request.data.get('email', None)
        message = request.data.get('message', None)

        if name is None or email is None or message is None or int(type) < 0 or int(type) > 2:
            return Response(status=400, data={
                "info": "ERROR",
                "Parameter docstring": {
                    'name': {'type': 'string', 'max_length': '1000', 'desc': 'Person name'},
                    'email': {'type': 'string', 'max_length': '1000',
                              'desc': 'Person email (without checking from API side)'},
                    'message': {'type': 'string', 'max_length': '10000', 'desc': 'message'},
                    'type': {'type': 'integer', 'valid values': {
                        0: 'other',
                        1: 'from subscribe form',
                        2: 'from feature request form'
                    }}
                },
                'example': "http://mlprior.com/api/feedback?type=0&name=user_name&email=user_email&message=Please continue"
            })
        else:
            type = int(type)

        mp = MixPanel(request.user)
        mp.track(MixPanel_actions.feedback, {'type': type})

        # save to DB
        item = Feedback(type=type, name=name, email=email, message=message)
        item.save()

        return _success()


class RequestDemoAPI(APIView):
    permission_classes = [
        permissions.AllowAny
    ]

    def post(self, request):
        # 1 -- from landing page
        source = request.data.get('source', 0)
        name = request.data.get('name', None)
        email = request.data.get('email', None)
        message = request.data.get('message', None)

        # 1 -- Not cited
        # 2 -- Formulas
        # 3 -- Skipped parts
        # 4 -- Fit to a conference
        # 5 -- Acceptance prediction
        feature = request.data.get('feature', 0)

        if name is None or email is None or int(source) < 0 or int(feature) < 0:
            example = "https://mlprior.com/api/requestdemo?"
            example += "source=0&name=user_name&email=user_email&message=I want to buy&feature=0"
            return Response(status=400, data={'example': example})
        else:
            source = int(source)
            feature = int(feature)

        if message is None:
            message = ""

        mp = MixPanel(request.user)
        mp.track(MixPanel_actions.request_demo, {'source': source, 'feature': feature})

        # save to DB
        item = RequestDemo(source=source, name=name, email=email, message=message, feature=feature)
        item.save()

        return _success()


class FileUploadView(APIView):

    def post(self, request, *args, **kwargs):
        file_serializer = FileSerializer(data=request.data)

        if file_serializer.is_valid():
            file_serializer.save()
            return Response(file_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
