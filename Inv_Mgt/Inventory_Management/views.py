import json
import base64
import qrcode
import pandas as pd
from uuid import uuid4
from io import BytesIO
from urllib.parse import quote
from datetime import datetime
from django.http import JsonResponse
from django.http.multipartparser import MultiPartParser
from django.http import HttpResponse
from django.db.models import Q, F
from django.shortcuts import render
from django.db import IntegrityError
from django.contrib.auth import authenticate
from django.core.files.base import ContentFile

from knox.models import AuthToken
from rest_framework import status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, permissions
from rest_framework.exceptions import ValidationError

from Inventory_Management.models import CustomUser, Business, Supplier, ItemDetails, UpiDetails, Transaction
from Inventory_Management.serializers import CustomUserSerializer, BusinessSerializer, SupplierSerializer, ItemDetailsSerializer, ItemDetailsSearchSerializer, ItemDetailAlertSerializer, TransactionSerializer, UpiDetailsSerializer


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
        business_name = request.query_params.get('business')
        if user and business_name:
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
    serializer_class = ItemDetailAlertSerializer
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

class CreateUpiDetailsAPIView(generics.CreateAPIView):
    queryset = UpiDetails.objects.all()
    serializer_class = UpiDetailsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)   

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError:
            return Response({"message": "UPI details for this user already exist."}, status=status.HTTP_400_BAD_REQUEST)

class GenerateQRCodeAPIView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        quantity_delta = request.data.get('quantity_delta')
        price = request.data.get('price')

        if quantity_delta < 0:  # Item is being sold
            upi_details = UpiDetails.objects.get(user=request.user)

            # Calculate the total price
            total_price = price * abs(quantity_delta)
            # transaction_ref_id = f"tr-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid4()}"
            payee_name = quote(upi_details.payee_name)

            # Generate the UPI QR code
            transaction_note = f"Purchase of Item x {quantity_delta}"  # example transaction note
            upi_payload = f"upi://pay?pa={upi_details.payee_vpa}&pn={payee_name}&tn={transaction_note}&am={total_price}&cu=INR"
            qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
            qr.add_data(upi_payload)
            qr.make(fit=True)
            qr_code_img = qr.make_image(fill_color="black", back_color="white")

            # Save the QR code image to a BytesIO buffer
            buffered = BytesIO()
            qr_code_img.save(buffered, format="PNG")
            buffered.seek(0)  # Move the buffer position to the beginning

            response = HttpResponse(buffered, content_type='image/png')
            return response
        else:
            return Response({"message": "No item sold."}, status=status.HTTP_400_BAD_REQUEST)

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
            upi_details = UpiDetails.objects.get(user=request.user)
            business = Business.objects.get(owner=user, business_name=business_name)
            supplier = Supplier.objects.get(business=business, category=category, distributor_name=distributor_name)
            item = ItemDetails.objects.get(supplier=supplier, item_name=item_name, item_type=item_type, size=size, unit_of_measurement=uom)

            if quantity_delta < 0:  # Item is being sold
                if item.quantity + quantity_delta < 0:
                    response_data = {
                        "message": "Insufficient quantity in stock.",
                    }
                    return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
                
                # Calculate the total price
                total_price = item.price * abs(quantity_delta)

                # Generate transaction_id and transaction_ref_id
                transaction_id = f"txn-{uuid4()}"
                transaction_ref_id = f"tr-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid4()}"

            # Update the item quantity
            if additional_info:
                for key, value in additional_info.items():
                    if item.additional_info and key in item.additional_info and item.additional_info[key] == value:
                        item.quantity += quantity_delta
                        item.save()

                        if quantity_delta < 0:  # Item is being sold
                            # Create a new transaction object
                            transaction = Transaction.objects.create(
                                upi_details=upi_details,
                                transaction_id=transaction_id,
                                transaction_ref_id=transaction_ref_id,
                                amount=total_price,
                                item_id = item.id,
                                unit = abs(quantity_delta),
                                status='pending',
                            )

                            response_data = {
                                "message": "QR code generated successfully.",
                                "quantity_delta": quantity_delta,
                                "total_price": total_price,
                                "transaction_id": transaction_id
                            }
                            return Response(response_data, status=status.HTTP_200_OK)

                        else:  # Item is being added
                            response_data = {
                                "message": "Item quantity updated successfully.",
                                "updated_quantity": item.quantity,
                            }
                            return Response(response_data, status=status.HTTP_200_OK)

                    else:
                        return Response({"message": "Additional info doesn't match."}, status=status.HTTP_400_BAD_REQUEST)

            else:
                item.quantity += quantity_delta
                item.save()

                if quantity_delta < 0:  # Item is being sold
                    # Create a new transaction object
                    transaction = Transaction.objects.create(
                        upi_details=upi_details,
                        transaction_id=transaction_id,
                        transaction_ref_id=transaction_ref_id,
                        amount=total_price,
                        item_id = item.id,
                        unit = abs(quantity_delta),
                        status='pending',
                    )

                    response_data = {
                                "message": "QR code generated successfully.",
                                "quantity_delta": quantity_delta,
                                "total_price": total_price,
                                "transaction_id": transaction_id
                            }
                    return Response(response_data, status=status.HTTP_200_OK)

                else:  # Item is being added
                    response_data = {
                        "message": "Item quantity updated successfully.",
                        "updated_quantity": item.quantity,
                    }
                    return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            response_data = {"message": str(e)}
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

class UpdateTransactionStatusAPIView(generics.UpdateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        transaction_id = request.data.get('transaction_id')
        identifier = request.data.get('identifier')

        try:
            transaction = Transaction.objects.get(transaction_id=transaction_id)

            if identifier == 'Y':
                transaction.status = 'success'
                transaction.save()

                return Response({"message": "Transaction status updated to success."}, status=status.HTTP_200_OK)

            elif identifier == 'N':
                transaction.status = 'failed'
                transaction.save()

                item = ItemDetails.objects.get(id=transaction.item_id)
                item.quantity += transaction.unit
                item.save()

                return Response({"message": "Transaction status updated to failed and item quantity updated."}, status=status.HTTP_200_OK)

            else:
                return Response({"message": "Invalid identifier. It should be either 'Y' or 'N'."}, status=status.HTTP_400_BAD_REQUEST)

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

                existing_item = ItemDetails.objects.filter(supplier=supplier, item_name=item_name, item_type=item_type, size=size, unit_of_measurement=uom).first()

                if existing_item:
                    existing_item.quantity = quantity
                    existing_item.alert_quantity = alert_quantity
                    existing_item.additional_info.update(additional_info)
                    existing_item.imported_date = imported_date
                    existing_item.save()

                    serialized_data = ItemDetailsSerializer(existing_item).data
                    updated_rows += 1
                else:
                    item = ItemDetails.objects.create(supplier=supplier, item_name=item_name, item_type=item_type, size=size, unit_of_measurement=uom, quantity=quantity, alert_quantity=alert_quantity, additional_info=additional_info, imported_date=imported_date)

                    serialized_data = ItemDetailsSerializer(item).data
                    added_rows += 1
                    print(added_rows, updated_rows)

            return Response({"status": "success", "message": "Data imported successfully.", "added_rows": added_rows, "updated_rows": updated_rows}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"status": "failure", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
