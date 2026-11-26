from datetime import timedelta
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db.models import Q
from core.models import PriceRule

def quote_reservation(accommodation, check_in, check_out, guest_count):
    nights=(check_out-check_in).days
    if nights <= 0:
        raise ValidationError("La fecha de salida debe ser posterior a la de ingreso.")
    rows=[]
    day=check_in
    while day < check_out:
        base=PriceRule.objects.filter(account=accommodation.account,accommodation=accommodation,is_active=True).filter(Q(valid_from__isnull=True)|Q(valid_from__lte=day)).filter(Q(valid_until__isnull=True)|Q(valid_until__gte=day))
        exact=base.filter(guest_count=guest_count).order_by("-valid_from")
        general=base.filter(guest_count__isnull=True).order_by("-valid_from")
        rule=exact.first() or general.first()
        if rule:
            rows.append((rule.nightly_rate,rule.currency,rule.minimum_nights))
        elif accommodation.base_nightly_rate and accommodation.base_nightly_rate > 0:
            rows.append((accommodation.base_nightly_rate,accommodation.base_currency,1))
        else:
            raise ValidationError("No hay una tarifa configurada para todas las noches. Cargá una tarifa base o una regla de precios.")
        day+=timedelta(days=1)
    currencies={row[1] for row in rows}
    if len(currencies)>1:
        raise ValidationError("Las tarifas de una misma estadía deben usar la misma moneda.")
    minimum=max(row[2] for row in rows)
    if nights<minimum:
        raise ValidationError(f"La estadía requiere al menos {minimum} noches.")
    return sum((row[0] for row in rows),Decimal("0.00")), rows[0][1], nights
