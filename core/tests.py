from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from datetime import date
from decimal import Decimal
from .models import Accommodation, BusinessAccount, Complex, PriceRule, Reservation
from .services.pricing import quote_reservation

class OwnerWorkspaceTests(TestCase):
    def setUp(self):
        self.owner=User.objects.create_user(username="owner_a",password="LongSecure123!")
        self.account=BusinessAccount.objects.create(owner=self.owner,business_name="Cabañas del Lago",must_change_password=False)
        other_user=User.objects.create_user(username="owner_b",password="LongSecure123!")
        other=BusinessAccount.objects.create(owner=other_user,business_name="Casas del Bosque",must_change_password=False)
        self.complex=Complex.objects.create(account=self.account,name="Lago")
        other_complex=Complex.objects.create(account=other,name="Bosque")
        self.unit=Accommodation.objects.create(account=self.account,complex=self.complex,name="Cabaña 1",capacity=4,base_nightly_rate=Decimal("50000"))
        Accommodation.objects.create(account=other,complex=other_complex,name="Casa 1",capacity=6)
    def test_owner_only_sees_own_units(self):
        self.client.login(username="owner_a",password="LongSecure123!")
        response=self.client.get(reverse("accommodation_list"))
        self.assertContains(response,"Cabaña 1"); self.assertNotContains(response,"Casa 1")
    def test_owner_cannot_edit_another_accounts_complex(self):
        other_complex=Complex.objects.get(name="Bosque")
        self.client.login(username="owner_a",password="LongSecure123!")
        self.assertEqual(self.client.get(reverse("complex_edit",args=[other_complex.pk])).status_code,404)
    def test_initial_password_is_required_to_change(self):
        self.account.must_change_password=True; self.account.save(update_fields=["must_change_password"])
        self.client.login(username="owner_a",password="LongSecure123!")
        response=self.client.get(reverse("dashboard"))
        self.assertRedirects(response,reverse("password_change"),fetch_redirect_response=False)
    def test_reservation_price_uses_guest_and_date_rule(self):
        PriceRule.objects.create(account=self.account,accommodation=self.unit,guest_count=2,valid_from=date(2027,1,1),valid_until=date(2027,1,31),nightly_rate=Decimal("80000"),currency="ARS")
        total,currency,nights=quote_reservation(self.unit,date(2027,1,10),date(2027,1,12),2)
        self.assertEqual(total,Decimal("160000")); self.assertEqual(currency,"ARS"); self.assertEqual(nights,2)
