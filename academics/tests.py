from django.test import TestCase
from django.urls import reverse

from users.models import User

from .models import AcademicYear, ClassGroup, Level


class EstablishmentManagementTests(TestCase):
	def setUp(self):
		self.owner = User.objects.create_superuser(
			email="owner@example.com",
			password="StrongPassword123!",
			first_name="Super",
			last_name="Admin",
		)

	def test_owner_can_create_year_level_and_class(self):
		self.client.force_login(self.owner)
		self.client.post(reverse("academics:establishment_management"), {
			"action": "create_year",
			"label": "2026-2027",
			"start_date": "2026-09-01",
			"end_date": "2027-07-01",
			"is_current": "on",
		})
		self.client.post(reverse("academics:establishment_management"), {
			"action": "create_level", "name": "6e", "order": "1",
		})
		self.client.post(reverse("academics:establishment_management"), {
			"action": "create_class",
			"name": "A",
			"level": Level.objects.get(name="6e").pk,
			"academic_year": AcademicYear.objects.get(label="2026-2027").pk,
		})

		self.assertTrue(ClassGroup.objects.filter(name="A").exists())
