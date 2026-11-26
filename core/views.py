import calendar
from datetime import date
from functools import wraps
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from .forms import AccommodationForm, ComplexForm, CreateOwnerForm, OwnerLoginForm, OwnerPasswordChangeForm, PriceRuleForm, ReservationForm
from .models import Accommodation, BusinessAccount, Complex, PriceRule, Reservation

def owner_required(view):
    @wraps(view)
    @login_required
    def wrapped(request,*args,**kwargs):
        account=getattr(request.user,"business_account",None)
        if not account or not account.is_active: raise Http404
        request.business_account=account
        return view(request,*args,**kwargs)
    return wrapped

class OwnerLoginView(LoginView):
    template_name="core/login.html"; authentication_form=OwnerLoginForm; redirect_authenticated_user=True
    def form_valid(self,form):
        user=form.get_user()
        if not user.is_staff and not hasattr(user,"business_account"):
            form.add_error(None,"La cuenta no está habilitada para ingresar."); return self.form_invalid(form)
        if not user.is_staff and not user.business_account.is_active:
            form.add_error(None,"La cuenta está desactivada. Contactá al administrador."); return self.form_invalid(form)
        return super().form_valid(form)
    def get_success_url(self):
        return reverse("platform_owners") if self.request.user.is_staff else reverse("dashboard")

def owner_login(request): return OwnerLoginView.as_view()(request)
@login_required
def owner_logout(request): logout(request); return redirect("login")
@login_required
@require_http_methods(["GET","POST"])
def password_change(request):
    account=getattr(request.user,"business_account",None)
    if not account: return redirect("dashboard")
    form=OwnerPasswordChangeForm(request.user,request.POST or None)
    if request.method=="POST" and form.is_valid():
        user=form.save(); account.must_change_password=False; account.save(update_fields=["must_change_password"]); login(request,user)
        messages.success(request,"Contraseña actualizada."); return redirect("dashboard")
    return render(request,"core/password_change.html",{"form":form})
@owner_required
def dashboard(request):
    account=request.business_account
    return render(request,"core/dashboard.html",{"account":account,"complex_count":Complex.objects.filter(account=account).count(),"accommodation_count":Accommodation.objects.filter(account=account,is_active=True).count(),"recent_complexes":Complex.objects.filter(account=account)[:5],"today":timezone.localtime().date(),"upcoming":Reservation.objects.filter(account=account,status__in=["PENDING","CONFIRMED"]).select_related("accommodation","guest").order_by("check_in")[:5]})
@owner_required
def complex_list(request):
    data=Complex.objects.filter(account=request.business_account).prefetch_related("accommodations")
    return render(request,"core/complex_list.html",{"complexes":data})
@owner_required
@require_http_methods(["GET","POST"])
def complex_create(request):
    form=ComplexForm(request.POST or None)
    if request.method=="POST" and form.is_valid():
        obj=form.save(commit=False); obj.account=request.business_account; obj.save(); messages.success(request,"Complejo creado."); return redirect("complex_list")
    return render(request,"core/complex_form.html",{"form":form,"title":"Nuevo complejo"})
@owner_required
@require_http_methods(["GET","POST"])
def complex_edit(request,pk):
    obj=get_object_or_404(Complex,pk=pk,account=request.business_account); form=ComplexForm(request.POST or None,instance=obj)
    if request.method=="POST" and form.is_valid():
        form.save(); messages.success(request,"Complejo actualizado."); return redirect("complex_list")
    return render(request,"core/complex_form.html",{"form":form,"title":"Editar complejo"})
@owner_required
def accommodation_list(request):
    data=Accommodation.objects.filter(account=request.business_account).select_related("complex")
    return render(request,"core/accommodation_list.html",{"accommodations":data})
@owner_required
@require_http_methods(["GET","POST"])
def accommodation_create(request):
    form=AccommodationForm(request.POST or None,account=request.business_account)
    if request.method=="POST" and form.is_valid():
        form.save(); messages.success(request,"Alojamiento creado."); return redirect("accommodation_list")
    return render(request,"core/accommodation_form.html",{"form":form,"title":"Nuevo alojamiento"})
@owner_required
@require_http_methods(["GET","POST"])
def accommodation_edit(request,pk):
    obj=get_object_or_404(Accommodation,pk=pk,account=request.business_account); form=AccommodationForm(request.POST or None,instance=obj,account=request.business_account)
    if request.method=="POST" and form.is_valid():
        form.save(); messages.success(request,"Alojamiento actualizado."); return redirect("accommodation_list")
    return render(request,"core/accommodation_form.html",{"form":form,"title":"Editar alojamiento"})
@owner_required
def price_rule_list(request):
    rules=PriceRule.objects.filter(account=request.business_account).select_related("accommodation")
    return render(request,"core/price_rule_list.html",{"rules":rules})
@owner_required
@require_http_methods(["GET","POST"])
def price_rule_create(request):
    form=PriceRuleForm(request.POST or None,account=request.business_account)
    if request.method=="POST" and form.is_valid():
        form.save(); messages.success(request,"Tarifa guardada."); return redirect("price_rule_list")
    return render(request,"core/price_rule_form.html",{"form":form})
@owner_required
def reservation_list(request):
    try: year=int(request.GET.get("year",date.today().year)); month=int(request.GET.get("month",date.today().month))
    except ValueError: year,month=date.today().year,date.today().month
    if month<1 or month>12: month=date.today().month
    start=date(year,month,1); end=date(year+1,1,1) if month==12 else date(year,month+1,1)
    rows=Reservation.objects.filter(account=request.business_account,check_in__lt=end,check_out__gt=start).select_related("accommodation","guest").order_by("check_in")
    prev_month=12 if month==1 else month-1; prev_year=year-1 if month==1 else year
    next_month=1 if month==12 else month+1; next_year=year+1 if month==12 else year
    return render(request,"core/reservation_list.html",{"reservations":rows,"month_label":calendar.month_name[month],"year":year,"month":month,"prev_year":prev_year,"prev_month":prev_month,"next_year":next_year,"next_month":next_month})
@owner_required
@require_http_methods(["GET","POST"])
def reservation_create(request):
    form=ReservationForm(request.POST or None,account=request.business_account)
    if request.method=="POST" and form.is_valid():
        try:
            form.save()
        except ValidationError as exc:
            form.add_error(None,exc)
        else:
            messages.success(request,"Reserva cargada.")
            return redirect("reservation_list")
    return render(request,"core/reservation_form.html",{"form":form,"title":"Nueva reserva"})
@owner_required
@require_http_methods(["GET","POST"])
def reservation_edit(request,pk):
    obj=get_object_or_404(Reservation,pk=pk,account=request.business_account)
    form=ReservationForm(request.POST or None,instance=obj,account=request.business_account)
    if request.method=="POST" and form.is_valid():
        try:
            form.save()
        except ValidationError as exc:
            form.add_error(None,exc)
        else:
            messages.success(request,"Reserva actualizada.")
            return redirect("reservation_list")
    return render(request,"core/reservation_form.html",{"form":form,"title":"Editar reserva"})
@login_required
@require_http_methods(["GET","POST"])
def platform_owners(request):
    if not request.user.is_staff: raise Http404
    form=CreateOwnerForm(request.POST or None); credentials=None
    if request.method=="POST" and form.is_valid():
        account,password=form.create_owner(); credentials={"account":account,"password":password}; form=CreateOwnerForm()
    accounts=BusinessAccount.objects.select_related("owner").order_by("business_name")
    return render(request,"core/platform_owners.html",{"form":form,"accounts":accounts,"generated_credentials":credentials})
