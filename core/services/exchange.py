import json
from datetime import timedelta
from decimal import Decimal
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from django.core.exceptions import ValidationError
from django.core.cache import cache

API="https://api.bcra.gob.ar"
def _get_json(url):
    request=Request(url,headers={"Accept":"application/json","User-Agent":"PlataformaAlojamientos/1.0"})
    try:
        with urlopen(request,timeout=8) as response: return json.loads(response.read().decode("utf-8"))
    except (URLError,HTTPError,TimeoutError,ValueError) as exc:
        raise ValidationError("No se pudo consultar la cotización del BCRA. Reintentá en unos minutos.") from exc

def _series_id(source):
    key="bcra-series-"+source
    cached=cache.get(key)
    if cached: return cached
    data=_get_json(API+"/estadisticas/v3.0/monetarias").get("results",[])
    match=None
    for row in data:
        desc=(row.get("descripcion") or "").lower()
        if source=="BCRA_MINORISTA_VENDEDOR" and "tipo de cambio minorista" in desc and "promedio vendedor" in desc: match=row; break
        if source=="BCRA_MAYORISTA" and "tipo de cambio mayorista" in desc and "referencia" in desc: match=row; break
    if not match: raise ValidationError("El BCRA no devolvió la serie cambiaria configurada.")
    cache.set(key,match["idVariable"],86400)
    return match["idVariable"]

def quote_to_ars(currency, on_date, source):
    if currency=="ARS": return Decimal("1"),on_date,"ARS (sin conversión)"
    if currency=="USD":
        series=_series_id(source)
        start=(on_date-timedelta(days=10)).isoformat()
        url=API+f"/estadisticas/v3.0/monetarias/{series}?"+urlencode({"desde":start,"hasta":on_date.isoformat(),"limit":1000})
        rows=_get_json(url).get("results",[])
        rows=[x for x in rows if x.get("valor") is not None and x.get("fecha","")<=on_date.isoformat()]
        if rows:
            row=max(rows,key=lambda x:x["fecha"])
            return Decimal(str(row["valor"])),__import__("datetime").date.fromisoformat(row["fecha"]),source
    for offset in range(0,11):
        day=on_date-timedelta(days=offset)
        url=API+"/estadisticascambiarias/v1.0/Cotizaciones?"+urlencode({"fecha":day.isoformat()})
        result=_get_json(url).get("results",{})
        for row in result.get("detalle",[]):
            if row.get("codigoMoneda")==currency and row.get("tipoCotizacion"):
                return Decimal(str(row["tipoCotizacion"])),day,"BCRA cotizaciones por fecha"
    raise ValidationError(f"No hay cotización oficial disponible para {currency} en la fecha seleccionada.")

def convert_currency(amount, currency_from, currency_to, on_date, source):
    if currency_from==currency_to: return Decimal(amount),Decimal("1"),on_date,"Sin conversión"
    rate_from,date_from,source_from=quote_to_ars(currency_from,on_date,source)
    rate_to,date_to,source_to=quote_to_ars(currency_to,on_date,source)
    if rate_to==0: raise ValidationError("La cotización de destino no es válida.")
    converted=(Decimal(amount)*rate_from/rate_to).quantize(Decimal("0.01"))
    return converted,(rate_from/rate_to).quantize(Decimal("0.00000001")),min(date_from,date_to),source_from if source_from==source_to else f"{source_from} / {source_to}"
