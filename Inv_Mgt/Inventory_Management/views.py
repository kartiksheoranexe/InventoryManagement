import json
import pandas as pd
from django.db.models import Q, F
from django.shortcuts import render
from django.db import IntegrityError
from django.contrib.auth import authenticate

from knox.models import AuthToken
from rest_framework import status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, permissions
from rest_framework.exceptions import ValidationError

from Inventory_Management.models import CustomUser, Business, Supplier, ItemDetails
from Inventory_Management.serializers import CustomUserSerializer, BusinessSerializer, SupplierSerializer, ItemDetailsSerializer, ItemDetailsSearchSerializer


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

class ItemDetailsListAPIView(generics.ListAPIView):
    serializer_class = ItemDetailsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        business_name = request.data.get('business_name')
        category = request.data.get('category')
        distributor_name = request.data.get('distributor_name')

        try:
            business = Business.objects.get(owner=request.user, business_name=business_name)
            supplier = Supplier.objects.get(business=business, category=category, distributor_name=distributor_name)
            queryset = ItemDetails.objects.filter(supplier=supplier)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        except (Business.DoesNotExist, Supplier.DoesNotExist):
            return Response({"error": "Business Or Supplier does not exist!"}, status=status.HTTP_400_BAD_REQUEST)

class ItemDetailsCreateAPIView(generics.CreateAPIView):
    queryset = ItemDetails.objects.all()
    serializer_class = ItemDetailsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        business_name = request.data.get('business_name')
        category = request.data.get('category')
        distributor_name = request.data.get('distributor_name')

        try:
            business = Business.objects.get(owner=request.user, business_name=business_name)
            supplier = Supplier.objects.get(business=business, category=category, distributor_name=distributor_name)
            request.data['supplier'] = supplier.id

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

        except (Business.DoesNotExist, Supplier.DoesNotExist):
            return Response({"error": "Business Or Supplier does not exist!"}, status=status.HTTP_400_BAD_REQUEST)

class SearchItemDetailsAPIView(generics.ListAPIView):
    serializer_class = ItemDetailsSearchSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['item_name', 'supplier__category', 'supplier__distributor_name']

    def get_queryset(self):
        business_name = self.request.query_params.get('business_name', None)
        category = self.request.query_params.get('category', None)
        distributor_name = self.request.query_params.get('distributor_name', None)
        item_name = self.request.query_params.get('item_name', None)

        if business_name:
            user_business = Business.objects.filter(owner=self.request.user, business_name=business_name)
        else:
            user_business = Business.objects.filter(owner=self.request.user)

        queryset = ItemDetails.objects.filter(supplier__business__in=user_business)

        if category is not None:
            queryset = queryset.filter(supplier__category__icontains=category)

        if distributor_name is not None:
            queryset = queryset.filter(supplier__distributor_name__icontains=distributor_name)

        if item_name is not None:
            queryset = queryset.filter(item_name__icontains=item_name)

        if not queryset.exists():
            queryset = ItemDetails.objects.none()

        return queryset
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            # return a custom error response
            return Response({'error': 'No match found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ItemAlertListAPIView(generics.GenericAPIView):
    serializer_class = ItemDetailsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = self.request.user
        business_name = request.data.get('business_name')

        try:
            business = Business.objects.get(owner=user, business_name=business_name)
            suppliers = Supplier.objects.filter(business=business)

            alert_items = []
            for supplier in suppliers:
                queryset = ItemDetails.objects.filter(supplier=supplier, quantity__lte=F('alert_quantity'))
                if queryset.exists():
                    serializer = self.get_serializer(queryset, many=True)
                    alert_items.extend(serializer.data)

            if alert_items:
                return Response(alert_items, status=status.HTTP_200_OK)
            else:
                response_data = {"message": "No items are below the alert quantity value for any supplier in this business"}
                return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            response_data = {"message": str(e)}
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

class ItemAlertCountAPIView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = self.request.user
        business_name = request.data.get('business_name')

        try:
            business = Business.objects.get(owner=user, business_name=business_name)
            suppliers = Supplier.objects.filter(business=business)

            alert_items_count = 0
            for supplier in suppliers:
                queryset = ItemDetails.objects.filter(supplier=supplier, quantity__lte=F('alert_quantity'))
                alert_items_count += queryset.count()

            response_data = {"alert_items_count": alert_items_count}
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            response_data = {"message": str(e)}
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        

class UpdateItemQuantityAPIView(generics.UpdateAPIView):
    queryset = ItemDetails.objects.all()
    serializer_class = ItemDetailsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        business_name = request.data.get('business')
        distributor_name = request.data.get('distributors_name')
        category = request.data.get('category')
        item_name = request.data.get('item_name')
        item_type = request.data.get('item_type')
        size = request.data.get('size')
        uom = request.data.get('uom')
        quantity_delta = request.data.get('quantity_delta')
        additional_info = request.data.get('additional_info')

        try:
            user = request.user
            business = Business.objects.get(owner=user, business_name=business_name)
            supplier = Supplier.objects.get(business=business, category=category, distributor_name=distributor_name)
            item = ItemDetails.objects.get(supplier=supplier, item_name=item_name, item_type=item_type, size=size, unit_of_measurement=uom)

            if additional_info:
                for key, value in additional_info.items():
                    if item.additional_info and key in item.additional_info and item.additional_info[key] == value:
                        item.quantity += quantity_delta
                        item.save()
                        serializer = self.get_serializer(item)
                        return Response(serializer.data, status=status.HTTP_200_OK)
                    else:
                        return Response({"message": "Additional info doesn't match."}, status=status.HTTP_400_BAD_REQUEST)

            else:
                item.quantity += quantity_delta
                item.save()
                serializer = self.get_serializer(item)
                return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            response_data = {"message": str(e)}
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

class ImportExcelDataAPIView(generics.CreateAPIView):
    serializer_class = ItemDetailsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        try:
            excel_file = request.FILES['file']
            df = pd.read_excel(excel_file, sheet_name='Data')
            added_rows = 0
            updated_rows = 0

            for row in df.itertuples():
                business_name = row.Business
                category = row.Category
                distributor_name = row._3
                item_name = row._4
                item_type = row._5
                size = row.Size
                uom = row.Uom
                quantity = row.Quantity
                alert_quantity = row.Alert
                additional_info_str = row._10
                imported_date = row.Date.date()

                additional_info = json.loads(additional_info_str)

                business = Business.objects.get(business_name=business_name)
                supplier, created = Supplier.objects.get_or_create(business=business, category=category, distributor_name=distributor_name)

                existing_item = ItemDetails.objects.filter(supplier=supplier, item_name=item_name, item_type=item_type, size=size, unit_of_measurement=uom, imported_date=imported_date).first()

                if existing_item:
                    existing_item.quantity = quantity
                    existing_item.alert_quantity = alert_quantity
                    existing_item.additional_info.update(additional_info)
                    existing_item.save()

                    serialized_data = ItemDetailsSerializer(existing_item).data
                    updated_rows += 1

                else:
                    item = ItemDetails.objects.create(supplier=supplier, item_name=item_name, item_type=item_type, size=size, unit_of_measurement=uom, quantity=quantity, alert_quantity=alert_quantity, additional_info=additional_info, imported_date=imported_date)

                    serialized_data = ItemDetailsSerializer(item).data
                    added_rows += 1

            return Response({"status": "success", "message": "Data imported successfully.", "added_rows": added_rows, "updated_rows": updated_rows}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"status": "failure", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
