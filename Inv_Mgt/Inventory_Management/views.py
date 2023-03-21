from django.db.models import Q
from django.shortcuts import render
from django.db import IntegrityError
from django.contrib.auth import authenticate

from knox.models import AuthToken
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, permissions
from rest_framework.exceptions import ValidationError

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

class SupplierUpdateAPIView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        business_name = request.data['business']
        distributor_name = request.data['distributor_name']
        category = request.data.get('category', None)
        distributor_name_new = request.data.get('distributor_name_new', None)

        business = Business.objects.get(owner=request.user, business_name=business_name)
        try:
            supplier = Supplier.objects.get(business=business, distributor_name=distributor_name)
        except Supplier.DoesNotExist:
            raise ValidationError('The supplier with the given distributor name does not exist.')
        
        if category is not None:
            supplier.category = category
        if distributor_name_new is not None:
            supplier.distributor_name = distributor_name_new
        
        supplier.save()
        serializer = SupplierSerializer(supplier)
        return Response(serializer.data, status=status.HTTP_200_OK)

class SupplierDeleteAPIView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        business_name = request.data['business']
        category = request.data.get('category', None)
        distributor_name = request.data.get('distributor_name', None)
        
        business = Business.objects.get(owner=request.user, business_name=business_name)
        
        if category is not None and distributor_name is not None:
            try:
                supplier = Supplier.objects.get(business=business, category=category, distributor_name=distributor_name)
            except Supplier.DoesNotExist:
                raise ValidationError('The supplier with the given category and distributor name does not exist.')
            supplier.delete()
            message = 'The supplier with the given category and distributor name has been deleted successfully.'
        elif category is not None:
            suppliers = Supplier.objects.filter(business=business, category=category)
            if not suppliers:
                raise ValidationError('No suppliers found under the given category.')
            suppliers.delete()
            message = 'All suppliers under the given category have been deleted successfully.'
        else:
            raise ValidationError('Either the category or the combination of category and distributor name must be provided.')
        
        return Response({'message': message}, status=status.HTTP_200_OK)
    

class ListBusinessSuppliers(generics.ListAPIView):
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = self.request.user
        business_name = request.data['business']
        if user:
            business = Business.objects.get(owner=user, business_name=business_name)
            supplier = Supplier.objects.filter(business=business)
            serializer = SupplierSerializer(supplier, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


class SearchSupplierAPIView(generics.ListAPIView):
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        business_name = self.request.data.get('business', None)
        queryset = Supplier.objects.none()

        if user and business_name:
            business = Business.objects.filter(owner=user, business_name=business_name).first()
            if business:
                queryset = Supplier.objects.filter(business=business)
                search_query = self.request.data.get('search', None)
                if search_query:
                    queryset = queryset.filter(
                        Q(category__icontains=search_query) | 
                        Q(distributor_name__icontains=search_query)
                    )
        return queryset

    def post(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            # return a custom error response
            return Response({'error': 'No match found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)