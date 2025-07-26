from django.shortcuts import redirect
from django.urls import reverse, NoReverseMatch
from django.utils.deprecation import MiddlewareMixin

class RoleAndStatusCheckMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        
        # This part for unauthenticated users remains the same
        if not request.user.is_authenticated:
            # ... (your existing code for unauthenticated users)
            try:
                allowed_unauthenticated_paths = [
                    reverse('login_register'),
                    reverse('login'),
                    reverse('register'),
                    reverse('logout'),
                    reverse('telegram_webhook'),
                ]
            except NoReverseMatch:
                allowed_unauthenticated_paths = ['/login-register/', '/login/', '/register/', '/logout/', '/telegram-webhook/']

            if request.path not in allowed_unauthenticated_paths:
                return redirect('login_register')
            
            return None
        
        # --- NEW LOGIC ORDER STARTS HERE ---
        
        # 1. First, check if the user is a staff member.
        # This check is now at the top to bypass profile checks for staff.
        if request.user.is_staff:
            is_on_custom_admin = request.path.startswith('/admin-panel/')
            is_on_default_admin = request.path.startswith('/admin/')
            is_on_logout = request.path == reverse('logout')

            # If a staff user is not in one of the allowed admin areas, redirect them.
            if not (is_on_custom_admin or is_on_default_admin or is_on_logout):
                return redirect('admin-panel') # The URL name for your admin panel's home
            
            # If the staff user is in an allowed area, do nothing and proceed.
            return None

        # 2. If the user is NOT staff, then they are a regular user.
        # Now we can safely check for the profile.
        else:
            # Check for active profile for regular users
            try:
                is_profile_active = request.user.profile.is_active
            except AttributeError: 
                # Handles cases where a regular user might not have a profile for some reason
                is_profile_active = False

            if not is_profile_active:
                allowed_for_deactivated = [reverse('logout'), reverse('home_deactive')]
                if request.path not in allowed_for_deactivated:
                    return redirect('home_deactive')
                return None

            # Prevent regular users from accessing any admin panels
            if request.path.startswith('/admin-panel/') or request.path.startswith('/admin/'):
                return redirect('home')

        # If no other conditions were met, allow the request to proceed.
        return None