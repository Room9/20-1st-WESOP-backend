from django.shortcuts import render

# Create your views here.
import json, re, bcrypt, jwt

from datetime     import datetime, timedelta

from django.core.exceptions import ObjectDoesNotExist
from django.http            import JsonResponse
from django.views           import View

from orders.models   import WishList, OrderList, Order, PaymentMethod, OrderStatus
from products.models import Product, ProductSelection
from users.models    import User
from my_settings     import SECRET

from users.utils     import Authorization_decorator


class OrderCheckView(View):
    @Authorization_decorator
    def get(self, request):
        try:
            user = request.user
            status_id = OrderStatus.objects.get(name='주문 전').id
            order_id= Order.objects.get(status_id=status_id).id #에러 except
            cartlists = OrderList.objects.all() 

            result=[]

            for cartlist in cartlists:
                selection_id = cartlist.product_selection_id
                select        = ProductSelection.objects.get(id=selection_id)
                status_id    =OrderStatus.objects.get(name='주문 전').id
                status_id_done = OrderStatus.objects.get(name='주문 후').id
                total        = select.price * cartlist.quantity

                Order.objects.filter(status_id=status_id).update(
                        status_id    = status_id_done, #status table에 yes 는 id 1 , no는 id 2로 설정 예정
                        address      = user.address,
                        memo         = '',
                        total_price  = total if (total >= 50000) else (total+3000), 
                        free_delivery= True if (total >= 50000) else False 
                    )
            
                order_dict = {
                    'name': Product.objects.get(id=select.product_id).name,
                    'quantity': cartlist.quantity ,
                    'total_price': Order.objects.get(id=cartlist.order_id).total_price,
                    'purchased_at': Order.objects.get(id=cartlist.order_id).purchased_at,
                    'address': User.objects.get(id=user.id).address
                } # 주문내용 어떤거 return?, address 없는 경우 입력하세요도 필요?
                result.append(order_dict)

            OrderList.objects.all().delete()

            return JsonResponse({'result':result}, status=200)

        except KeyError:
            return JsonResponse({'MESSAGE':'KEY ERROR'}, status=400)

        except OrderList.DoesNotExist:
            return JsonResponse({'MESSAGE':'noting in cart'}, status=400)