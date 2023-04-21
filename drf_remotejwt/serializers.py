from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class PasswordField(serializers.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('style', {})

        kwargs['style']['input_type'] = 'password'
        kwargs['write_only'] = True

        super().__init__(*args, **kwargs)


class TokenObtainSerializer(serializers.Serializer):
    username_field = get_user_model().USERNAME_FIELD

    default_error_messages = {
        'no_active_account': 'No active account found with the given \
            credentials'
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields[self.username_field] = serializers.CharField()
        self.fields['password'] = PasswordField()

    def validate(self, attrs):
        authenticate_kwargs = {
            self.username_field: attrs[self.username_field],
            'password': attrs['password'],
        }
        try:
            authenticate_kwargs['request'] = self.context['request']
        except KeyError:
            pass

        return authenticate_kwargs


class TokenObtainPairSerializer(TokenObtainSerializer):

    def validate(self, attrs):
        return super().validate(attrs)


class TokenRefreshSerializer(serializers.Serializer):
    # There is technically no JWT length limit.
    refresh = serializers.CharField(max_length=255)


class TokenVerifySerializer(serializers.Serializer):
    # There is technically no JWT length limit.
    token = serializers.CharField(max_length=255)