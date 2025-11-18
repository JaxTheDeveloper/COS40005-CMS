from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model


class TokenObtainPairCompatView(APIView):
    permission_classes = [AllowAny]
    """Compatibility endpoint: accepts 'username' or 'email' and returns JWT tokens.

    Our User model uses email as USERNAME_FIELD. This view allows clients that still
    send 'username' (legacy) to authenticate by mapping username -> email.
    """

    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        # If client sent 'username' but not 'email', try to map it.
        if 'username' in data and 'email' not in data:
            username = data.get('username')
            User = get_user_model()
            try:
                user = User.objects.get(username=username)
                data['email'] = user.email
            except User.DoesNotExist:
                # leave as-is; serializer will handle invalid credentials
                pass

        # Delegate to SimpleJWT's serializer for normal processing
        # Some environments may not expose TokenObtainPairView.serializer_class reliably,
        # so use the serializer class directly.
        serializer = TokenObtainPairSerializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as exc:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.validated_data, status=status.HTTP_200_OK)
