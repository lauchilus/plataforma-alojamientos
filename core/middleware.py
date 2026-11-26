from django.shortcuts import redirect
from django.urls import reverse

class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user and user.is_authenticated and not user.is_staff:
            account = getattr(user, "business_account", None)
            if account and account.must_change_password:
                allowed = {reverse("password_change"), reverse("login"), reverse("logout")}
                if request.path not in allowed and not request.path.startswith(("/admin/", "/static/")):
                    return redirect(reverse("password_change"))
        return self.get_response(request)
