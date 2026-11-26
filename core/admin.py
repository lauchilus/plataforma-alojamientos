from django.contrib import admin
from .models import Accommodation, BusinessAccount, Complex, Guest, PriceRule, Reservation

@admin.register(BusinessAccount)
class BusinessAccountAdmin(admin.ModelAdmin):
    list_display=("business_name","owner","is_active","base_currency","created_at")
    list_filter=("is_active","base_currency")
    search_fields=("business_name","owner__username","owner__email")
@admin.register(Complex)
class ComplexAdmin(admin.ModelAdmin):
    list_display=("name","account","city","province")
    list_filter=("account","province")
    search_fields=("name","account__business_name","city")
@admin.register(Accommodation)
class AccommodationAdmin(admin.ModelAdmin):
    list_display=("name","complex","account","kind","capacity","is_active")
    list_filter=("account","kind","is_active")
    search_fields=("name","complex__name","account__business_name")
@admin.register(PriceRule)
class PriceRuleAdmin(admin.ModelAdmin):
    list_display=("accommodation","guest_count","valid_from","valid_until","nightly_rate","currency","is_active")
    list_filter=("account","currency","is_active")
@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display=("accommodation","guest","check_in","check_out","status","total_price","currency")
    list_filter=("account","status","currency")
@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display=("full_name","phone","email","account")
    search_fields=("full_name","phone","email")
