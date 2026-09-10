from django.contrib.auth.models import Permission
from django.core.exceptions import ImproperlyConfigured
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from config.startup import ensure_owner_exists

from .models import Role, User


class AccountManagementTests(TestCase):
	def setUp(self):
		self.owner = User.objects.create_superuser(
			email="owner@example.com",
			password="StrongPassword123!",
			first_name="Super",
			last_name="Admin",
		)
		self.person = User.objects.create_user(
			email="person@example.com",
			password="StrongPassword123!",
			first_name="Marie",
			last_name="Martin",
			role=Role.SECRETARY,
		)

	def test_owner_can_create_requested_role(self):
		self.client.force_login(self.owner)
		response = self.client.post(
			reverse("users:account_management"),
			{
				"action": "create_account",
				"email": "nurse@example.com",
				"first_name": "Nina",
				"last_name": "Durand",
				"role": Role.NURSE,
				"password1": "StrongPassword123!",
				"password2": "StrongPassword123!",
				"is_active": "on",
			},
		)

		self.assertRedirects(response, reverse("users:account_management"))
		account = User.objects.get(email="nurse@example.com")
		self.assertEqual(account.role, Role.NURSE)
		self.assertTrue(account.check_password("StrongPassword123!"))

	def test_owner_can_delegate_creation_to_person(self):
		permission = Permission.objects.get(
			content_type__app_label="users",
			codename="can_create_accounts",
		)
		self.client.force_login(self.owner)
		response = self.client.post(
			reverse("users:account_management"),
			{"action": "save_permissions", "account_users": [str(self.person.pk)]},
		)

		self.assertRedirects(response, reverse("users:account_management"))
		self.person.refresh_from_db()
		self.assertTrue(self.person.has_perm("users.can_create_accounts"))
		self.assertIn(permission, self.person.user_permissions.all())

	def test_unauthorized_person_cannot_create_account(self):
		self.client.force_login(self.person)
		response = self.client.get(reverse("users:account_management"))

		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse("users:role_redirect"))
		self.assertFalse(User.objects.filter(email="blocked@example.com").exists())

	def test_startup_requires_an_owner(self):
		self.owner.is_superuser = False
		self.owner.save(update_fields=["is_superuser"])
		try:
			with self.assertRaises(ImproperlyConfigured):
				ensure_owner_exists()
		finally:
			self.owner.is_superuser = True
			self.owner.save(update_fields=["is_superuser"])

	def test_database_allows_only_one_superadmin(self):
		with self.assertRaises(ValueError):
			User.objects.create_superuser(
				email="second-owner@example.com",
				password="StrongPassword123!",
				first_name="Second",
				last_name="Owner",
			)

		second = User(
			email="second-owner@example.com",
			first_name="Second",
			last_name="Owner",
			role=Role.ADMIN,
			is_staff=True,
			is_superuser=True,
		)
		with self.assertRaises(ValidationError):
			second.save()
