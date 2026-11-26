from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("ingresar/", views.owner_login, name="login"),
    path("salir/", views.owner_logout, name="logout"),
    path("cambiar-contrasena/", views.password_change, name="password_change"),
    path("complejos/", views.complex_list, name="complex_list"),
    path("complejos/nuevo/", views.complex_create, name="complex_create"),
    path("complejos/<int:pk>/editar/", views.complex_edit, name="complex_edit"),
    path("alojamientos/", views.accommodation_list, name="accommodation_list"),
    path("alojamientos/nuevo/", views.accommodation_create, name="accommodation_create"),
    path("alojamientos/<int:pk>/editar/", views.accommodation_edit, name="accommodation_edit"),
    path("plataforma/cuentas/", views.platform_owners, name="platform_owners"),
]
