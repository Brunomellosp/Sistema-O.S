from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from .models import OrdemServico
from .serializers import UserSerializer, OrdemServicoSerializer
from .permissions import IsAdminOrOwner

User = get_user_model()

# --- USUÁRIOS ---
class UserList(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

class UserDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrOwner]

# --- ORDENS DE SERVIÇO ---
class OrdemServicoList(generics.ListCreateAPIView):
    queryset = OrdemServico.objects.all()
    serializer_class = OrdemServicoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(criado_por=self.request.user)

class OrdemServicoDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = OrdemServico.objects.all()
    serializer_class = OrdemServicoSerializer
    permission_classes = [IsAdminOrOwner]

# --- IMPORT CSV ---
class OrdemServicoImportCSV(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        file = request.FILES['file']
        import csv
        from io import StringIO
        data = StringIO(file.read().decode('utf-8'))
        reader = csv.DictReader(data)
        count = 0
        for row in reader:
            OrdemServico.objects.create(
                cliente=row['cliente'],
                descricao=row['descricao'],
                prioridade=row['prioridade'],
                status=row['status'],
                criado_por=request.user
            )
            count += 1
        return Response({'imported': count}, status=status.HTTP_201_CREATED)


from django.contrib.auth import login
from rest_framework.decorators import api_view, permission_classes

@api_view(['POST'])
@permission_classes([])
def register(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        user.set_password(request.data['password'])
        user.save()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)
