# Create your views here.
from django.views.generic import TemplateView
from rest_framework import status, permissions
from rest_framework.generics import RetrieveUpdateAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

# from core.forms import FeedbackForm
from core.exceptions import ProfileDoesNotExist
from core.models import Profile, Feedback
from utils.http import _success, _error
from utils.mixpanel import MixPanel, MixPanel_actions
from .renderers import UserJSONRenderer, ProfileJSONRenderer
from .serializers import LoginSerializer, RegistrationSerializer, UserSerializer, ProfileSerializer


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

    def retrieve(self, request, email, *args, **kwargs):
        # Try to retrieve the requested profile and throw an exception if the
        # profile could not be found.
        try:
            # We use the `select_related` method to avoid making unnecessary
            # database calls.
            profile = Profile.objects.select_related('user').get(
                user__email=email
            )
        except Profile.DoesNotExist:
            raise ProfileDoesNotExist

        serializer = self.serializer_class(profile)

        return Response(serializer.data, status=status.HTTP_200_OK)


class LandingView(TemplateView):
    template_name = 'landing.html'


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
