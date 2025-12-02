import csv
import io
from django.contrib.auth import get_user_model
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, status
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from .models import ServiceOrder
from .serializers import (
    UserProfileSerializer,
    UserSerializer,
    UserRegistrationSerializer,
    ServiceOrderSerializer,
    PasswordResetConfirmSerializer
)

from django.utils.http import urlsafe_base64_encode
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.conf import settings

from .serializers import ChangePasswordSerializer

from django.shortcuts import render, redirect, get_object_or_404

User = get_user_model()

class IsAdminOrOwnerOrCreator(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True

        if isinstance(obj, User):
            return obj == request.user

        if isinstance(obj, ServiceOrder):
            return obj.created_by == request.user

        return False

class UserRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrOwnerOrCreator]


class ServiceOrderListCreateView(generics.ListCreateAPIView):
    serializer_class = ServiceOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return ServiceOrder.objects.all().order_by('-created_at')

        return ServiceOrder.objects.filter(created_by=user).order_by('-created_at')

class ServiceOrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ServiceOrder.objects.all()
    serializer_class = ServiceOrderSerializer
    permission_classes = [IsAdminOrOwnerOrCreator]

class ServiceOrderImportCSVView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        csv_file = request.FILES.get('file')

        if not csv_file:
            return Response(
                {"error": "Nenhum arquivo 'file' foi enviado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not csv_file.name.endswith('.csv'):
            return Response(
                {"error": "O arquivo deve ser um .csv"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            data_set = csv_file.read().decode('utf-8')
            io_string = io.StringIO(data_set)

            reader = csv.DictReader(io_string)

            created_count = 0
            errors = []

            with transaction.atomic():
                for i, row in enumerate(reader):
                    serializer = ServiceOrderSerializer(
                        data=row,
                        context={'request': request}
                    )

                    if serializer.is_valid():
                        serializer.save()
                        created_count += 1
                    else:

                        errors.append({
                            'row': i + 2,
                            'data': row,
                            'errors': serializer.errors
                        })

                if errors:
                    raise Exception("Erros de validação ocorreram durante a importação.")

            return Response(
                {'status': 'sucesso', 'imported': created_count},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:

            return Response(
                {
                    'status': 'erro',
                    'message': f"Falha na importação: {str(e)}",
                    'errors': errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    if request.method == 'POST':
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            return Response(
                {"message": f"User '{user.username}' created successfully."},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserList(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserDetail(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class UserProfileView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

class OrdemServicoList(generics.ListCreateAPIView):

    queryset = ServiceOrder.objects.all()
    serializer_class = ServiceOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter
    ]

    filterset_fields = ['status', 'priority', 'type', 'provider']

    search_fields = ['protocol', 'so_number', 'description', 'recipient_name']

    ordering_fields = ['created_at', 'priority']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class OrdemServicoDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = ServiceOrder.objects.all()
    serializer_class = ServiceOrderSerializer


class _OrdemServicoImportCSV(APIView):
    def post(self, request, *args, **kwargs):
        return Response({"message": "CSV Import endpoint is working"}, status=status.HTTP_200_OK)

class OrdemServicoImportCSV(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get('file')
        if not csv_file:
            return Response({"error": "Nenhum arquivo enviado."}, status=status.HTTP_400_BAD_REQUEST)

        if not csv_file.name.endswith('.csv'):
            return Response({"error": "O arquive deve ser um CSV."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            decoded_file = csv_file.read().decode('utf-8-sig')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            csv_data = list(reader)
        except Exception as e:
            return Response({"error": f"Não foi possível processar o arquivo CSV: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        if not csv_data:
            return Response({"error": "CSV está vázio."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ServiceOrderSerializer(data=csv_data, many=True, context={'request': request})

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": f"Importado com sucesso {len(serializer.data)} ordens de serviço."},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    email = request.data.get('email')
    if not email:
        return Response(
            {'error': 'O campo de e-mail é obrigatório.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(
            {'message': 'Se um usuário com este e-mail existir, um link de redefinição foi enviado.'},
            status=status.HTTP_200_OK
        )

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    frontend_url = 'https://sistema-os-frontend.vercel.app'

    reset_link = f"{frontend_url}/#/resetar-senha/?uid={uid}&token={token}"

    subject = 'Redefina sua senha'
    message = f"""
    Olá, {user.username}!

    Você solicitou a redefinição de senha. Clique no link abaixo:
    {reset_link}

    Se você não solicitou isso, por favor ignore este e-mail.
    """
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )

    return Response(
        {'message': 'Se um usuário com este e-mail existir, um link de redefinição foi enviado.'},
        status=status.HTTP_200_OK
    )

@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    serializer = PasswordResetConfirmSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(
            {'message': 'Senha redefinida com sucesso.'},
            status=status.HTTP_200_OK
        )
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kargs):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Senha alterada com sucesso."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def presentation_user_list(request):
    users = User.objects.all().order_by("-date_joined")
    return render(request, "presentation_users.html", {"users": users})

def presentation_user_delete(request, pk):
    if request.method == "POST":
        user_to_delete = get_object_or_404(User, pk=pk)
        user_to_delete.delete()

    return redirect("presentation-list")

@api_view(['GET'])
@permission_classes([AllowAny])
def hello_world(request):
    return Response({"message": "hello"})
