from django.urls import path
from . import finance_views as v
urlpatterns=[
 path("finanzas/",v.finance_home,name="finance_home"),
 path("finanzas/pagos/nuevo/",v.payment_create,name="payment_create"),
 path("finanzas/gastos/nuevo/",v.expense_create,name="expense_create"),
 path("finanzas/distribuir-gasto/",v.allocation_create,name="allocation_create"),
 path("inventario/",v.inventory_home,name="inventory_home"),
 path("inventario/elementos/nuevo/",v.inventory_item_create,name="inventory_item_create"),
 path("inventario/movimientos/nuevo/",v.inventory_movement_create,name="inventory_movement_create"),
 path("informes/",v.reports,name="reports"),
]
