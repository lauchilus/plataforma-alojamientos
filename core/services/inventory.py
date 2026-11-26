from django.core.exceptions import ValidationError
from django.db import transaction
from core.finance_models import InventoryMovement

@transaction.atomic
def record_movement(item,movement_type,quantity,account,reservation=None,source_state="",notes=""):
    if quantity<=0: raise ValidationError("La cantidad debe ser mayor que cero.")
    if item.account_id!=account.id: raise ValidationError("El elemento no pertenece a esta cuenta.")
    field_map={"clean":"clean_quantity","in_use":"in_use_quantity","used":"used_quantity"}
    if movement_type in {"DELIVER_CLEAN","REPLACEMENT"}:
        if item.clean_quantity<quantity: raise ValidationError("No hay suficiente stock limpio/disponible.")
        item.clean_quantity-=quantity; item.in_use_quantity+=quantity
    elif movement_type=="RETURN_USED":
        if item.in_use_quantity<quantity: raise ValidationError("La cantidad devuelta supera lo entregado.")
        item.in_use_quantity-=quantity; item.used_quantity+=quantity
    elif movement_type=="LAUNDRY_CLEAN":
        if item.used_quantity<quantity: raise ValidationError("No hay suficientes elementos usados para marcar como limpios.")
        item.used_quantity-=quantity; item.clean_quantity+=quantity
    elif movement_type in {"DAMAGE","MISSING"}:
        field=field_map.get(source_state)
        if not field: raise ValidationError("Elegí el estado actual del elemento.")
        current=getattr(item,field)
        if current<quantity: raise ValidationError("La cantidad supera el stock en ese estado.")
        setattr(item,field,current-quantity)
        target="damaged_quantity" if movement_type=="DAMAGE" else "missing_quantity"
        setattr(item,target,getattr(item,target)+quantity)
    elif movement_type=="STOCK_IN":
        item.clean_quantity+=quantity
    else: raise ValidationError("Tipo de movimiento inválido.")
    item.save(update_fields=["clean_quantity","in_use_quantity","used_quantity","damaged_quantity","missing_quantity"])
    movement=InventoryMovement(account=account,item=item,reservation=reservation,movement_type=movement_type,quantity=quantity,source_state=source_state,notes=notes)
    movement.full_clean(); movement.save()
    return movement
