from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Profile
from client_actions.models import Config, Order, Payment
from plans.models import Plan

from .serializers import (ConfigSerializer, OrderSerializer, PaymentSerializer,
                          PlanSerializer, ProfileSerializer,
                          RegisterSerializer)

User = get_user_model()


# ----------------- Account views -----------------

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

class ProfileView(APIView):
    permission_classes = [IsAuthenticated, ]
    
    
    def get(self, request):
        
        try:
            profile = Profile.objects.get(user=request.user)
            serializer = ProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Profile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

  
# ----------------- Client actions views -----------------  
        
class ConfigView(APIView):
    permission_classes = [IsAuthenticated, ]
    
    
    def get(self, request):
        
        # get the config_pk
        config_pk = request.query_params.get('config_pk')
        if config_pk is None:
            return Response({'error': 'Pick a config first'}, status=status.HTTP_400_BAD_REQUEST)
        
        # check if the config exists       
        try:
            config = Config.objects.get(pk= config_pk, user=request.user)
        
        except Config.DoesNotExist:
            return Response({'error': 'Config not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # return the config
        serializer = ConfigSerializer(config)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = ConfigSerializer(data=request.data)
        
        # check if the serializer is valid
        if serializer.is_valid(raise_exception=True):
            serializer.save(user=request.user)
            
            # update the profile is_active field
            profile = Profile.objects.get(user=request.user)
            profile.is_active = True
            profile.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ConfigListView(APIView):
    permission_classes = [IsAuthenticated, ]
    
    def get(self, request):
        configs = Config.objects.filter(user=request.user)
        serializer = ConfigSerializer(configs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class OrderView(APIView):
    permission_classes = [IsAuthenticated, ]
    
    # function to get the config
    def get_config(self, config_pk):
        try:
            return Config.objects.get(pk=config_pk)
        
        except Config.DoesNotExist:
            return False
    
    def get_plan(self, plan_pk):
        try:
            return Plan.objects.get(pk=plan_pk)
        
        except Plan.DoesNotExist:
            return
    
    # function to check if the last order is paid or not
    def get_last_order(self, config, request):
        try:
            last_order = config.order_configs.filter(user=request.user).last()
            
            if last_order is None:
                return True
            
            print(last_order)
            if last_order.status == False:
                return 'not paid'
            else:
                return True
        
        except Order.DoesNotExist:
            return False
    
    def get(self, request):
        
        # get the order_pk
        order_pk = request.query_params.get('order_pk')
        if order_pk is None:
            return Response({'error': 'Pick a order first'}, status=status.HTTP_400_BAD_REQUEST)
        
        # check if the order exists
        try:
            order = Order.objects.get(user=request.user, pk=order_pk)
            print(order)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    def post(self, request):
        
        serializer = OrderSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
        
            # check if the config exists
            config = self.get_config(config_pk=request.data.get('config'))
            if not config:
                return Response({'error': 'Config not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # check if the last order is paid or not
            if self.get_last_order(config, request) == 'not paid':
                return Response({'error': 'You have not paid for the last order'}, status=status.HTTP_412_PRECONDITION_FAILED)
            
            plan = self.get_plan(plan_pk=request.data.get('plan'))
            if not plan:
                return Response({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # create the order
            serializer.save(user=request.user, config=config, plan=plan)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class OrderListView(APIView):
    permission_classes = [IsAuthenticated, ]
    
    def get_config(self, config_pk):
        try:
            return Config.objects.get(pk=config_pk)
        
        except Config.DoesNotExist:
            return False
    
    def get(self, request):
        
        config_pk = request.query_params.get('config_pk')
        if config_pk is None:
            return Response({'error': 'Pick a config first'}, status=status.HTTP_400_BAD_REQUEST)
        
        # check if the config_pk is None
        if config_pk is None:
            return Response({'error': 'Pick a config first'}, status=status.HTTP_400_BAD_REQUEST)
        
        # check if the config exists
        config = self.get_config(config_pk)
        if not config:
            return Response({'error': 'Config not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # get the orders
        orders = config.order_configs.filter(user=request.user)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)     
        
class PaymentView(APIView):
    permission_classes = [IsAuthenticated, ]
    
    def get_order(self, order_pk):
        '''function to get the order'''
        
        try:
            return Order.objects.get(pk=order_pk)
        
        except Order.DoesNotExist:
            return False
    
    def get(self, request):
        
        # get the payment_pk
        payment_pk = request.query_params.get('payment_pk')
        if payment_pk is None:
            return Response({'error': 'Pick a payment first'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            payment = Payment.objects.get(user=request.user, pk=payment_pk)
        except Payment.DoesNotExist:
            return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = PaymentSerializer(payment)
        return Response(serializer.data, status=status.HTTP_200_OK)
              
    def post(self, request):
        serializer = PaymentSerializer(data=request.data)
        print('----------------------------------------------')
        
        # check if the order existss
        order = self.get_order(order_pk = request.data.get('order'))
        if not order:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # check if the serializer is valid
        if serializer.is_valid(raise_exception=True):
            serializer.save(user=request.user, order=order, config=order.config)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
class PaymentListView(APIView):
    permission_classes = [IsAuthenticated, ]
            
    def get(self, request):
        
        
        # get the config_pk
        config_pk = request.query_params.get('config_pk')        
        if config_pk is None:
            return Response({'error': 'Pick a config first'}, status=status.HTTP_400_BAD_REQUEST)
        
        # check if the config exists
        try :
            config = Config.objects.get(pk=config_pk, user=request.user)
        
        except Config.DoesNotExist:
            return Response({'error': 'Config not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # get the payments
        try:
            payments = config.config_payments.filter(config=config).order_by('-created_date')
        except Payment.DoesNotExist:
            return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # return the payments
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ----------------- Plan views -----------------   
 
class PlanlisrView(APIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request):
            
        plans = Plan.objects.all()
        serializer = PlanSerializer(plans, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        