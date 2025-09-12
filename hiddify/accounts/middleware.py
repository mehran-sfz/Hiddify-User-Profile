from django.shortcuts import redirect
from django.urls import NoReverseMatch, reverse
from django.utils.deprecation import MiddlewareMixin


class RoleAndStatusCheckMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        
        # This part for unauthenticated users remains the same
        if not request.user.is_authenticated:
            try:
                allowed_unauthenticated_paths = [
                    reverse('login_register'),
                    reverse('login'),
                    reverse('register'),
                    reverse('logout'),
                    reverse('telegram_webhook'),
                    reverse('addinvitecode'),
                    reverse('addconfig'),
                ]
            except NoReverseMatch:
                allowed_unauthenticated_paths = ['/login-register/', '/login/', '/register/', '/logout/', '/telegram-webhook/', '/addconfig/', '/addinvitecode/']

            if request.path not in allowed_unauthenticated_paths:
                return redirect('login_register')
            
            return None
        
        # --- LOGIC FOR AUTHENTICATED USERS ---
        
        # 1. First, check for staff members.
        if request.user.is_staff:
            is_on_custom_admin = request.path.startswith('/admin-panel/')
            is_on_default_admin = request.path.startswith('/admin/')
            is_on_payment_screenshot = request.path.startswith('/payment-screenshot/')
            is_on_logout = request.path == reverse('logout')

            if not (is_on_custom_admin or is_on_default_admin or is_on_payment_screenshot or is_on_logout):
                return redirect('admin-panel')
            
            return None

        # 2. If the user is NOT staff, they are a regular user.
        else:
            try:
                is_profile_active = request.user.profile.is_active
            except AttributeError: 
                is_profile_active = False

            # --- NEW LOGIC FOR ACTIVE USERS ---
            # If an active user tries to access the deactivated page, redirect them to home.
            if is_profile_active:
                try:
                    deactivated_home_path = reverse('home_deactive')
                    if request.path == deactivated_home_path:
                        return redirect('home')
                except NoReverseMatch:
                    # If the URL doesn't exist, we don't need to check for it.
                    pass

            # --- MODIFIED LOGIC FOR INACTIVE USERS ---
            # If the user's profile is not active:
            if not is_profile_active:
                try:
                    # CHANGED: Added 'addconfig' and 'addinvitecode' to the allowed list for inactive users.
                    allowed_for_deactivated = [
                        reverse('logout'), 
                        reverse('home_deactive'),
                        reverse('addconfig'),
                        reverse('addinvitecode')
                    ]
                except NoReverseMatch:
                    allowed_for_deactivated = ['/logout/', '/home-deactive/', '/addconfig/', '/addinvitecode/']
                
                if request.path not in allowed_for_deactivated:
                    return redirect('home_deactive')
                
                return None

            # Prevent regular users from accessing any admin panels
            if request.path.startswith('/admin-panel/') or request.path.startswith('/admin/'):
                return redirect('home')

        # If no other conditions were met, allow the request to proceed.
        return None