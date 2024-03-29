import json
import base64
import qrcode
# import cv2
# import pytesseract
import numpy
import pandas as pd
from uuid import uuid4
from io import BytesIO
from urllib.parse import quote
from django.db.models import Sum
from django.core.mail import send_mail
from django.utils import timezone
from django.db.models import Subquery
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from datetime import datetime, date, timedelta
from django.http.multipartparser import MultiPartParser
from django.http import HttpResponse
from django.db.models import Q, F
from django.conf import settings
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

from Inventory_Management.models import CustomUser, PasswordResetRequest, Business, Supplier, ItemDetails, UpiDetails, \
    Transaction, CartItem, Cart, BusinessWorker
from Inventory_Management.serializers import CustomUserSerializer, PasswordResetRequestSerializer, BusinessSerializer, \
    SupplierSerializer, ItemDetailsSerializer, ItemDetailsSearchSerializer, ItemDetailAlertSerializer, TransactionSerializer, \
    UpiDetailsSerializer, TransactionDetailsSerializer, CartItemSerializer, BusinessWorkerSerializer


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
            Cart.objects.create(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({"error": "Username, email, or phone number already in use"}, status=status.HTTP_400_BAD_REQUEST)

class CurrentUserAPIView(generics.RetrieveAPIView):
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

class UpdateUserAPIView(generics.UpdateAPIView):
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)
    

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

class PasswordResetRequestCreateAPIView(generics.CreateAPIView):
    queryset = PasswordResetRequest.objects.all()
    serializer_class = PasswordResetRequestSerializer

    def create(self, request, *args, **kwargs):
        identifier = request.data['identifier']
        user = CustomUser.objects.filter(username=identifier).first() or \
               CustomUser.objects.filter(email=identifier).first() or \
               CustomUser.objects.filter(phone_no=identifier).first()
        if user:
            otp = PasswordResetRequest.generate_otp()
            password_reset_request = PasswordResetRequest(user=user, otp=otp)
            password_reset_request.save()

            # Send email
            subject = 'Password Reset Request'
            message = f'Your OTP for password reset is: {otp}'
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [user.email]

            send_mail(subject, message, from_email, recipient_list)

            # Send SMS
            # Use your preferred SMS gateway service, like Twilio, to send the OTP to the user's phone number

            return Response({'message': 'OTP sent'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

class VerifyOTPAPIView(APIView):
    def post(self, request):
        identifier = request.data['identifier']
        provided_otp = request.data['otp']

        user = CustomUser.objects.filter(username=identifier).first() or \
               CustomUser.objects.filter(email=identifier).first() or \
               CustomUser.objects.filter(phone_no=identifier).first()

        if user:
            reset_request = PasswordResetRequest.objects.filter(user=user, otp=provided_otp, is_used=False).first()
            if reset_request:
                # Optionally, check if the OTP has expired
                time_elapsed = timezone.now() - reset_request.timestamp
                if time_elapsed > timedelta(minutes=15):
                    return Response({'error': 'OTP has expired'}, status=status.HTTP_400_BAD_REQUEST)

                return Response({'message': 'OTP verified'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
class ResetPasswordAPIView(APIView):
    def post(self, request):
            identifier = request.data['identifier']
            provided_otp = request.data['otp']
            new_password = request.data['new_password']

            user = CustomUser.objects.filter(username=identifier).first() or \
                CustomUser.objects.filter(email=identifier).first() or \
                CustomUser.objects.filter(phone_no=identifier).first()

            if user:
                reset_request = PasswordResetRequest.objects.filter(user=user, otp=provided_otp, is_used=False).first()
                if reset_request:
                    user.set_password(new_password)
                    user.save()
                    reset_request.is_used = True
                    reset_request.save()

                    return Response({'message': 'Password reset successful'}, status=status.HTTP_200_OK)
                else:
                    return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

class BusinessCreateView(generics.CreateAPIView):
    queryset = Business.objects.all()
    serializer_class = BusinessSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        try:
            user = self.request.user
            data = serializer.save(owner=user)
            user.role = 'owner'
            user.save()
            return Response("Successfully registered!", data, status=status.HTTP_201_CREATED)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)

class ListBusiness(generics.ListAPIView):
    serializer_class = BusinessSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user:
            if user.role == 'worker':
                worker_business = BusinessWorker.objects.filter(worker=user)
                return [association.business for association in worker_business]
            else:
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
            try:
                business = Business.objects.get(business_name=business_name)
            except Business.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
            if business.owner == user or BusinessWorker.objects.filter(worker=user, business=business).exists():
                supplier = Supplier.objects.filter(business=business)
                serializer = SupplierSerializer(supplier, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_403_FORBIDDEN)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

class ListUPIDetails(generics.ListAPIView):
    serializer_class = UpiDetailsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user:
            return UpiDetails.objects.filter(user=user)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

class UPIDeleteAPIView(generics.DestroyAPIView):
    serializer_class = UpiDetailsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        user = request.user
        upi = request.data['upi']
        try:
            upi_details = UpiDetails.objects.get(user=user,payee_vpa=upi)
        except UpiDetails.DoesNotExist:
            raise ValidationError('UpiDetails does not exist for the current user.')
        upi_details.delete()
        message = 'UpiDetails has been deleted successfully.'
        return Response({'message': message}, status=status.HTTP_204_NO_CONTENT)

class SearchSupplierAPIView(generics.ListAPIView):
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        business_name = self.request.data.get('business', None)
        queryset = Supplier.objects.none()

        if user and business_name:
            try:
                business = Business.objects.get(business_name=business_name)
            except Business.DoesNotExist:
                return queryset

            if business.owner == user or BusinessWorker.objects.filter(worker=user, business=business).exists():
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
            business = Business.objects.get(business_name=business_name)
        except Business.DoesNotExist:
            return Response({"error": "Business does not exist!"}, status=status.HTTP_400_BAD_REQUEST)

        if business.owner == request.user or BusinessWorker.objects.filter(worker=request.user, business=business).exists():
            try:
                supplier = Supplier.objects.get(business=business, category=category, distributor_name=distributor_name)
                queryset = ItemDetails.objects.filter(supplier=supplier)

                serializer = self.get_serializer(queryset, many=True)
                return Response(serializer.data)

            except Supplier.DoesNotExist:
                return Response({"error": "Supplier does not exist!"}, status=status.HTTP_400_BAD_REQUEST)

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
        item_name = self.request.query_params.get('item_name', None)

        businesses = Business.objects.filter(Q(owner=self.request.user) | Q(businessworker__worker=self.request.user))

        if business_name:
            businesses = businesses.filter(business_name=business_name)
            if not businesses.exists():
                return ItemDetails.objects.none()

        queryset = ItemDetails.objects.filter(supplier__business__in=businesses)
        
        if item_name and item_name.isdigit():
            try:
                item = ItemDetails.objects.get(id=item_name, supplier__business__in=businesses)
                return [item,]  # Return a list containing the item
            except ItemDetails.DoesNotExist:
                pass

        category = self.request.query_params.get('category', None)
        distributor_name = self.request.query_params.get('distributor_name', None)

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
        if isinstance(queryset, list):
            if not queryset:
                return Response({'error': 'No match found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            if not queryset.exists():
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
            business = Business.objects.get(Q(owner=user) | Q(businessworker__worker=user), business_name=business_name)
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
            business = Business.objects.get(Q(owner=user) | Q(businessworker__worker=user), business_name=business_name)
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


class ItemDetailsUpdateDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        item_id = request.data.get('item_id', None)
        identifier = request.data.get('identifier', None)
        details = request.data.get('details', None)

        if item_id is None or identifier is None:
            raise ValidationError({'error': 'Missing required parameters: item_id, identifier'})

        try:
            item = ItemDetails.objects.get(id=item_id)
        except ItemDetails.DoesNotExist:
            raise ValidationError({'error': 'Invalid item_id'})

        if identifier.upper() == 'E':
            if details is None:
                raise ValidationError({'error': 'Missing required parameters: details'})
            serializer = ItemDetailsSerializer(item, data=details, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=400)
        elif identifier.upper() == 'D':
            item.delete()
            return Response({'success': 'Item deleted successfully'})
        else:
            raise ValidationError({'error': 'Invalid identifier. Must be either E or D'})
        
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
        price = request.data.get('price')
        
        user = request.user
        business = Business.objects.filter(Q(owner=user) | Q(businessworker__worker=user)).first()
        upi_details = UpiDetails.objects.get(user=business.owner)
        payee_name = quote(upi_details.payee_name)

        # Generate the UPI QR code
        transaction_note = f"Purchase of Item x price {price}"  # example transaction note
        upi_payload = f"upi://pay?pa={upi_details.payee_vpa}&pn={payee_name}&tn={transaction_note}&am={price}&cu=INR"
        qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(upi_payload)
        qr.make(fit=True)
        qr_code_img = qr.make_image(fill_color="black", back_color="white")

        buffered = BytesIO()
        qr_code_img.save(buffered)
        buffered.seek(0)  # Move the buffer position to the beginning
        response = HttpResponse(buffered, content_type='image/png')
        return response
        

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
            business = Business.objects.get(Q(owner=user, business_name=business_name) | Q(businessworker__worker=user, business_name=business_name))
            supplier = Supplier.objects.get(business=business, category=category, distributor_name=distributor_name)
            items = ItemDetails.objects.filter(supplier=supplier, item_name=item_name, item_type=item_type, size=size, unit_of_measurement=uom)
            
            # Check if the user is a worker and tries to add items
            if quantity_delta > 0 and business.owner != user:
                return Response({"message": "Workers are not permitted to add items."}, status=status.HTTP_403_FORBIDDEN)

            if additional_info:
                match_found = False
                for item in items:
                    additional_info_matched = True
                    for key, value in additional_info.items():
                        if not (item.additional_info and key in item.additional_info and item.additional_info[key] == value):
                            additional_info_matched = False
                            break

                    if additional_info_matched:
                        match_found = True
                        item.quantity += quantity_delta
                        item.save()
                        break

                if not match_found:
                    return Response({"message": "Additional info doesn't match."}, status=status.HTTP_400_BAD_REQUEST)

            else:
                item = items.first()
                item.quantity += quantity_delta
                item.save()

            if quantity_delta < 0:  # Item is being sold
                if item.quantity + quantity_delta < 0:
                    response_data = {
                        "message": "Insufficient quantity in stock.",
                    }
                    return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
                
                response_data = {
                    "item_id": item.id,
                    "quantity_delta": quantity_delta
                }
                return Response(response_data, status=status.HTTP_200_OK)

            else:  # Item is being added
                # Calculate the total price
                total_price = item.price * abs(quantity_delta)
                # Generate transaction_id and transaction_ref_id
                transaction_id = f"txn-{uuid4()}"
                transaction_ref_id = f"tr-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid4()}"

                # Create a new transaction object
                upi_details = UpiDetails.objects.get(user=business.owner)
                transaction = Transaction.objects.create(
                    upi_details=upi_details,
                    transaction_made_by=request.user,
                    transaction_id=transaction_id,
                    transaction_ref_id=transaction_ref_id,
                    amount=total_price,
                    item_id=item.id,
                    unit=abs(quantity_delta),
                    status='success',
                    type='added'
                )
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
        transaction_ids = request.data.get('transaction_ids', [])
        identifier = request.data.get('identifier')

        if not transaction_ids or not isinstance(transaction_ids, list):
            return Response({"message": "transaction_ids must be a non-empty list."}, status=status.HTTP_400_BAD_REQUEST)

        for transaction_id in transaction_ids:
            try:
                transaction = Transaction.objects.get(transaction_id=transaction_id)

                if identifier == 'Y':
                    transaction.status = 'success'
                    transaction.save()

                elif identifier == 'N':
                    transaction.status = 'failed'
                    transaction.save()

                    item = ItemDetails.objects.get(id=transaction.item_id)
                    item.quantity += transaction.unit
                    item.save()

                else:
                    return Response({"message": "Invalid identifier. It should be either 'Y' or 'N'."}, status=status.HTTP_400_BAD_REQUEST)

            except Exception as e:
                response_data = {"message": str(e), "transaction_id": transaction_id}
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Transaction statuses updated successfully."}, status=status.HTTP_200_OK)


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
                price = row.Price if not pd.isna(row.Price) else 0.00
                cogs = row.COGS if not pd.isna(row.COGS) else 0.00
                alert_quantity = row.Alert
                additional_info_str = row._12
                imported_date = row.Date.date()

                additional_info = json.loads(additional_info_str)

                business = Business.objects.get(business_name=business_name)
                supplier, created = Supplier.objects.get_or_create(business=business, category=category, distributor_name=distributor_name)

                items = ItemDetails.objects.filter(supplier=supplier, item_name=item_name, item_type=item_type, size=size, unit_of_measurement=uom)
                

                existing_item = None
                for item in items:
                    if item.additional_info == additional_info:
                        existing_item = item
                        break
                
                if existing_item:
                    existing_item.quantity = quantity
                    existing_item.price = price
                    existing_item.cogs = cogs
                    existing_item.alert_quantity = alert_quantity
                    existing_item.additional_info.update(additional_info)
                    existing_item.imported_date = imported_date
                    existing_item.save()
                
                    serialized_data = ItemDetailsSerializer(existing_item).data
                    updated_rows += 1
                    print(f"Updated row: {item_name} ({updated_rows})")
                else:
                    item = ItemDetails.objects.create(supplier=supplier, item_name=item_name, item_type=item_type, size=size, unit_of_measurement=uom, quantity=quantity, price=price, cogs=cogs,  alert_quantity=alert_quantity, additional_info=additional_info, imported_date=imported_date)

                    serialized_data = ItemDetailsSerializer(item).data
                    added_rows += 1
                    print(f"Added row: {item_name} ({added_rows})")

            return Response({"status": "success", "message": "Data imported successfully.", "added_rows": added_rows, "updated_rows": updated_rows}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"status": "failure", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

class TransactionsByDateView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TransactionDetailsSerializer

    def get_queryset(self):
        target_date_str = self.request.query_params.get('date')
        business_name = self.request.query_params.get('business_name')
        if target_date_str:
            target_date = date.fromisoformat(target_date_str)
        else:
            target_date = date.today()

        queryset = Transaction.objects.filter(created_at__date=target_date, status='success').order_by('-created_at')

        if business_name:
            user = self.request.user
            business = Business.objects.get(Q(owner=user) | Q(businessworker__worker=user), business_name=business_name)
            item_ids = ItemDetails.objects.filter(supplier__business=business).values('id')
            queryset = queryset.filter(item_id__in=Subquery(item_ids))

        return queryset


class SalesPerformanceAPIView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        business = self.request.query_params.get('business')
        time_period = self.request.query_params.get('time_period', '1')
        current_date = timezone.now().date()

        if time_period == '1':
            start_date = current_date
        elif time_period == '30':
            start_date = current_date - timedelta(days=30)
        elif time_period == '9':
            current_year = current_date.year
            start_date = current_date.replace(year=current_year, month=1, day=1)
        else:
            start_date = current_date
        
        if business:
            business = get_object_or_404(Business, business_name=business)
            suppliers = Supplier.objects.filter(business=business)
            items = ItemDetails.objects.filter(supplier__in=suppliers)
            transactions = Transaction.objects.filter(status='success', type='sold', created_at__gte=start_date, item_id__in=items)
        else:
            transactions = Transaction.objects.filter(status='success', type='sold', created_at__gte=start_date)
        sales_data = []
        
        total_revenue = 0
        total_cogs = 0
        total_profit_loss = 0

        consolidated_data = {}

        for transaction in transactions:
            item = get_object_or_404(ItemDetails, pk=transaction.item_id)
            supplier = item.supplier
            units_sold = transaction.unit
            revenue = transaction.amount
            cogs = item.cogs * units_sold
            profit_loss = revenue - cogs
            profit_loss_percentage = (profit_loss / revenue) * 100

            total_revenue += revenue
            total_cogs += cogs
            total_profit_loss += profit_loss

            item_key = (item.item_name, supplier.distributor_name, supplier.category)

            if item_key not in consolidated_data:
                consolidated_data[item_key] = {
                    'item_name': item.item_name,
                    'distributor': supplier.distributor_name,
                    'category': supplier.category,
                    'units_sold': units_sold,
                    'revenue': revenue,
                    'cogs': cogs,
                    'profit_loss': profit_loss,
                    'profit_loss_percentage': profit_loss_percentage
                }
            else:
                existing_data = consolidated_data[item_key]
                existing_data['units_sold'] += units_sold
                existing_data['revenue'] += revenue
                existing_data['cogs'] += cogs
                existing_data['profit_loss'] += profit_loss
                existing_data['profit_loss_percentage'] = (existing_data['profit_loss'] / existing_data['revenue']) * 100

        total_profit_loss_percentage = (total_profit_loss / total_revenue) * 100 if total_revenue != 0 else 0
        sales_data = list(consolidated_data.values())

        summary_data = {
            'total_revenue': total_revenue,
            'total_cogs': total_cogs,
            'total_profit_loss': total_profit_loss,
            'total_profit_loss_percentage': total_profit_loss_percentage,
            'sales_data': sales_data
        }

        return summary_data

    def list(self, request, *args, **kwargs):
        summary_data = self.get_queryset()
        return Response(summary_data)


class TopItemsAPIView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = ItemDetails.objects.all()

    def list(self, request, *args, **kwargs):
        business = self.request.query_params.get('business')
        current_year = datetime.now().year

        if business:
            business = get_object_or_404(Business, business_name=business)
            suppliers = Supplier.objects.filter(business=business)
            items = ItemDetails.objects.filter(supplier__in=suppliers)
        else:
            items = self.get_queryset()
        item_sales = []

        for item in items:
            units_sold = Transaction.objects.filter(
                status='success', 
                type='sold',
                item_id=item.id,
                created_at__year=current_year
            ).aggregate(Sum('unit'))['unit__sum'] or 0

            revenue = units_sold * item.price
            cogs = units_sold * item.cogs
            profit_loss = revenue - cogs
            profit_loss_percentage = (profit_loss / revenue) * 100 if revenue != 0 else 0

            supplier = Supplier.objects.get(id=item.supplier_id)

            item_sales.append({
                'item_name': item.item_name,
                'size': item.size,
                'unit_of_measurement': item.unit_of_measurement,
                'distributor': supplier.distributor_name,
                'category': supplier.category,
                'units_sold': units_sold,
                'revenue': revenue,
                'cogs': cogs,
                'profit_loss': profit_loss,
                'profit_loss_percentage': profit_loss_percentage,
            })

        sorted_items = sorted(item_sales, key=lambda x: x['units_sold'], reverse=True)[:10]

        ranked_items = []
        for rank, item in enumerate(sorted_items, start=1):
            ranked_item = item.copy()
            ranked_item['rank'] = rank
            ranked_items.append(ranked_item)

        return Response(ranked_items)

class CartItemListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        cart, created = Cart.objects.get_or_create(user=user)
        return CartItem.objects.filter(cart=cart)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        response_data = []

        for cart_item in queryset:
            item = cart_item.item
            transaction = Transaction.objects.filter(item_id=item.id).last()
            response_data.append({
                "cart_item_id": cart_item.id,
                "item": item.item_name,
                "size": item.size,
                "unit": transaction.unit,
                "total_price": transaction.amount,
                "transaction_id": transaction.transaction_id
            })

        return Response(response_data)

    def create(self, request, *args, **kwargs):
        item_id = request.data.get('item_id')
        quantity = request.data.get('quantity', 0)

        try:
            user = request.user
            cart, created = Cart.objects.get_or_create(user=user)
            item = ItemDetails.objects.get(id=item_id)

            if quantity < 0:  # Item is being sold
                if item.quantity + quantity < 0:
                    response_data = {
                        "message": "Insufficient quantity in stock.",
                    }
                    return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

            cart_item, created = CartItem.objects.get_or_create(cart=cart, item=item, quantity=quantity)
            if not created:
                cart_item.quantity += quantity
            else:
                cart_item.quantity = quantity
            cart_item.save()

            # Calculate the total price
            total_price = item.price * abs(quantity)
            # Generate transaction_id and transaction_ref_id
            transaction_id = f"txn-{uuid4()}"
            transaction_ref_id = f"tr-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid4()}"

            # Create a new transaction object
            business = Business.objects.filter(Q(owner=user) | Q(businessworker__worker=user)).first()
            upi_details = UpiDetails.objects.get(user=business.owner)
            transaction = Transaction.objects.create(
                upi_details=upi_details,
                transaction_made_by=request.user,
                transaction_id=transaction_id,
                transaction_ref_id=transaction_ref_id,
                amount=total_price,
                item_id=item.id,
                unit=abs(quantity),
                status='pending',
                type='sold'
            )

            response_data = {
                "message": "Item added.",
                "cart_item_id": cart_item.id,
                "item": item.item_name,
                "size": item.size,
                "unit": transaction.unit,
                "total_price": total_price,
                "transaction_id": transaction_id
            }
            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            response_data = {"message": str(e)}
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


class CartItemRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        cart = Cart.objects.get(user=user)
        return CartItem.objects.filter(cart=cart)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response({"message": "Item deleted"}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"message": "Item not deleted"}, status=status.HTTP_400_BAD_REQUEST)

class CartItemCountAPIView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CartItemSerializer

    def retrieve(self, request, *args, **kwargs):
        user = request.user
        cart = Cart.objects.get(user=user)
        cart_items_count = CartItem.objects.filter(cart=cart).count()
        if cart_items_count is None:
            cart_items_count = 0
        return Response({"items_count": cart_items_count})
    

# from rest_framework.parsers import MultiPartParser, JSONParser
# class OCRAPIView(APIView):
#     parser_classes = (MultiPartParser, JSONParser)

#     def post(self, request, *args, **kwargs):
#         file = request.data['image']
#         image = cv2.imdecode(numpy.fromstring(file.read(), numpy.uint8), cv2.IMREAD_UNCHANGED)
#         gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
#         import os
#         os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata'
#         pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
#         ocr_result = pytesseract.image_to_string(gray_image)
#         return Response({"text_detected": ocr_result})


class BusinessWorkerCreateAPIView(generics.CreateAPIView):
    queryset = BusinessWorker.objects.all()
    serializer_class = BusinessWorkerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        owner = request.user
        if owner.role != 'owner':
            return Response({"message": "You must be an owner to perform this action."}, status=status.HTTP_403_FORBIDDEN)

        worker_username = request.data.get('worker_username')
        business_names = request.data.get('business_names')

        try:
            worker = CustomUser.objects.get(username=worker_username)
        except CustomUser.DoesNotExist:
            return Response({"message": "User does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the worker is not an owner
        if worker.role != 'worker':
            return Response({"message": "This user is not a worker."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the businesses exist and the user is the owner
        for business_name in business_names:
            try:
                business = Business.objects.get(business_name=business_name)
                if business.owner != owner:
                    return Response({"message": "You are not the owner of this business."}, status=status.HTTP_403_FORBIDDEN)
            except Business.DoesNotExist:
                return Response({"message": "Business does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        for business_name in business_names:
            business = Business.objects.get(business_name=business_name)
            BusinessWorker.objects.create(worker=worker, business=business)

        return Response({"message": "Business worker created successfully."}, status=status.HTTP_201_CREATED)
    


class HelloWorldView(APIView):
    def get(self, request):
        print("hello!!!!!!world!!!!")
        return Response("Hello World <3")