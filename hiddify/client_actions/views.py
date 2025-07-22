import mimetypes
from datetime import timedelta
from django.utils import timezone

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db import transaction
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect

from adminlogs.action import add_admin_log
from client_actions.models import Config, Order, Payment
from plans.models import Plan
from task_manager.hiddify_actions import (
    add_new_user,
    delete_user,
    extract_uuid_from_url,
    send_telegram_message,
)
from task_manager.models import HiddifyAccessInfo, HiddifyUser
from telegram_bot.models import Telegram_Bot_Info

import task_manager.hiddify_actions as hiddify_actions


@transaction.atomic
def AddConfigView(request):
    # Redirect if the user is not authenticated
    if not request.user.is_authenticated:
        return redirect("/login-register/")

    # Process POST request
    if request.method == "POST":
        uuid = request.POST.get("uuid", "").strip()
        
        # It's better to call the extraction function inside the POST block
        if uuid:
            uuid = extract_uuid_from_url(uuid)

        # Validate UUID
        if not uuid:
            messages.error(request, "لطفا یک UUID معتبر وارد کنید")
            return redirect("/home/")

        # Check if UUID exists in HiddifyUser
        if not HiddifyUser.objects.filter(uuid=uuid).exists():
            messages.error(request, "کاربری با این uuid در سیستم وجود ندارد")
            return redirect("/home/")
            
        # Check if the config already exists for this user or any user
        if Config.objects.filter(uuid=uuid).exists():
            messages.error(request, "این کانفیگ قبلاً در سیستم ثبت شده است.")
            return redirect("/home/")

        # Attempt to create and save the Config object
        try:
            # Both operations are now inside a single atomic transaction
            Config.objects.create(user=request.user, uuid=uuid)

            # Update user profile status
            if not request.user.profile.is_active:
                request.user.profile.is_active = True
                request.user.profile.save()

            messages.success(request, "کانفیگ با موفقیت به حساب شما اضافه شد.")

        except Exception as e:
            # Catch any other unexpected errors during creation
            add_admin_log(f"Error in add config for user {request.user.email}: {e}", "error", request.user)
            messages.error(request, "خطای پیش‌بینی‌نشده‌ای هنگام اضافه کردن کانفیگ رخ داد.")

    # Redirect to home
    return redirect("/home/")


@transaction.atomic
def BuyNewConfigView(request):
    if not request.user.is_authenticated:
        return redirect("/login-register/")

    if request.method != "POST":
        # If the method is GET, redirect to the purchase page (or you can render the template).
        return redirect("/buyconfig/")

    # --- Step 1: Input Validation ---
    plan_pk = request.POST.get("plan")
    name = request.POST.get("name")

    if not plan_pk or not name:
        messages.error(request, "لطفا تمامی فیلدها را پر کنید")
        return redirect("/buyconfig/")

    elif len(name) < 3 or len(name) > 20:
        messages.error(request, "نام کانفیگ باید بین 3 تا 20 کاراکتر باشد")
        return redirect("/buyconfig/")

    # --- Step 2: Prerequisite and Rule Checks ---
    try:
        plan = Plan.objects.get(pk=plan_pk)
        hiddify_access_info = HiddifyAccessInfo.objects.latest("created_date")
    except Plan.DoesNotExist:
        messages.error(request, "پلن انتخابی وجود ندارد.")
        return redirect("/buyconfig/")
    except HiddifyAccessInfo.DoesNotExist:
        messages.error(
            request, "اطلاعات اتصال به سرور پیدا نشد. لطفاً با مدیریت تماس بگیرید."
        )
        return redirect("/buyconfig/")

    # Check the user's config limit
    if (
        request.user.profile.config_limitation
        <= Config.objects.filter(user=request.user).count()
    ):
        messages.error(
            request,
            "شما به حداکثر تعداد کانفیگ‌های مجاز رسیده‌اید، برای درخواست افزایش تعداد کانفیگ‌ها با مدیریت تماس بگیرید.",
        )
        return redirect("/buyconfig/")

    # Check for the 5-minute interval since the last purchase
    last_config = (
        Config.objects.filter(user=request.user).order_by("-created_date").first()
    )
    if last_config and (
        timezone.now() - last_config.created_date < timedelta(minutes=5)
    ):
        messages.error(request, "شما باید حداقل 5 دقیقه بین ایجاد کانفیگ‌ها صبر کنید.")
        return redirect("/buyconfig/")

    # Check for any unpaid orders
    if Order.objects.filter(user=request.user, status=False).exists():
        messages.error(
            request, "شما یک سفارش پرداخت نشده دارید. لطفاً آن را پرداخت یا لغو کنید."
        )
        return redirect("/buyconfig/")

    # --- Step 3: Execute Main Operations (API and Database) ---
    # <<< Improvement 2: Unified error handling. If any part fails, the entire operation is rolled back.
    hiddify_user_data = None
    try:
        # 1. Add a new user in Hiddify
        
        hiddify_user_data = add_new_user(
            name=name,
            duration=plan.duration,
            trafic=plan.trafic,
            hiddify_api_key=hiddify_access_info.hiddify_api_key,
            admin_proxy_path=hiddify_access_info.admin_proxy_path,
            panel_admin_domain=hiddify_access_info.panel_admin_domain,
        )
        if not hiddify_user_data:
            messages.error(
                request, "خطا در ایجاد کاربر جدید در سایت. لطفاً با مدیریت تماس بگیرید."
            )
            # Since nothing is saved to the DB yet, a simple return is sufficient.
            return redirect("/buyconfig/")

        # 2. Create records in the database (within a transaction)
        # Thanks to @transaction.atomic, these three operations are performed together.
        HiddifyUser.objects.create(
            uuid=hiddify_user_data["uuid"],
            name=hiddify_user_data["name"],
            package_days=hiddify_user_data["package_days"],
            usage_limit_GB=hiddify_user_data["usage_limit_GB"],
        )

        config = Config.objects.create(
            user=request.user,
            uuid=hiddify_user_data["uuid"],
        )

        order = Order.objects.create(user=request.user, config=config, plan=plan)

        # 3. Log the action and send a notification
        add_admin_log(
            f'User {name} bought a new config with UUID {hiddify_user_data["uuid"]}.',
            "add user",
            request.user,
        )

        telegram_bot_info = Telegram_Bot_Info.objects.first()
        if telegram_bot_info:
            telegram_message = f"""
<b>New Order Submitted</b>
<b>User Name:</b> {name}
<b>UUID:</b> {hiddify_user_data['uuid']}
<b>Duration:</b> {plan.duration} days
<b>Traffic:</b> {plan.trafic} GB
<b>Order ID:</b> {order.pk}
"""
            send_telegram_message(
                token=telegram_bot_info.token,
                chat_id=telegram_bot_info.admin_user_id,
                message=telegram_message,
            )

        # <<< Improvement 3: A single, clear success message at the end.
        messages.success(
            request, "سفارش شما با موفقیت ثبت شد. کانفیگ در حال پردازش است."
        )
        return redirect("/home/")

    except Exception as e:
        # If an error occurs at any stage of the try block (API or DB),
        # the database transaction is automatically rolled back.
        add_admin_log(
            f"Error during config purchase for user {request.user.email}: {e}",
            "error",
            request.user,
        )

        # We only delete the Hiddify user if it was actually created before the error.
        if hiddify_user_data and hiddify_user_data.get("uuid"):
            delete_user(
                uuid=hiddify_user_data["uuid"],
                hiddify_api_key=hiddify_access_info.hiddify_api_key,
                admin_proxy_path=hiddify_access_info.admin_proxy_path,
                panel_admin_domain=hiddify_access_info.panel_admin_domain,
            )
            add_admin_log(
                f'Rolled back Hiddify user creation for UUID {hiddify_user_data["uuid"]}.',
                "delete user",
                request.user,
            )

        messages.error(request, "خطا در ثبت سفارش شما. لطفاً با پشتیبانی تماس بگیرید.")
        return redirect("/buyconfig/")


@transaction.atomic 
def AddOrderView(request):
    if not request.user.is_authenticated:
        return redirect("/login-register/")
    
    if request.method != "POST":
        return redirect("/home/")  # Redirect if not a POST request

    # --- Step 1: Input Validation ---
    plan_id = request.POST.get("plan")
    config_uuid = request.POST.get("config_uuid")

    if not plan_id or not config_uuid:
        messages.error(request, "اطلاعات ارسالی ناقص است. لطفا دوباره تلاش کنید.")
        return redirect("/home/")

    # --- Step 2: Fetch Objects and Check Rules ---
    try:
        plan = Plan.objects.get(pk=plan_id)
        config = Config.objects.get(user=request.user, uuid=config_uuid)
        # HiddifyUser is only needed for the Telegram message, so we fetch it here.
        hiddify_user = HiddifyUser.objects.get(uuid=config_uuid)

    except (Plan.DoesNotExist, Config.DoesNotExist, HiddifyUser.DoesNotExist):
        messages.error(request, "پلن یا کانفیگ انتخاب شده یافت نشد.")
        return redirect("/home/")

    # Improvement 2: More efficient check for existing orders using .exists()
    if Order.objects.filter(user=request.user, status=False).exists():
        messages.error(request, "شما یک سفارش پرداخت نشده دارید.")
        return redirect("/home/")

    if Order.objects.filter(user=request.user, config=config, pending=True).exists():
        messages.error(request, "سفارش قبلی شما برای این کانفیگ در حال بررسی است.")
        return redirect("/home/")

    # --- Step 3: Execute Action ---
    try:
        # Create the new order. .create() automatically saves the object.
        order = Order.objects.create(user=request.user, config=config, plan=plan)
        # Improvement 3: The call to order.save() is redundant and has been removed.

        messages.success(request, "سفارش شما با موفقیت ثبت شد.")

        # Send Telegram notification
        telegram_bot_info = Telegram_Bot_Info.objects.first()
        if telegram_bot_info:
            telegram_message = f"""
<b>Config Renewal Order</b>
<b>User Email:</b> {request.user.email}
<b>Config Name:</b> {hiddify_user.name}
<b>UUID:</b> {config_uuid}
<b>Selected Plan:</b> {plan}
<b>Order ID:</b> {order.pk}
"""
            response = send_telegram_message(
                token=telegram_bot_info.token,
                chat_id=telegram_bot_info.admin_user_id,
                message=telegram_message,
            )
            if not response:
                add_admin_log(
                    f"Failed to send Telegram message for order {order.pk}.",
                    "error",
                    request.user,
                )

        return redirect("/home/")

    except Exception as e:
        # This will catch any unexpected errors during order creation or notification.
        add_admin_log(
            f"Unexpected error in AddOrderView for user {request.user.email}: {e}",
            "error",
            request.user,
        )
        messages.error(request, "خطای پیش‌ بینی‌ نشده‌ای رخ داد. لطفا دوباره تلاش کنید.")
        return redirect("/home/")


def OrderEditView(request):
    # Redirect if the user is not authenticated
    if not request.user.is_authenticated:
        return redirect("/login-register/")

    if request.method == "POST":
        selected_plan = request.POST.get("selected_plan")
        selected_order = request.POST.get("selected_order")
        selected_uuid = request.POST.get("config_uuid")
        action = request.POST.get("action")

        # Check if all required fields are provided
        if not (selected_order and selected_plan and action and selected_uuid):
            messages.error(request, "لطفا تمامی فیلدها را پر کنید")
            return redirect("/home/")

        try:
            # Handle 'edit' action
            if action == "edit":
                # Fetch the relevant order
                order = Order.objects.get(
                    config__uuid=selected_uuid, order_peak=selected_order
                )

                # Update the plan for the order
                order.plan = Plan.objects.get(pk=selected_plan)
                order.save()

                # send telegram message to admin trough html message template
                telegram_bot_info = Telegram_Bot_Info.objects.first()
                if telegram_bot_info:
                    telegram_message = f"""
<b>Order Edited</b>
<b>User ID:</b> {request.user.email}
<b>New Plan:</b> {order.plan}
<b>Config UUID:</b> {selected_uuid}
<b>Order Number:</b> {order.pk}
"""

                    respons = send_telegram_message(
                        token=telegram_bot_info.token,
                        chat_id=telegram_bot_info.admin_user_id,
                        message=telegram_message,
                    )
                    if not respons:
                        add_admin_log(
                            f"Error in send telegram message for edit order {order.pk}",
                            "user",
                            request.user,
                        )

                messages.success(request, "سفارش با موفقیت ویرایش شد")

            else:
                messages.error(request, "عملیات نامعتبر است")

        # Handle cases where the order or plan does not exist
        except (Order.DoesNotExist, Plan.DoesNotExist):
            messages.error(request, "سفارش یا پلن پیدا نشد")

        # Handle any validation or value errors
        except (ValueError, ValidationError) as e:
            messages.error(request, f"خطا در ویرایش سفارش: {str(e)}")

        except Exception as e:
            add_admin_log(f"Error in order edit {e}", "user", request.user)
            messages.error(request, f"خطای ناشناخته: {str(e)}")

    # Redirect to home after processing
    return redirect("/home/")


def DeleteOrderView(request):
    # Redirect if the user is not authenticated
    if not request.user.is_authenticated:
        return redirect("/login-register/")

    if request.method == "POST":
        order_pk = request.POST.get("order_pk")

        # Validate if order_pk is provided
        if not order_pk:
            messages.error(request, "سفارش پیدا نشد")
            return redirect("/orders/")

        try:
            # Retrieve the order for the logged-in user
            order = Order.objects.get(user=request.user, pk=order_pk)

            # Check if the order can be deleted
            if order.status == "paid" or hasattr(order, "order_payment"):
                messages.error(request, "سفارش پرداخت شده است و نمی‌تواند حذف شود")
            elif not order.pending:
                messages.error(request, "سفارش اعمال شده است و نمی‌تواند حذف شود")
            else:
                # Delete the order
                order.delete()

                # delete created config and hiddify user
                config = Config.objects.get(user=request.user, uuid=order.config.uuid)
                config.delete()

                # delete hiddify user with tools delete_user
                try:

                    hiddify_access_info = HiddifyAccessInfo.objects.latest(
                        "created_date"
                    )
                    hiddify_api_key = hiddify_access_info.hiddify_api_key
                    panel_admin_domain = hiddify_access_info.panel_admin_domain
                    admin_proxy_path = hiddify_access_info.admin_proxy_path

                    delete_user(
                        uuid=order.config.uuid,
                        hiddify_api_key=hiddify_api_key,
                        admin_proxy_path=admin_proxy_path,
                        panel_admin_domain=panel_admin_domain,
                    )

                except HiddifyAccessInfo.DoesNotExist:
                    messages.error(request, "خطای در سایت")

                except Exception as e:
                    add_admin_log(
                        f"Error in delete hiddify user {e}", "user", request.user
                    )
                    messages.error(request, f"خطا در حذف کاربر: {str(e)}")

                messages.success(request, "سفارش با موفقیت حذف شد")

        except Order.DoesNotExist:
            messages.error(request, "سفارش پیدا نشد")

        except Exception as e:
            add_admin_log(f"Error in delete order {e}", "user", request.user)
            messages.error(request, f"خطا در حذف سفارش: {str(e)}")

        # Redirect to the orders page after processing
        return redirect("/orders/")


def PaymentView(request):
    # Redirect if the user is not authenticated
    if not request.user.is_authenticated:
        return redirect("/login-register/")

    if request.method == "POST":
        order_pk = request.POST.get("order_pk")
        payment_picture = request.FILES.get("payment_picture")
        tracking_code = request.POST.get("tracking_code")
        config_uuid = request.POST.get("config_uuid")

        # Validate required fields
        if not (order_pk and config_uuid and (payment_picture or tracking_code)):
            messages.error(request, "لطفا تمامی فیلدها را پر کنید")
            return redirect("/home/")

        try:
            # Create the payment entry
            payment = Payment.objects.create(
                user=request.user,
                config=Config.objects.get(user=request.user, uuid=config_uuid),
                order=Order.objects.get(user=request.user, pk=order_pk),
                screenshot=payment_picture,
                tracking_code=tracking_code,
            )

            # send telegram message to admin trough html message template
            telegram_bot_info = Telegram_Bot_Info.objects.first()
            if telegram_bot_info:
                telegram_message = f"""
<b>New Payment Registered</b>
<b>User ID:</b> {request.user.email}
<b>Config UUID:</b> {config_uuid}
<b>Order Number:</b> {order_pk}
<b>Tracking Code:</b> {tracking_code}
<b>Payment Picture:</b> {'Exists' if payment_picture else 'Not available'}
<b>Payment ID:</b> {payment.pk}
"""

            respons = send_telegram_message(
                token=telegram_bot_info.token,
                chat_id=telegram_bot_info.admin_user_id,
                message=telegram_message,
            )
            if not respons:
                add_admin_log(
                    f"Error in send telegram message for new payment {payment.pk}",
                    "user",
                    request.user,
                )

            messages.success(request, "پرداخت با موفقیت ثبت شد")

        except (Order.DoesNotExist, Config.DoesNotExist):
            messages.error(request, "سفارش یا کانفیگ پیدا نشد")

        except IntegrityError as e:
            messages.error(request, "یک پرداخت قبلا ثبت شده است")

        except ValidationError as e:
            messages.error(request, f"خطا در ذخیره پرداخت")

        except Exception as e:
            messages.error(request, f"خطای ناشناخته")

    # Redirect to home after processing
    return redirect("/home/")


def DeleteOrderAdminView(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect("/login-register/")

    if request.method == "POST":
        order_pk = request.POST.get("order_pk")

        if not order_pk:
            messages.error(request, "سفارش پیدا نشد")
            return redirect("/admin-panel/orders/")

        try:
            order = Order.objects.get(pk=order_pk)
            config = Config.objects.get(user=order.user, uuid=order.config.uuid)
            hiddify_access_info = HiddifyAccessInfo.objects.latest("created_date")

            # if the config of that order created before 60 minutes, delete that config and hiddify user
            if (
                config.updated_date > timezone.now() - timedelta(minutes=60)
            ) and not order.status:

                status = hiddify_actions.delete_user(
                    uuid=order.config.uuid,
                    hiddify_api_key=hiddify_access_info.hiddify_api_key,
                    admin_proxy_path=hiddify_access_info.admin_proxy_path,
                    panel_admin_domain=hiddify_access_info.panel_admin_domain,
                )
                if status:
                    order.delete()
                    config.delete()
                    messages.success(request, "سفارش و کانفیگ با موفقیت حذف شد")
                else:
                    messages.error(request, "خطا در حذف کاربر در هیدیفای")

            elif not order.pending and not order.status:

                status = hiddify_actions.on_off_user(
                    uuid=order.config.uuid,
                    hiddify_api_key=hiddify_access_info.hiddify_api_key,
                    admin_proxy_path=hiddify_access_info.admin_proxy_path,
                    panel_admin_domain=hiddify_access_info.panel_admin_domain,
                    enable=False,
                )

                if not status:
                    messages.error(request, "خطا در غیرفعال کردن کاربر در هیدیفای")
                    return redirect("/admin-panel/orders/")
                else:
                    messages.success(request, "کاربر در هیدیفای غیرفعال شد")

                order.delete()
                messages.warning(request, "سفارش با موفقیت حذف شد")

            else:
                messages.error(request, "این سفارش را در حال حاضر نمیتوان حذف کرد")

        except Config.DoesNotExist:
            messages.error(request, "کانفیگ پیدا نشد")
            return redirect("/admin-panel/orders/")

        except Order.DoesNotExist:
            messages.error(request, "سفارش پیدا نشد")

        except HiddifyAccessInfo.DoesNotExist:
            messages.error(request, "کانفیگ در هیدیفای پیدا نشد")
            return redirect("/admin-panel/orders/")

        except Exception as e:
            add_admin_log(f"Error in delete order {e}", "admin", request.user)
            messages.error(request, f"خطا در حذف سفارش: {str(e)}")

    return redirect("/admin-panel/orders/")


def ConfirmOrderAdminView(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect("/login-register/")

    if request.method == "POST":
        payment_pk = request.POST.get("payment_pk")
        confirm_payment = request.POST.get("confirm_payment")

        if not payment_pk or not confirm_payment:
            messages.error(request, "خطا در اطلاعات وارد شده")
            return redirect("/admin-panel/orders/")

        try:
            payment = Payment.objects.get(pk=payment_pk)
            if confirm_payment == "true":
                payment.validated = True
                payment.order.status = True
                payment.save()
                payment.order.save()
                messages.success(request, "سفارش تایید شد")

            elif confirm_payment == "false":

                # disable the user in hiddify using tools.on_off_user
                hiddify_access_info = HiddifyAccessInfo.objects.latest("created_date")
                hiddify_api_key = hiddify_access_info.hiddify_api_key
                panel_admin_domain = hiddify_access_info.panel_admin_domain
                admin_proxy_path = hiddify_access_info.admin_proxy_path
                status = hiddify_actions.on_off_user(
                    uuid=payment.config.uuid,
                    hiddify_api_key=hiddify_api_key,
                    admin_proxy_path=admin_proxy_path,
                    panel_admin_domain=panel_admin_domain,
                    enable=False,
                )
                if not status:
                    messages.error(request, "خطا در غیرفعال کردن کاربر در هیدیفای")
                    return redirect("/admin-panel/orders/")

                payment.delete()
                messages.warning(request, "پرداخت حذف شد")

        except Order.DoesNotExist:
            messages.error(request, "سفارش پیدا نشد")

        except Exception as e:
            add_admin_log(f"Error in confirm order {e}", "admin", request.user)
            messages.error(request, f"خطا در تایید سفارش: {str(e)}")

    return redirect("/admin-panel/orders/")


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
        response["Content-Type"] = content_type or "application/octet-stream"

        # set the content disposition to attachment to prompt download
        # response['Content-Disposition'] = f'attachment; filename="{file_path.split("/")[-1]}"'
        response["X-Accel-Redirect"] = f"/protected_media/{file_path}"

        return response
    else:
        # 5. if the user does not have permission, return a forbidden response
        return HttpResponseForbidden("شما اجازه دسترسی به این فایل را ندارید.")
