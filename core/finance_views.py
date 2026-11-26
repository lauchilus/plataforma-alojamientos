from datetime import date,timedelta
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.http import Http404
from django.shortcuts import redirect,render
from django.views.decorators.http import require_http_methods
from .views import owner_required
from .models import Accommodation,Reservation
from .finance_models import Payment,Expense,ExpenseAllocation,InventoryItem,InventoryMovement
from .finance_forms import PaymentForm,ExpenseForm,ExpenseAllocationForm,InventoryItemForm,InventoryMovementForm,BusinessSettingsForm
from .services.inventory import record_movement

@owner_required
@require_http_methods(["GET","POST"])
def business_settings(request):
    form=BusinessSettingsForm(request.POST or None,instance=request.business_account)
    if request.method=="POST" and form.is_valid():
        form.save()
        messages.success(request,"Configuración financiera actualizada.")
        return redirect("business_settings")
    return render(request,"core/business_settings.html",{"form":form})

@owner_required
def finance_home(request):
    account=request.business_account
    return render(request,"core/finance_home.html",{"payments":Payment.objects.filter(account=account).select_related("reservation","reservation__guest")[:12],"expenses":Expense.objects.filter(account=account).select_related("accommodation")[:12],"payment_count":Payment.objects.filter(account=account).count(),"expense_count":Expense.objects.filter(account=account).count(),"base_currency":account.base_currency})
@owner_required
@require_http_methods(["GET","POST"])
def payment_create(request):
    form=PaymentForm(request.POST or None,account=request.business_account)
    if request.method=="POST" and form.is_valid():
        try: form.save()
        except ValidationError as exc: form.add_error(None,exc)
        else: messages.success(request,"Pago registrado y convertido con la cotización disponible."); return redirect("finance_home")
    return render(request,"core/payment_form.html",{"form":form})
@owner_required
@require_http_methods(["GET","POST"])
def expense_create(request):
    form=ExpenseForm(request.POST or None,account=request.business_account)
    if request.method=="POST" and form.is_valid():
        try: form.save()
        except ValidationError as exc: form.add_error(None,exc)
        else: messages.success(request,"Gasto registrado."); return redirect("finance_home")
    return render(request,"core/expense_form.html",{"form":form})
@owner_required
@require_http_methods(["GET","POST"])
def allocation_create(request):
    form=ExpenseAllocationForm(request.POST or None,account=request.business_account)
    if request.method=="POST" and form.is_valid():
        obj=form.save(commit=False); obj.full_clean(); obj.save(); messages.success(request,"Gasto general distribuido."); return redirect("finance_home")
    return render(request,"core/allocation_form.html",{"form":form})
@owner_required
def inventory_home(request):
    account=request.business_account
    return render(request,"core/inventory_home.html",{"items":InventoryItem.objects.filter(account=account,is_active=True).select_related("accommodation"),"movements":InventoryMovement.objects.filter(account=account).select_related("item","reservation")[:15]})
@owner_required
@require_http_methods(["GET","POST"])
def inventory_item_create(request):
    form=InventoryItemForm(request.POST or None,account=request.business_account)
    if request.method=="POST" and form.is_valid():
        form.save(); messages.success(request,"Elemento agregado al inventario."); return redirect("inventory_home")
    return render(request,"core/inventory_item_form.html",{"form":form,"title":"Nuevo elemento"})
@owner_required
@require_http_methods(["GET","POST"])
def inventory_item_edit(request,pk):
    from .finance_forms import InventoryItemForm
    item=get_object_or_404(InventoryItem,pk=pk,account=request.business_account)
    form=InventoryItemForm(request.POST or None,instance=item,account=request.business_account)
    if request.method=="POST" and form.is_valid():
        form.save()
        messages.success(request,"Elemento actualizado.")
        return redirect("inventory_home")
    return render(request,"core/inventory_item_form.html",{"form":form,"title":"Editar elemento"})

@owner_required
@require_http_methods(["GET","POST"])
def inventory_movement_create(request):
    from .models import Reservation
    form=InventoryMovementForm(request.POST or None,account=request.business_account)
    if request.method=="POST" and form.is_valid():
        try:
            record_movement(item=form.cleaned_data["item"],movement_type=form.cleaned_data["movement_type"],quantity=form.cleaned_data["quantity"],account=request.business_account,reservation=form.cleaned_data["reservation"],source_state=form.cleaned_data["source_state"],notes=form.cleaned_data["notes"])
        except ValidationError as exc: form.add_error(None,exc)
        else: messages.success(request,"Movimiento de inventario registrado."); return redirect("inventory_home")
    return render(request,"core/inventory_movement_form.html",{"form":form})
@owner_required
def reports(request):
    account=request.business_account
    end=date.today(); start=end.replace(day=1)
    try:
        if request.GET.get("desde"): start=date.fromisoformat(request.GET["desde"])
        if request.GET.get("hasta"): end=date.fromisoformat(request.GET["hasta"])
    except ValueError: pass
    payments=Payment.objects.filter(account=account,paid_on__gte=start,paid_on__lte=end)
    expenses=Expense.objects.filter(account=account,spent_on__gte=start,spent_on__lte=end)
    collected=payments.aggregate(v=Sum("base_amount"))["v"] or Decimal("0")
    spent=expenses.aggregate(v=Sum("base_amount"))["v"] or Decimal("0")
    units=[]
    for unit in Accommodation.objects.filter(account=account,is_active=True):
        unit_pay=payments.filter(reservation__accommodation=unit).aggregate(v=Sum("base_amount"))["v"] or Decimal("0")
        direct=expenses.filter(accommodation=unit).aggregate(v=Sum("base_amount"))["v"] or Decimal("0")
        allocated=ExpenseAllocation.objects.filter(expense__in=expenses,accommodation=unit).aggregate(v=Sum("amount_base"))["v"] or Decimal("0")
        units.append({"name":unit.name,"complex":unit.complex.name,"collected":unit_pay,"expenses":direct+allocated,"net":unit_pay-direct-allocated})
    reserved=Reservation.objects.filter(account=account,status__in=["PENDING","CONFIRMED","CHECKED_IN","COMPLETED"],check_in__lte=end,check_out__gt=start)
    occupied_days=sum(max(0,(min(r.check_out,end+timedelta(days=1))-max(r.check_in,start)).days) for r in reserved)
    available_days=max(1,Accommodation.objects.filter(account=account,is_active=True).count()*((end-start).days+1))
    unallocated_general=Decimal("0.00")
    for expense in expenses.filter(accommodation__isnull=True).prefetch_related("allocations"):
        assigned=sum((row.amount_base for row in expense.allocations.all()),Decimal("0.00"))
        unallocated_general+=max(Decimal("0.00"),expense.base_amount-assigned)
    return render(request,"core/reports.html",{"start":start,"end":end,"collected":collected,"expenses":spent,"net":collected-spent,"base_currency":account.base_currency,"units":units,"reservation_count":reserved.count(),"occupancy":min(100,round(100*occupied_days/available_days)),"unallocated_general":unallocated_general})
