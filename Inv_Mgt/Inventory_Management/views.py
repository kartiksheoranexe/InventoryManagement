from django.shortcuts import render
from django.db import IntegrityError
from django.contrib.auth import authenticate

from knox.models import AuthToken
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, permissions
from rest_framework.permissions import IsAuthenticated

from Inventory_Management.models import CustomUser, Business, Supplier
from Inventory_Management.serializers import CustomUserSerializer, BusinessSerializer, SupplierSerializer


# Create your views here.
class CustomUserCreateAPIView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            user.set_password(request.data['password'])
            user.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({"error": "Username, email, or phone number already in use"}, status=status.HTTP_400_BAD_REQUEST)
        
class LoginAPIView(APIView):
    def post(self, request):
        # Validate the login credentials
        username = request.data['username']
        password = request.data['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            token = AuthToken.objects.create(user)
            return Response({'token': token[1]})
        else:
            return Response({'error': 'Invalid login credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutAPIView(APIView):
    def post(self, request):
        # Get the user's JWT
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        t = token[:8]
        auth_token = AuthToken.objects.get(token_key=t)
        auth_token.delete()
        return Response({"User Logged Out Succesfully!!"}, status=status.HTTP_204_NO_CONTENT)

class BusinessCreateView(generics.CreateAPIView):
    queryset = Business.objects.all()
    serializer_class = BusinessSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        try:
            user = self.request.user
            data = serializer.save(owner=user)
            return Response("Successfully registered!", data, status=status.HTTP_201_CREATED)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)

class ListBusiness(generics.ListAPIView):
    serializer_class = BusinessSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user:
            return Business.objects.filter(owner=user)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


class SupplierCreateAPIView(generics.CreateAPIView):
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        try:
            business_name = request.data['business']
            category = request.data['category']
            distributor_name = request.data['distributor_name']
            business = Business.objects.get(owner=request.user, business_name=business_name)
            supplier = Supplier.objects.create(business=business, category=category, distributor_name=distributor_name)
            serializer = SupplierSerializer(supplier)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        
        except KeyError as e:
            return Response({"error": f"Missing field: {e.args[0]}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
