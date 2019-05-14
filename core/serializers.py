from rest_framework import serializers

from core.models import User


class UserSerializer(serializers.ModelSerializer):
    # blogposts = serializers.HyperlinkedIdentityField(view_name='userpost-list', lookup_field='username')

    class Meta:
        model = User
        fields = ['id']
