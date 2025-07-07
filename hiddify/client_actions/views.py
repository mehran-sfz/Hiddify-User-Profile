import mimetypes
from datetime import timedelta
from django.utils import timezone

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect

from adminlogs.action import add_admin_log
from client_actions.models import Config, Order, Payment
from plans.models import Plan
from task_manager.hiddify_actions import (add_new_user, delete_user,
                                          extract_uuid_from_url,
                                          send_telegram_message)
from task_manager.models import HiddifyAccessInfo, HiddifyUser
from telegram_bot.models import Telegram_Bot_Info

import task_manager.hiddify_actions as hiddify_actions

def AddConfigView(request):
    # Redirect if the user is not authenticated
    if not request.user.is_authenticated:
        return redirect('/login-register/')

    # Process POST request
    if request.method == 'POST':
        uuid = request.POST.get('uuid', '').strip()
        uuid = extract_uuid_from_url(uuid)

        # Validate UUID
        if not uuid:
            messages.error(request, 'لطفا یک UUID معتبر وارد کنید')
            return redirect('/home/')

        # Check if UUID exists in HiddifyUser
        if not HiddifyUser.objects.filter(uuid=uuid).exists():
            messages.error(request, 'کاربری با این uuid وجود ندارد')
            return redirect('/home/')

        # Attempt to create and save the Config object
        try:
            Config.objects.create(user=request.user, uuid=uuid)

            # Update user profile status
            request.user.profile.is_active = True
            request.user.profile.save()

            messages.success(request, 'کانفیگ با موفقیت ذخیره شد')

        except IntegrityError:
            messages.error(
                request, 'UUID قبلاً ثبت شده است، از یک UUID جدید استفاده کنید')

        except (ValueError, ValidationError) as e:
            messages.error(request, f'ارور در ساخت کانفیگ: {str(e)}')

        except Exception as e:
            add_admin_log(f'Error in add config {e}', 'user', request.user)
            messages.error(request, f'خطای غیرمنتظره: {str(e)}')

    # Redirect to home regardless of success or failure
    return redirect('/home/')


def BuyNewConfigView(request):
    # Redirect if the user is not authenticated
    if not request.user.is_authenticated:
        return redirect('/login-register/')

    if request.method == 'POST':
        plan_pk = request.POST.get('accountOption')
        name = request.POST.get('name')

        # Validate required fields
        if not plan_pk or not name:
            messages.error(request, 'لطفا تمامی فیلدها را پر کنید')
            return redirect('/buyconfig/')

        # Log the admin action
        admin_log = add_admin_log(
            f'User {name} buy a config.', 'add user', request.user)
        if not admin_log:
            messages.error(request, 'خطا در ثبت')
            return redirect('/buyconfig/')

        # Fetch the selected plan
        try:
            plan = Plan.objects.get(pk=plan_pk)
        except Plan.DoesNotExist:
            messages.error(request, 'پلن انتخابی موجود نیست')
            return redirect('/buyconfig/')
        except Exception as e:
            messages.error(request, 'خطا در بازیابی پلن انتخابی')
            return redirect('/buyconfig/')
        
        # check the maximum number of configs for the user
        if request.user.profile.config_limitation <= Config.objects.filter(user=request.user).count():
            messages.error(
                request, 'شما به حداکثر تعداد کانفیگ مجاز رسیده‌اید، برای خرید کانفیگ جدید، لطفا با ادمین تماس بگیرید.')
            return redirect('/buyconfig/')
        
        # check that passed 5 minutes from last config creation to create a new config
        last_config = Config.objects.filter(user=request.user).last()
        if last_config:
            time_difference = timezone.now() - last_config.updated_date
            if time_difference < timedelta(minutes=5):
                messages.error(
                    request, 'شما باید حداقل 5 دقیقه بین ایجاد کانفیگ‌ها فاصله بگذارید.')
                return redirect('/buyconfig/')
    
        # get the orders for the user and this config if exist to check if the user has a pending order
        unpaid_orders = Order.objects.filter(
            user=request.user, status=False).order_by('-created_date')

        if unpaid_orders.exists():
            messages.error(
                request, 'شما یک سفارش پرداخت نشده دارید، لطفا آن را پرداخت کنید یا حذف کنید.')
            return redirect('/buyconfig/')
    

        # Call external function to add the new user and receive the UUID
        try:
            hiddify_access_info = HiddifyAccessInfo.objects.latest('created_date')
        except HiddifyAccessInfo.DoesNotExist:
            messages.error(request, 'خطای در سایت')
            return redirect('/buyconfig/')
        except Exception as e:
            messages.error(request, 'خطای در سایت')
            add_admin_log(
                            f'Error in add hiddify user in client acction view - {e}', 'user', request.user)
            return redirect('/buyconfig/')
        
        # Extract necessary information from HiddifyAccessInfo
        hiddify_api_key = hiddify_access_info.hiddify_api_key
        panel_admin_domain = hiddify_access_info.panel_admin_domain
        admin_proxy_path = hiddify_access_info.admin_proxy_path

        # Call the function to add a new user
        add_new_user_status = add_new_user(
            name=name,
            duration=plan.duration,
            trafic=plan.trafic,
            hiddify_api_key=hiddify_api_key,
            admin_proxy_path=admin_proxy_path,
            panel_admin_domain=panel_admin_domain,
            )
            
        if not add_new_user_status:
            messages.error(
                request, 'خطا در ارتباط با سرور لطفا دوباره تلاش کنید')
            return redirect('/buyconfig/')

        # Create the new HiddifyUser
        try:
            hiddifyuser = HiddifyUser.objects.create(uuid=add_new_user_status['uuid'],
                                                     name=add_new_user_status['name'],
                                                     package_days=add_new_user_status['package_days'],
                                                     usage_limit_GB=add_new_user_status['usage_limit_GB'],)
        except Exception as e:
            add_admin_log(
                f'Error in add hiddify user {e}', 'user', request.user)
            messages.error(
                request, 'خطا در ذخیره کاربر، لطفا با ادمین تماس بگیرید')
            return redirect('/buyconfig/')

        # Create the new config
        try:
            config = Config.objects.create(
                user=request.user, uuid=add_new_user_status['uuid'])
            messages.success(request, 'کانفیگ با موفقیت ذخیره شد')
        except Exception as e:
            messages.error(
                request, 'خطا در ذخیره کانفیگ، لطفا با ادمین تماس بگیرید')
            return redirect('/buyconfig/')

        # Create the new order
        try:
            order = Order.objects.create(
                user=request.user, config=Config.objects.get(user=request.user, uuid=add_new_user_status['uuid']), plan=plan)
            order.save()
            messages.success(request, 'سفارش با موفقیت ثبت شد. برای فعال شدن کانفیگ یک دقیقه صبر کنید.')
            
            # send telegram message to admin trough html message template
            telegram_bot_info = Telegram_Bot_Info.objects.first()
            if telegram_bot_info:
                telegram_message = f"""
                <b>سفارش جدید ثبت شد</b>
                <b>نام کاربر:</b> {name}
                <b>UUID:</b> {add_new_user_status['uuid']}
                <b>طول دوره:</b> {plan.duration} days
                <b>ترافیک:</b> {plan.trafic} GB
                <b>شماره سفارش:</b> {order.pk}
                """            
            respons = send_telegram_message(
                token=telegram_bot_info.token,
                chat_id=telegram_bot_info.admin_user_id,
                message=telegram_message)
            
            if not respons:
                add_admin_log(
                    f'Error in send telegram message for new order {order.pk}', 'user', request.user)
            
            
            
        except Exception as e:


            delete_user(uuid=add_new_user_status['uuid'],
                        hiddify_api_key=hiddify_api_key,
                        admin_proxy_path=admin_proxy_path,
                        panel_admin_domain=panel_admin_domain
                        )
            
            config.delete()

            add_admin_log(f'Error in add order {e}', 'user', request.user)
            messages.error(
                request, 'خطا در ذخیره سفارش، لطفا با ادمین تماس بگیرید')
            return redirect('/buyconfig/')

        messages.success(
            request, 'کانفیگ و سفارش در حال پردازش هستند، لطفا کمی صبر کنید.')
        return redirect('/home/')


def AddOrderView(request):
    if not request.user.is_authenticated:
        return redirect('/login-register/')

    if request.method == 'POST':
        selected_plan_id = request.POST.get('accountOption')
        selected_plan_config_uuid = request.POST.get('config_uuid')
        if selected_plan_id and selected_plan_config_uuid:

            try:
                plan = Plan.objects.get(pk=selected_plan_id)
                config = Config.objects.get(
                    user=request.user, uuid=selected_plan_config_uuid)
                hiddify_user = HiddifyUser.objects.get(
                    uuid=selected_plan_config_uuid)

            except (Plan.DoesNotExist, Config.DoesNotExist, HiddifyUser.DoesNotExist) as e:
                messages.error(request, 'خطا در گرفتن اطلاعات توسط کاربر')
                return redirect('/home/')

            except Exception as e:
                add_admin_log(f'Error in add order {e}', 'user', request.user)
                messages.error(request, 'خطای غیرمنتظره')
                return redirect('/home/')

            # get the last order for the user and this config if exist
            last_order = Order.objects.filter(
                user=request.user, config=config).last()

            if last_order and not last_order.status:
                messages.error(request, 'شما یک سفارش پرداخت نشده دارید')
                return redirect('/home/')
            elif last_order and last_order.pending:
                messages.error(request, 'سفارش قبلی شما در حال انجام است')
                return redirect('/home/')

            # add a new order
            order = Order.objects.create(
                user=request.user, config=config, plan=plan)
            order.save()

            messages.success(request, 'سفارش با موفقیت ثبت شد')
            
            
            # send telegram message to admin trough html message template
            telegram_bot_info = Telegram_Bot_Info.objects.first()
            if telegram_bot_info:
                telegram_message = f"""
                <b>سفارش جدید ثبت شد</b>
                <b>شماره کاربر:</b> {request.user.phone_number}
                <b>نام کانفیگ:</b> {hiddify_user.name}
                <b>UUID:</b> {selected_plan_config_uuid}
                <b>پلن انتخاب شده:</b> {plan}
                <b>شماره سفارش:</b> {order.pk}
                """
            
            respons = send_telegram_message(
                token=telegram_bot_info.token,
                chat_id=telegram_bot_info.admin_user_id,
                message=telegram_message)
            
            if not respons:
                add_admin_log(
                    f'Error in send telegram message for new order {order.pk}', 'user', request.user)
            
            
            return redirect('/home/')


def OrderEditView(request):
    # Redirect if the user is not authenticated
    if not request.user.is_authenticated:
        return redirect('/login-register/')

    if request.method == 'POST':
        selected_plan = request.POST.get('selected_plan')
        selected_order = request.POST.get('selected_order')
        selected_uuid = request.POST.get('config_uuid')
        action = request.POST.get('action')

        # Check if all required fields are provided
        if not (selected_order and selected_plan and action and selected_uuid):
            messages.error(request, 'لطفا تمامی فیلدها را پر کنید')
            return redirect('/home/')

        try:
            # Handle 'edit' action
            if action == 'edit':
                # Fetch the relevant order
                order = Order.objects.get(
                    config__uuid=selected_uuid, order_peak=selected_order)

                # Update the plan for the order
                order.plan = Plan.objects.get(pk=selected_plan)
                order.save()
                
                
                # send telegram message to admin trough html message template
                telegram_bot_info = Telegram_Bot_Info.objects.first()
                if telegram_bot_info:
                    telegram_message = f"""
                    <b>سفارش ویرایش شد</b>
                    <b>شماره کاربر:</b> {request.user.phone_number}
                    <b>پلن جدید:</b> {order.plan}
                    <b>UUID کانفیگ:</b> {selected_uuid}
                    <b>شماره سفارش:</b> {order.pk}
                    """
                    
                    respons = send_telegram_message(
                        token=telegram_bot_info.token,
                        chat_id=telegram_bot_info.admin_user_id,
                        message=telegram_message)
                    if not respons: 
                        add_admin_log(
                            f'Error in send telegram message for edit order {order.pk}', 'user', request.user)                
                
                messages.success(request, 'سفارش با موفقیت ویرایش شد')
                
            else:
                messages.error(request, 'عملیات نامعتبر است')

        # Handle cases where the order or plan does not exist
        except (Order.DoesNotExist, Plan.DoesNotExist):
            messages.error(request, 'سفارش یا پلن پیدا نشد')

        # Handle any validation or value errors
        except (ValueError, ValidationError) as e:
            messages.error(request, f'خطا در ویرایش سفارش: {str(e)}')

        except Exception as e:
            add_admin_log(f'Error in order edit {e}', 'user', request.user)
            messages.error(request, f'خطای ناشناخته: {str(e)}')

    # Redirect to home after processing
    return redirect('/home/')


def DeleteOrderView(request):
    # Redirect if the user is not authenticated
    if not request.user.is_authenticated:
        return redirect('/login-register/')

    if request.method == 'POST':
        order_pk = request.POST.get('order_pk')

        # Validate if order_pk is provided
        if not order_pk:
            messages.error(request, 'سفارش پیدا نشد')
            return redirect('/orders/')

        try:
            # Retrieve the order for the logged-in user
            order = Order.objects.get(user=request.user, pk=order_pk)

            # Check if the order can be deleted
            if order.status == 'paid' or hasattr(order, 'order_payment'):
                messages.error(
                    request, 'سفارش پرداخت شده است و نمی‌تواند حذف شود')
            elif not order.pending:
                messages.error(
                    request, 'سفارش اعمال شده است و نمی‌تواند حذف شود')
            else:
                # Delete the order
                order.delete()
            
                # delete created config and hiddify user
                config = Config.objects.get(user=request.user, uuid=order.config.uuid)
                config.delete()
                
                # delete hiddify user with tools delete_user
                try:
                    
                    hiddify_access_info = HiddifyAccessInfo.objects.latest('created_date')
                    hiddify_api_key = hiddify_access_info.hiddify_api_key
                    panel_admin_domain = hiddify_access_info.panel_admin_domain
                    admin_proxy_path = hiddify_access_info.admin_proxy_path
                    
                    delete_user(uuid=order.config.uuid,
                                hiddify_api_key=hiddify_api_key,
                                admin_proxy_path=admin_proxy_path,
                                panel_admin_domain=panel_admin_domain
                                )
                    
                    
                except HiddifyAccessInfo.DoesNotExist:
                    messages.error(request, 'خطای در سایت')
                    
                except Exception as e:
                    add_admin_log(f'Error in delete hiddify user {e}', 'user', request.user)
                    messages.error(request, f'خطا در حذف کاربر: {str(e)}')
                
                
                messages.success(request, 'سفارش با موفقیت حذف شد')

        except Order.DoesNotExist:
            messages.error(request, 'سفارش پیدا نشد')

        except Exception as e:
            add_admin_log(f'Error in delete order {e}', 'user', request.user)
            messages.error(request, f'خطا در حذف سفارش: {str(e)}')

        # Redirect to the orders page after processing
        return redirect('/orders/')


def PaymentView(request):
    # Redirect if the user is not authenticated
    if not request.user.is_authenticated:
        return redirect('/login-register/')

    if request.method == 'POST':
        order_pk = request.POST.get('order_pk')
        payment_picture = request.FILES.get('payment_picture')
        tracking_code = request.POST.get('tracking_code')
        config_uuid = request.POST.get('config_uuid')

        # Validate required fields
        if not (order_pk and config_uuid and (payment_picture or tracking_code)):
            messages.error(request, 'لطفا تمامی فیلدها را پر کنید')
            return redirect('/home/')

        try:
            # Create the payment entry
            payment = Payment.objects.create(
                user=request.user,
                config=Config.objects.get(user=request.user, uuid=config_uuid),
                order=Order.objects.get(user=request.user, pk=order_pk),
                screenshot=payment_picture,
                tracking_code=tracking_code
            )
            
            
            
            # send telegram message to admin trough html message template
            telegram_bot_info = Telegram_Bot_Info.objects.first()
            if telegram_bot_info:
                telegram_message = f"""
                <b>پرداخت جدید ثبت شد</b>
                <b>شماره کاربر:</b> {request.user.phone_number}
                <b>UUID کانفیگ:</b> {config_uuid}
                <b>شماره سفارش:</b> {order_pk}
                <b>کد رهگیری:</b> {tracking_code}
                <b>تصویر پرداخت:</b> {'وجود دارد' if payment_picture else 'ندارد'}
                <b>شماره پرداخت:</b> {payment.pk}
                """
            
            respons = send_telegram_message(
                token=telegram_bot_info.token,
                chat_id=telegram_bot_info.admin_user_id,
                message=telegram_message)
            if not respons:
                add_admin_log(
                    f'Error in send telegram message for new payment {payment.pk}', 'user', request.user)
            
            messages.success(request, 'پرداخت با موفقیت ثبت شد')

        except (Order.DoesNotExist, Config.DoesNotExist):
            messages.error(request, 'سفارش یا کانفیگ پیدا نشد')

        except IntegrityError as e:
            messages.error(request, 'یک پرداخت قبلا ثبت شده است')

        except ValidationError as e:
            messages.error(request, f'خطا در ذخیره پرداخت')

        except Exception as e:
            messages.error(request, f'خطای ناشناخته')

    # Redirect to home after processing
    return redirect('/home/')


def DeleteOrderAdminView(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('/login-register/')

    if request.method == 'POST':
        order_pk = request.POST.get('order_pk')

        if not order_pk:
            messages.error(request, 'سفارش پیدا نشد')
            return redirect('/admin-panel/orders/')
                    
        try:
            order = Order.objects.get(pk=order_pk)
            config = Config.objects.get(user=order.user, uuid=order.config.uuid)
            hiddify_access_info = HiddifyAccessInfo.objects.latest('created_date')
                        
            # if the config of that order created before 60 minutes, delete that config and hiddify user
            if (config.updated_date > timezone.now() - timedelta(minutes=60)) and not order.status:
                
                status = hiddify_actions.delete_user(
                    uuid=order.config.uuid,
                    hiddify_api_key=hiddify_access_info.hiddify_api_key,
                    admin_proxy_path=hiddify_access_info.admin_proxy_path,
                    panel_admin_domain=hiddify_access_info.panel_admin_domain,
                )
                if status:
                    order.delete()
                    config.delete()
                    messages.success(request, 'سفارش و کانفیگ با موفقیت حذف شد')
                else:
                    messages.error(request, 'خطا در حذف کاربر در هیدیفای')
            
            elif not order.pending and not order.status:
                
                status = hiddify_actions.on_off_user(
                    uuid=order.config.uuid,
                    hiddify_api_key=hiddify_access_info.hiddify_api_key,
                    admin_proxy_path=hiddify_access_info.admin_proxy_path,
                    panel_admin_domain=hiddify_access_info.panel_admin_domain,
                    enable = False
                )
            
                if not status:
                    messages.error(request, 'خطا در غیرفعال کردن کاربر در هیدیفای')
                    return redirect('/admin-panel/orders/')
                else:
                    messages.success(request, 'کاربر در هیدیفای غیرفعال شد')            
            
                order.delete()
                messages.warning(request, 'سفارش با موفقیت حذف شد')
            
            else:
                messages.error(request, 'این سفارش را در حال حاضر نمیتوان حذف کرد')
            
        except Config.DoesNotExist:
            messages.error(request, 'کانفیگ پیدا نشد')
            return redirect('/admin-panel/orders/')

        except Order.DoesNotExist:
            messages.error(request, 'سفارش پیدا نشد')
            
        except HiddifyAccessInfo.DoesNotExist:
            messages.error(request, 'کانفیگ در هیدیفای پیدا نشد')
            return redirect('/admin-panel/orders/')

        except Exception as e:
            add_admin_log(f'Error in delete order {e}', 'admin', request.user)
            messages.error(request, f'خطا در حذف سفارش: {str(e)}')

    return redirect('/admin-panel/orders/')


def ConfirmOrderAdminView(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('/login-register/')

    if request.method == 'POST':
        payment_pk = request.POST.get('payment_pk')
        confirm_payment = request.POST.get('confirm_payment')

        if not payment_pk or not confirm_payment:
            messages.error(request, 'خطا در اطلاعات وارد شده')
            return redirect('/admin-panel/orders/')

        try:
            payment = Payment.objects.get(pk=payment_pk)
            if confirm_payment == 'true':
                payment.validated = True
                payment.order.status = True
                payment.save()
                payment.order.save()
                messages.success(request, 'سفارش تایید شد')

            elif confirm_payment == 'false':
                
                
                # disable the user in hiddify using tools.on_off_user
                hiddify_access_info = HiddifyAccessInfo.objects.latest('created_date')
                hiddify_api_key = hiddify_access_info.hiddify_api_key
                panel_admin_domain = hiddify_access_info.panel_admin_domain
                admin_proxy_path = hiddify_access_info.admin_proxy_path
                status = hiddify_actions.on_off_user(
                    uuid=payment.config.uuid,
                    hiddify_api_key=hiddify_api_key,
                    admin_proxy_path=admin_proxy_path,
                    panel_admin_domain=panel_admin_domain,
                    enable = False
                )
                if not status:
                    messages.error(request, 'خطا در غیرفعال کردن کاربر در هیدیفای')
                    return redirect('/admin-panel/orders/')
                
                
                payment.delete()
                messages.warning(request, 'پرداخت حذف شد')

        except Order.DoesNotExist:
            messages.error(request, 'سفارش پیدا نشد')

        except Exception as e:
            add_admin_log(f'Error in confirm order {e}', 'admin', request.user)
            messages.error(request, f'خطا در تایید سفارش: {str(e)}')

    return redirect('/admin-panel/orders/')


@login_required
def serve_payment_screenshot(request, payment_id):
    """
    this view serves the payment screenshot file securely
    using Nginx's internal redirect feature.
    It ensures that only the user who made the payment or an admin can access the file.
    """
    # 1. find the payment object by ID
    payment = get_object_or_404(Payment, pk=payment_id)

    # 2. ensure that the payment has a screenshot
    if not payment.screenshot:
        raise Http404("اسکرین‌شاتی برای این پرداخت ثبت نشده است.")

    # 3. check if the user has permission to access the screenshot
    # current user must be the one who made the payment or an admin
    user = request.user
    if user == payment.user or user.is_staff:
        # 4. nginx will serve the file from the media directory
        # the file_path is the relative path to the media directory
        # for example: 'screenshots/2024/07/05/img.png'
        
        file_path = payment.screenshot.name
        
        # generate the HttpResponse with the appropriate headers
        response = HttpResponse()
        
        # set the content type based on the file extension
        content_type, _ = mimetypes.guess_type(file_path)
        response['Content-Type'] = content_type or 'application/octet-stream'

        # set the content disposition to attachment to prompt download
        # response['Content-Disposition'] = f'attachment; filename="{file_path.split("/")[-1]}"'
        response['X-Accel-Redirect'] = f'/protected_media/{file_path}'

        return response
    else:
        # 5. if the user does not have permission, return a forbidden response
        return HttpResponseForbidden("شما اجازه دسترسی به این فایل را ندارید.")