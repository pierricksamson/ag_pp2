from datetime import time

from django.core.exceptions import ValidationError
from django.test import TestCase

from academics.models import AcademicYear, ClassGroup, Level, Subject
from users.models import Role, TeacherProfile, User

from .models import CourseSession, Room
from .forms import CourseSessionForm
from .services import validate_session_conflicts


class CourseSessionValidationTests(TestCase):
	def setUp(self):
		self.year = AcademicYear.objects.create(
			label="2026-2027",
			start_date="2026-09-01",
			end_date="2027-07-31",
		)
		self.level = Level.objects.create(name="Sixième", order=1)
		self.class_group = ClassGroup.objects.create(
			name="A", level=self.level, academic_year=self.year
		)
		self.subject = Subject.objects.create(
			code="MAT", name="Mathématiques", level=self.level
		)
		user = User.objects.create_user(
			email="teacher@example.com",
			password="password",
			first_name="Ada",
			last_name="Lovelace",
			role=Role.TEACHER,
		)
		self.teacher = TeacherProfile.objects.create(user=user)
		self.room = Room.objects.create(name="Salle A")

	def make_session(self, **overrides):
		values = {
			"subject": self.subject,
			"teacher": self.teacher,
			"room": self.room,
			"day": CourseSession.Day.MONDAY,
			"start_time": time(8, 0),
			"end_time": time(9, 0),
		}
		values.update(overrides)
		session = CourseSession(**values)
		session.full_clean(exclude=["class_groups"])
		session.save()
		session.class_groups.add(self.class_group)
		return session

	def test_end_time_must_be_after_start_time(self):
		session = CourseSession(
			subject=self.subject,
			teacher=self.teacher,
			day=CourseSession.Day.MONDAY,
			start_time=time(9, 0),
			end_time=time(9, 0),
		)

		with self.assertRaises(ValidationError):
			session.full_clean(exclude=["class_groups"])

	def test_conflicting_teacher_is_rejected(self):
		self.make_session()
		conflicting = CourseSession(
			subject=self.subject,
			teacher=self.teacher,
			room=Room.objects.create(name="Salle B"),
			day=CourseSession.Day.MONDAY,
			start_time=time(8, 30),
			end_time=time(9, 30),
		)

		with self.assertRaises(ValidationError):
			validate_session_conflicts(conflicting, [self.class_group.id])

	def test_form_accepts_a_valid_session(self):
		form = CourseSessionForm(data={
			"title": "Cours de maths",
			"class_groups": [self.class_group.id],
			"subject": self.subject.id,
			"teacher": self.teacher.id,
			"room": self.room.id,
			"day": CourseSession.Day.MONDAY,
			"start_time": "08:00",
			"end_time": "09:00",
			"color": "",
		})

		self.assertTrue(form.is_valid(), form.errors)
