from datetime import date
from decimal import Decimal
from unittest.mock import patch
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from .models import Accommodation,BusinessAccount,Complex,PriceRule
from .services.pricing import quote_reservation
from .finance_models import Expense,InventoryItem,Payment,Reservation
from .services.inventory import record_movement

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
  response=self.client.get(reverse("accommodation_list")); self.assertContains(response,"Cabaña 1"); self.assertNotContains(response,"Casa 1")
 def test_owner_cannot_edit_another_accounts_complex(self):
  other_complex=Complex.objects.get(name="Bosque")
  self.client.login(username="owner_a",password="LongSecure123!")
  self.assertEqual(self.client.get(reverse("complex_edit",args=[other_complex.pk])).status_code,404)
 def test_initial_password_is_required_to_change(self):
  self.account.must_change_password=True; self.account.save(update_fields=["must_change_password"])
  self.client.login(username="owner_a",password="LongSecure123!")
  self.assertRedirects(self.client.get(reverse("dashboard")),reverse("password_change"),fetch_redirect_response=False)
 def test_reservation_price_uses_guest_and_date_rule(self):
  PriceRule.objects.create(account=self.account,accommodation=self.unit,guest_count=2,valid_from=date(2027,1,1),valid_until=date(2027,1,31),nightly_rate=Decimal("80000"),currency="ARS")
  total,currency,nights=quote_reservation(self.unit,date(2027,1,10),date(2027,1,12),2)
  self.assertEqual(total,Decimal("160000")); self.assertEqual(currency,"ARS"); self.assertEqual(nights,2)
 def test_overlapping_reservation_is_rejected(self):
  from .models import Guest,Reservation
  guest=Guest.objects.create(account=self.account,full_name="Ana")
  first=Reservation(account=self.account,accommodation=self.unit,guest=guest,check_in=date(2027,2,1),check_out=date(2027,2,4),guest_count=2,status="CONFIRMED",total_price=Decimal("50000"),currency="ARS"); first.full_clean(); first.save()
  second=Reservation(account=self.account,accommodation=self.unit,guest=guest,check_in=date(2027,2,3),check_out=date(2027,2,5),guest_count=2,status="CONFIRMED",total_price=Decimal("50000"),currency="ARS")
  from django.core.exceptions import ValidationError
  with self.assertRaises(ValidationError): second.full_clean()

class FinanceInventoryTests(TestCase):
 def setUp(self):
  u=User.objects.create_user(username="owner",password="LongSecure123!")
  self.account=BusinessAccount.objects.create(owner=u,business_name="Complejo",must_change_password=False)
  c=Complex.objects.create(account=self.account,name="Costa")
  self.unit=Accommodation.objects.create(account=self.account,complex=c,name="Casa",capacity=4,base_nightly_rate=Decimal("10"))
  from .models import Guest
  g=Guest.objects.create(account=self.account,full_name="Huésped")
  self.reservation=Reservation.objects.create(account=self.account,accommodation=self.unit,guest=g,check_in=date(2027,1,1),check_out=date(2027,1,3),guest_count=2,status="CONFIRMED",total_price=Decimal("100"),currency="ARS")
 def test_same_currency_payment_is_saved_without_external_quote(self):
  from .finance_forms import PaymentForm
  form=PaymentForm({"reservation":self.reservation.pk,"amount":"40","currency":"ARS","method":"CASH","paid_on":"2027-01-01","reference":""},account=self.account)
  self.assertTrue(form.is_valid(),form.errors)
  payment=form.save()
  self.assertEqual(payment.reservation_amount,Decimal("40.00")); self.assertEqual(payment.base_amount,Decimal("40.00"))
 def test_reservation_balance_tracks_payments(self):
  from .finance_models import Payment
  payment=Payment.objects.create(account=self.account,reservation=self.reservation,amount=Decimal("40"),currency="ARS",method="CASH",paid_on=date(2027,1,1),reservation_amount=Decimal("40"),reservation_currency="ARS",base_amount=Decimal("40"),base_currency="ARS")
  self.assertEqual(self.reservation.paid_amount,Decimal("40"))
  self.assertEqual(self.reservation.balance_due,Decimal("60"))
 def test_linen_delivery_and_used_return_update_stock(self):
  from .finance_forms import InventoryMovementForm
  item=InventoryItem.objects.create(account=self.account,accommodation=self.unit,name="Sábanas",category="Blanquería",track_per_stay=True,clean_quantity=5)
  form=InventoryMovementForm({"item":item.pk,"movement_type":"DELIVER_CLEAN","quantity":1,"reservation":"","source_state":"","notes":""},account=self.account)
  self.assertFalse(form.is_valid())
  self.assertIn("reservation",form.errors)
  
  record_movement(item,"DELIVER_CLEAN",2,self.account,self.reservation)
  item.refresh_from_db(); self.assertEqual(item.clean_quantity,3); self.assertEqual(item.in_use_quantity,2)
  record_movement(item,"RETURN_USED",1,self.account,self.reservation)
  item.refresh_from_db(); self.assertEqual(item.in_use_quantity,1); self.assertEqual(item.used_quantity,1)
