from datetime import date

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.generic import TemplateView

from accounts.models import CustomUser, Profile
from adminlogs.action import add_admin_log
from adminlogs.models import AdminLog, Message
from client_actions.models import Config, Order
from plans.models import Bank_Information, Plan
from task_manager.hiddify_actions import generate_qr_code, on_off_user
from task_manager.models import HiddifyAccessInfo, HiddifyUser
from telegram_bot.models import Telegram_Bot_Info

# ------------------------------------ User Panel Views ------------------------------------#


def LoginRegisterView(request):

    if request.method == "POST":
        form_id = request.POST.get("form_id")

        # ------------------- Login Form -------------------
        if form_id == "login-form":
            email = request.POST.get("email")
            password = request.POST.get("password")

            # Check if email and password are provided
            if not email or not password:
                messages.error(request, "لطفاً ایمیل و رمز عبور را وارد کنید.")
                return redirect("/login-register/")

            email = email.strip().lower()

            # Authenticate user with email and password
            user = authenticate(request, email=email, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, "شما با موفقیت وارد شدید.")
                return redirect("/home/")  # Home page URL

        # ------------------- Registration Form -------------------
        elif form_id == "register-form":
            first_name = request.POST.get("name")
            last_name = request.POST.get("family")
            email = request.POST.get("email")
            password = request.POST.get("password")
            confirm_password = request.POST.get("confirm_password")
            invite_code = request.POST.get("invite_code")

            # بررسی تطابق رمزهای عبور
            if password != confirm_password:
                messages.error(request, "رمزهای عبور یکسان نیستند.")
                return redirect("/login-register/")

            # Validate email format
            try:
                validate_email(email)
                email = email.strip().lower()
            except ValidationError:
                messages.error(request, "فرمت ایمیل وارد شده صحیح نیست.")
                return redirect("/login-register/")

            # check if the email is already registered
            if CustomUser.objects.filter(email=email).exists():
                messages.error(request, "این ایمیل قبلاً ثبت شده است.")
                return redirect("/login-register/")

            # create a new user
            try:
                user = CustomUser.objects.create_user(
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                )
            except Exception as e:
                messages.error(request, f"خطا در ساخت کاربر: {str(e)}")
                return redirect("/login-register/")

            # check if the invite code is provided
            invited_by_user = None
            if invite_code:
                try:
                    # Find the inviter's profile using the invite code
                    inviter_profile = Profile.objects.get(invite_code=invite_code)
                    invited_by_user = inviter_profile.user
                except Profile.DoesNotExist:
                    user.delete()
                    messages.error(request, "کد دعوت وارد شده معتبر نیست.")
                    return redirect("/login-register/")

            # create a profile for the new user
            try:
                profile = Profile(user=user, invited_by=invited_by_user)
                profile.save()
                messages.success(request, "حساب کاربری شما با موفقیت ایجاد شد.")
            except Exception as e:
                user.delete()
                messages.error(request, f"خطا در ساخت پروفایل: {str(e)}")
                return redirect("/login-register/")

            # Login the user after successful registration
            login(request, user)
            # Redirect to the home page
            return redirect("/home/")

    # If the request method is GET or no form matches, show the login/register page
    return render(request, "user/login_register.html")


def LogoutView(request):
    
    logout(request)
    return redirect("/login-register/")


def OrdersView(request):

    if request.method == "GET":

        orders = request.user.orders.all()
        order_uuids = request.user.config.values_list("uuid", flat=True)
        hiddify_entries = HiddifyUser.objects.filter(uuid__in=order_uuids).values(
            "uuid", "name"
        )
        uuid_to_name = {entry["uuid"]: entry["name"] for entry in hiddify_entries}

        # Attach the Hiddify name to each order (add a custom attribute 'name')
        for order in orders:
            # Get name or None if not found
            order.name = uuid_to_name.get(order.config.uuid, None)

        invite_code = request.user.profile.invite_code

        return render(
            request, "user/orders.html", {"orders": orders, "invite_code": invite_code}
        )


def AddinviteCodeView(request):

    if request.method == "POST":
        invite_code = request.POST.get("invite_code")
        if not invite_code:
            messages.error(request, "لطفا کد دعوت را وارد کنید")
            return redirect("/home/")
        try:
            invite_code = int(invite_code)
        except ValueError:
            messages.error(request, "کد دعوت معتبر نیست")
            return redirect("/home/")

        # Check if the invite code exists
        try:
            profile = Profile.objects.get(invite_code=invite_code)
            if profile.user == request.user:
                messages.error(request, "شما نمیتوانید از کد دعوت خود استفاده کنید")
                return redirect("/home/")
            else:
                # Add the invite code to the user's profile
                request.user.profile.invited_by = profile.user
                request.user.profile.save()
                messages.success(request, "کد دعوت با موفقیت اضافه شد")
                return redirect("/home/")
        except Profile.DoesNotExist:
            messages.error(request, "کد دعوت معتبر نیست")
            return redirect("/home/")

    return redirect("/home/")


class HomeView(TemplateView):
    template_name = "user/home_active.html"

    def get(self, request, *args, **kwargs):

        # Fetch the user's plans and configurations also filter by status and order by days and price
        plans = Plan.objects.filter(status=True).order_by("duration", "price")
        user_configs = Config.objects.filter(user=request.user)

        # Get all admin messages
        admin_messages = self.get_admin_messages()

        # get telegram bot info
        telegram_bot_info = self.get_telegram_bot_info(request)

        # get bank information
        bank_information = self.get_bank_information(request)
        bank_information_show = False

        # check if the user has telegram_account or not
        telegram_account = False
        if request.user.telegram_account.exists():
            telegram_account = True
        else:
            telegram_account = False

        if not user_configs:
            return redirect("/buyconfig/")

        data_return = []
        for config in user_configs:
            hiddify_user = self.get_hiddify_user(config.uuid)
            if not hiddify_user:
                continue

            last_order = self.get_last_order(config)
            package_days = self.calculate_package_days(hiddify_user)
            subscriptionlink, qrcode = self.generate_subscription_data(
                config, hiddify_user
            )

            # should we show bank information?
            if last_order and isinstance(last_order, dict) and "status" in last_order:
                bank_information_show = last_order["status"] not in [
                    "payed",
                    "payed under checking",
                ]

            data_return.append(
                {
                    "name": hiddify_user.name,
                    "current_usage": round(float(hiddify_user.current_usage_GB), 2),
                    "is_active": hiddify_user.is_active,
                    "last_online": hiddify_user.last_online,
                    "left_trafic": round(
                        float(hiddify_user.usage_limit_GB)
                        - float(hiddify_user.current_usage_GB),
                        2,
                    ),
                    "package_days": package_days,
                    "uuid": config.uuid,
                    "qrcode": qrcode,
                    "subscriptionlink": subscriptionlink,
                    "last_order": last_order,
                    "comment": hiddify_user.comment,
                }
            )

        return_data = {
            "data": {"config": data_return},
            "bank_info": bank_information if bank_information_show else None,
            "invite_code": request.user.profile.invite_code,
            "telegram_id": telegram_account,
            "telegram_bot_info": telegram_bot_info,
            "user_uuid": request.user.profile.uuid,
            "plans": plans,
            "message_to_users": admin_messages,
        }
        return render(request, self.template_name, return_data)

    def get_hiddify_user(self, uuid):
        """Fetches the Hiddify user by UUID, with exception handling."""
        try:
            return HiddifyUser.objects.get(uuid=uuid)
        except HiddifyUser.DoesNotExist:
            messages.error(
                self.request, f"Error retrieving Hiddify user for config {uuid}"
            )
            return None
        except Exception as e:
            messages.error(
                self.request,
                f"Error retrieving Hiddify user for config {uuid}: {str(e)}",
            )
            return None

    def get_admin_messages(self):
        """Fetches the admin messages for the user."""
        return Message.objects.filter(status=True).order_by("-id")

    def get_last_order(self, config):
        """Fetches and processes the last order for a given configuration."""
        order = config.order_configs.filter(user=self.request.user).last()
        if order:
            payment_status = self.get_payment_status(order)
            return {
                "plan": order.plan,
                "pk_order": order.pk,
                "status": payment_status,
                "pending": order.pending,
            }
        return None

    def get_payment_status(self, order):
        """Determine the status of a payment related to an order."""
        # payment = order.order_payment.exists():
        payment = getattr(order, "order_payment", None)
        if payment and payment.validated:
            return "payed"
        elif payment and not payment.validated:
            return "payed under checking"
        elif not order.status and not order.pending:

            # how many dayes passed from the creation date
            remaining_days = (
                settings.WAITING_FOR_PAYMENT_TIMEOUT_DAYS
                - (date.today() - order.created_date.date()).days
            )

            return remaining_days
        elif not order.status and order.pending:
            return "pending"
        else:
            return "not paid"

    def calculate_package_days(self, hiddify_user):
        """Calculates the remaining days for a user's package."""
        if hiddify_user.start_date:
            return (
                hiddify_user.package_days
                - (date.today() - hiddify_user.start_date).days
            )
        return None

    def generate_subscription_data(self, config, hiddify_user):
        """Generates the subscription link and QR code for a user."""

        try:
            hiddify_access_info = HiddifyAccessInfo.objects.latest("created_date")
        except HiddifyAccessInfo.DoesNotExist:
            return None

        subscriptionlink = f"{hiddify_access_info.subscription_domain}/{hiddify_access_info.sub_proxy_path}/{config.uuid}/#{hiddify_user.name}"
        qrcode = generate_qr_code(subscriptionlink)
        return subscriptionlink, qrcode

    def get_telegram_bot_info(self, request):
        try:
            return Telegram_Bot_Info.objects.latest("created_date").bot_name
        except Telegram_Bot_Info.DoesNotExist:
            return None
        except Exception as e:
            add_admin_log(
                action=f"Error in fetching Telegram bot info: {str(e)}",
                category="admin",
                user=request.user,
            )
            return None

    def get_bank_information(self, request):
        try:
            # get the latest bank information with true status
            bank_info = Bank_Information.objects.filter(status=True).latest(
                "updated_date"
            )
            return {
                "bank_name": bank_info.bank_name,
                "card_number": bank_info.card_number,
                "account_name": bank_info.account_name,
            }
        except Bank_Information.DoesNotExist:
            return None
        except Exception as e:
            add_admin_log(
                action=f"Error while getting bank information: {str(e)}",
                category="admin",
                user=request.user,
            )
            return None


def ByConfig(request):
    """
    Handles the view for a user to buy a configuration.
    - Authenticates the user.
    - Retrieves available plans, user's invite code, and existing configurations.
    - Displays the 'buy_config.html' template with the necessary context.
    """
    
    if request.method == "GET":
        try:
            # Fetch all necessary data in one block
            plans = Plan.objects.filter(status=True).order_by("duration", "price")
            
            # Use select_related to avoid extra queries for the profile
            invite_code = request.user.profile.invite_code
            
            # Fetch user's configs and related HiddifyUser names efficiently
            user_configs = Config.objects.filter(user=request.user)
            
            # Get HiddifyUser info in a single, optimized query
            hiddify_user_configs = {
                str(hu.uuid): hu.name 
                for hu in HiddifyUser.objects.filter(uuid__in=user_configs.values_list('uuid', flat=True))
            }

        except Plan.DoesNotExist:
            messages.error(request, "No available plans found.")
            return redirect("home") # Use URL names
        except AttributeError:
            # This handles cases where user.profile might not exist
            messages.error(request, "User profile not found. Error Code: 13")
            # Log this specific issue for admin review
            # add_admin_log(...) 
            return redirect("home")
        except Exception as e:
            # General catch-all for other unexpected errors
            # add_admin_log(
            #     action=f"Error in buy_config_view: {str(e)}",
            #     category="critical",
            #     user=request.user,
            # )
            messages.error(request, "An unexpected error occurred. Please try again. Error Code: 15")
            return redirect("home")

        context = {
            "plans": plans,
            "invite_code": invite_code,
            "configs": hiddify_user_configs,
        }
        return render(request, "user/buy_config.html", context)

    # You might want to handle POST requests here if the form submission is on the same URL
    # For now, redirecting if not a GET request
    return redirect("home")


def HomeDeactiveView(request):
    """
    Renders the home deactive page for users whose profiles are inactive.
    """
    return render(request, "user/home_deactive.html")


# ------------------------------------ Admin Panel Views ------------------------------------#

def AdminPanelView(request):

    if request.method == "GET":

        hiddifyUsers_count = HiddifyUser.objects.all().count()
        plan_count = Plan.objects.all().count()
        not_payed_orders_count = Order.objects.filter(
            status=False, pending=False
        ).count()
        pending_orders_count = Order.objects.filter(pending=True).count()
        log_count = AdminLog.objects.all().count()
        admin_messages_count = Message.objects.filter(status=True).count()

        # Get tha first day of the month
        last_month = timezone.now().replace(day=1)

        # Query all orders that are not older than 5 days ago, still pending, and not paid
        last_month_orders = Order.objects.filter(
            created_date__gte=last_month,  # Orders created in this month
            status=True,  # Order not paid
        )

        alltime_orders = Order.objects.filter(status=True)
        total_sell_last_month = last_month_orders.aggregate(total=Sum("plan__price"))
        total_sell = alltime_orders.aggregate(total=Sum("plan__price"))

        data_return = {
            "hiddifyUsers_count": hiddifyUsers_count,
            "plan_count": plan_count,
            "not_payed_orders_count": not_payed_orders_count,
            "pending_orders_count": pending_orders_count,
            "log_count": log_count,
            "total_sell_last_month": (
                0
                if total_sell_last_month["total"] == None
                else total_sell_last_month["total"]
            ),
            "total_sell": 0 if total_sell["total"] == None else total_sell["total"],
            "admin_messages_count": admin_messages_count,
        }

        return render(request, "admin/admin_home.html", data_return)

    return redirect("/admin-panel/")


def AdminUsersView(request):

    if request.method == "GET":
        profiles = Profile.objects.all()

        return render(request, "admin/admin_users.html", {"profiles": profiles})

    elif request.method == "POST":

        # Check if the request is a PUT or DELETE
        action = request.POST.get("action")

        if action == "PUT":

            user_uuid = request.POST.get("user_uuid")
            if not user_uuid:
                messages.error(request, "لطفا یوزر انتخاب کنید")
                return redirect("/admin-panel/users")

            # Toggle the user's active status
            try:
                profile = Profile.objects.get(uuid=user_uuid)

                if profile.is_active:
                    profile.is_active = False
                    messages.success(request, "با موفقیت غیر فعال شد")
                else:
                    profile.is_active = True
                    messages.success(request, "با موفقیت فعال شد")
                profile.save()

            except Profile.DoesNotExist:
                messages.error(request, "کاربر یافت نشد")
                return redirect("/admin-panel/users")

        elif action == "DELETE":

            user_pk = request.POST.get("user_pk")

            if not user_pk:
                messages.error(request, "لطفا یوزر انتخاب کنید")
                return redirect("/admin-panel/users")

            # Delete the user
            try:
                User = CustomUser.objects.get(pk=user_pk)
                User.delete()
                messages.success(request, "با موفقیت حذف شد")
            except Profile.DoesNotExist:
                messages.error(request, "کاربر یافت نشد")
                return redirect("/admin-panel/users")

    return redirect("/admin-panel/users")


def AdminConfigsView(request):
    if request.method == "GET":
        filter = request.GET.get("filter")
        
        # ۱. کوئری بر اساس فیلتر مثل قبل انجام می‌شود
        if filter == "active":
            configs_list = HiddifyUser.objects.filter(enable=True, is_active=True).order_by('-id')
        elif filter == "inactive":
            configs_list = HiddifyUser.objects.filter(enable=False).order_by('-id')
        elif filter == "package_ended":
            configs_list = HiddifyUser.objects.filter(enable=True, is_active=False).order_by('-id')
        else:
            configs_list = HiddifyUser.objects.all().order_by('-id')
        
        # ۲. منطق صفحه‌بندی اضافه می‌شود
        paginator = Paginator(configs_list, 30)  # هر صفحه ۳۰ آیتم خواهد داشت
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        return render(
            request, 
            "admin/admin_configs.html", 
            {"page_obj": page_obj, "filter": filter} # به جای configs از page_obj استفاده می‌کنیم
        )

    elif request.method == "POST":
        action = request.POST.get("action")
        if action == "on_off":
            hidify_user_uuid = request.POST.get("hidify_user_uuid")
            if not hidify_user_uuid:
                messages.error(request, "لطفا یوزر انتخاب کنید")
                return redirect("/admin-panel/configs/")

            try:
                hiddify_access_info = HiddifyAccessInfo.objects.latest("created_date")
            except HiddifyAccessInfo.DoesNotExist:
                messages.warning(request, "اطلاعات دسترسی Hiddify یافت نشد.")
                return redirect("/admin-panel/configs/")

            hiddify_api_key = hiddify_access_info.hiddify_api_key
            panel_admin_domain = hiddify_access_info.panel_admin_domain
            admin_proxy_path = hiddify_access_info.admin_proxy_path

            try:
                hiddify_user = HiddifyUser.objects.get(uuid=hidify_user_uuid)
                new_enable_status = not hiddify_user.enable
                status = on_off_user(
                    hiddify_user.uuid,
                    enable=new_enable_status,
                    hiddify_api_key=hiddify_api_key,
                    admin_proxy_path=admin_proxy_path,
                    panel_admin_domain=panel_admin_domain,
                )
                if status:
                    hiddify_user.enable = new_enable_status
                    hiddify_user.save()
                    if new_enable_status:
                        messages.success(request, "با موفقیت فعال شد")
                    else:
                        messages.warning(request, "با موفقیت غیر فعال شد")
                else:
                    messages.error(request, "خطا در تغییر وضعیت کاربر")

            except HiddifyUser.DoesNotExist:
                messages.error(request, "کاربر یافت نشد")
        
        # برای حفظ صفحه و فیلتر فعلی بعد از POST
        current_filter = request.POST.get("filter", "")
        current_page = request.POST.get("page", "1")
        redirect_url = f"/admin-panel/configs/?page={current_page}"
        if current_filter:
            redirect_url += f"&filter={current_filter}"
            
        return redirect(redirect_url)


def AdminOrdersView(request):
    if request.method == "GET":
        # ۱. تمام سفارش‌ها را با pre-fetch کردن کانفیگ مربوطه دریافت می‌کنیم
        # این کار باعث بهینه‌سازی کوئری دیتابیس می‌شود
        orders_list = Order.objects.select_related('config').all().order_by("-id")

        # ۲. منطق صفحه‌بندی را اضافه می‌کنیم
        paginator = Paginator(orders_list, 30)  # هر صفحه ۳۰ سفارش
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        # ۳. فقط برای سفارش‌های موجود در صفحه فعلی، اطلاعات Hiddify را می‌گیریم
        # این کار باعث می‌شود به جای همه UUIDها، فقط UUIDهای صفحه فعلی بررسی شوند
        
        # ابتدا UUID های کانفیگ‌های سفارش‌های صفحه فعلی را استخراج می‌کنیم
        current_page_orders = page_obj.object_list
        order_uuids = [
            order.config.uuid for order in current_page_orders if order.config
        ]

        # سپس نام‌های Hiddify مربوط به این UUIDها را می‌گیریم
        hiddify_entries = HiddifyUser.objects.filter(uuid__in=order_uuids).values(
            "uuid", "name"
        )
        uuid_to_name = {entry["uuid"]: entry["name"] for entry in hiddify_entries}

        # در نهایت، نام Hiddify را به هر سفارش در صفحه فعلی اضافه می‌کنیم
        for order in page_obj:  # می‌توان مستقیم روی page_obj حلقه زد
            order_uuid = getattr(order.config, "uuid", None)
            order.name = uuid_to_name.get(order_uuid, "نامشخص") # یک مقدار پیش‌فرض

        return render(request, "admin/admin_orders.html", {"page_obj": page_obj})


def AdminPlansView(request):

    if request.method == "GET":
        plans = Plan.objects.filter(status=True).order_by("duration", "price")
        return render(request, "admin/admin_plans.html", {"plans": plans})

    return render(request, "admin/admin_plans.html")


def AdminLogsView(request):
    
    if request.method == "GET":
        category = request.GET.get("category")
        page = request.GET.get("page", 1)  # شماره صفحه‌ای که از URL می‌گیریم. پیش‌فرض 1

        categories = [cat[0] for cat in AdminLog.ACTION_CATEGORIES]
        if category and category in categories:
            logs = AdminLog.objects.filter(category=category).order_by("-id")
        else:
            logs = AdminLog.objects.all().order_by("-id")

        paginator = Paginator(logs, 10)  # صفحه‌بندی با 10 آیتم در هر صفحه
        try:
            logs_paginated = paginator.page(page)
        except PageNotAnInteger:
            logs_paginated = paginator.page(
                1
            )  # اگر شماره صفحه معتبر نبود، به صفحه اول برمی‌گردد
        except EmptyPage:
            logs_paginated = paginator.page(
                paginator.num_pages
            )  # اگر شماره صفحه خارج از بازه بود، آخرین صفحه را نشان می‌دهد

        total_logs = logs.count()
        return render(
            request,
            "admin/admin_logs.html",
            {
                "logs": logs_paginated,  # فقط لاگ‌های مربوط به صفحه فعلی
                "total_logs": total_logs,
                "categories": categories,
                "selected_category": category,
                "paginator": paginator,  # اضافه کردن شیء paginator برای رندر کردن لینک‌های ناوبری
            },
        )

    return redirect("/admin-panel/logs")


def AdminMessageView(request):

    if request.method == "GET":

        admin_messages = Message.objects.all().order_by("-id")

        return render(
            request, "admin/admin_messages.html", {"admin_messages": admin_messages}
        )

    return redirect("/admin-panel/messages")