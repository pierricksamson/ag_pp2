"""
seed_db — peuple la base avec un jeu de données de démonstration.

Usage :
    python manage.py seed_db
"""

from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from academics.models import (
    AcademicYear,
    ClassGroup,
    Evaluation,
    Grade,
    Level,
    Subject,
    Term,
)
from messaging.models import Conversation, ConversationKind, Message
from schedule.models import CourseSession, Room
from users.models import (
    AdminProfile,
    ParentProfile,
    Role,
    StudentProfile,
    TeacherProfile,
)

User = get_user_model()

PASSWORD = "password123"

USERS_TO_CREATE = [
    {"email": "admin@test.com",   "first_name": "Admin",    "last_name": "Root",    "role": Role.ADMIN},
    {"email": "prof1@test.com",   "first_name": "Pierre",   "last_name": "Durand",  "role": Role.TEACHER},
    {"email": "prof2@test.com",   "first_name": "Sophie",   "last_name": "Martin",  "role": Role.TEACHER},
    {"email": "eleve1@test.com",  "first_name": "Lucas",    "last_name": "Bernard", "role": Role.STUDENT},
    {"email": "eleve2@test.com",  "first_name": "Emma",     "last_name": "Petit",   "role": Role.STUDENT},
    {"email": "parent1@test.com", "first_name": "Marie",    "last_name": "Bernard", "role": Role.PARENT},
]

EVAL_TITLES = ["Controle", "Devoir surveille", "Interrogation", "Examen blanc"]
SUBJECT_TEMPLATES = [
    ("MATH", "Mathematiques"),
    ("FR",   "Francais"),
    ("HIST", "Histoire"),
    ("ANG",  "Anglais"),
    ("SVT",  "Sciences de la vie et de la Terre"),
]

# Salles de démonstration
ROOM_DEFINITIONS = [
    {"name": "A101",     "capacity": 30, "location": "Bâtiment A, RDC"},
    {"name": "A202",     "capacity": 30, "location": "Bâtiment A, 1er étage"},
    {"name": "Labo SVT", "capacity": 24, "location": "Bâtiment B, RDC"},
    {"name": "Salle info", "capacity": 18, "location": "Bâtiment B, 1er étage"},
    {"name": "Gymnase",  "capacity": 60, "location": "Annexe sportive"},
]


class Command(BaseCommand):
    help = "Reinitialise la base et cree un jeu de donnees de demonstration."

    def add_arguments(self, parser):
        parser.add_argument(
            "--keep-academics",
            action="store_true",
            help="Conserve les donnees academiques existantes (annee, classes, matieres, evaluations, notes).",
        )

    # ---------- helpers ----------
    def _log(self, label, email):
        self.stdout.write(f"  * {label:<10} {email:<22} mot de passe : {PASSWORD}")

    # ---------- entree ----------
    @transaction.atomic
    def handle(self, *args, **options):
        keep_academics = options.get("keep_academics", False)

        self.stdout.write(self.style.WARNING(">> Reinitialisation des utilisateurs..."))
        self._reset_users()

        if not keep_academics:
            self.stdout.write(self.style.WARNING(">> Reinitialisation des donnees..."))
            self._reset_academics()

        self.stdout.write(self.style.SUCCESS(">> Creation du jeu de demonstration..."))

        # --- Admin
        admin = User.objects.create_superuser(
            email="admin@test.com", password=PASSWORD,
            first_name="Admin", last_name="Root", role=Role.ADMIN,
        )
        AdminProfile.objects.create(user=admin, department="Direction")
        self._log("ADMIN", admin.email)

        # --- Professeurs
        prof1 = User.objects.create_user(
            email="prof1@test.com", password=PASSWORD,
            first_name="Pierre", last_name="Durand", role=Role.TEACHER,
        )
        prof2 = User.objects.create_user(
            email="prof2@test.com", password=PASSWORD,
            first_name="Sophie", last_name="Martin", role=Role.TEACHER,
        )

        # --- Academie minimale (annee, niveau, matieres, classe, trimestre)
        year = AcademicYear.objects.create(
            label="2025-2026",
            start_date="2025-09-01", end_date="2026-07-04", is_current=True,
        )
        level = Level.objects.create(name="6eme", order=1)
        subjects = []
        for code, name in SUBJECT_TEMPLATES:
            subjects.append(Subject.objects.create(code=code, name=name, level=level))
        class_group = ClassGroup.objects.create(name="6eme A", level=level, academic_year=year)
        term = Term.objects.create(
            name="Trimestre 1", academic_year=year,
            start_date="2025-09-01", end_date="2025-12-20", is_current=True,
        )

        prof1_profile = TeacherProfile.objects.create(user=prof1, employee_number="P001", hire_date="2020-09-01")
        prof2_profile = TeacherProfile.objects.create(user=prof2, employee_number="P002", hire_date="2021-09-01")
        prof1_profile.subjects.set([s for s in subjects if s.code in ("MATH", "SVT")])
        prof2_profile.subjects.set([s for s in subjects if s.code in ("FR", "HIST", "ANG")])
        self._log("TEACHER", prof1.email)
        self._log("TEACHER", prof2.email)

        # --- Eleves
        eleve1 = User.objects.create_user(
            email="eleve1@test.com", password=PASSWORD,
            first_name="Lucas", last_name="Bernard", role=Role.STUDENT,
        )
        student1 = StudentProfile.objects.create(
            user=eleve1, student_number="S0001",
            birth_date="2010-05-12", class_group=class_group,
        )
        eleve2 = User.objects.create_user(
            email="eleve2@test.com", password=PASSWORD,
            first_name="Emma", last_name="Petit", role=Role.STUDENT,
        )
        student2 = StudentProfile.objects.create(
            user=eleve2, student_number="S0002",
            birth_date="2010-09-23", class_group=class_group,
        )
        self._log("STUDENT", eleve1.email)
        self._log("STUDENT", eleve2.email)

        # --- Parent
        parent_user = User.objects.create_user(
            email="parent1@test.com", password=PASSWORD,
            first_name="Marie", last_name="Bernard", role=Role.PARENT,
        )
        parent_profile = ParentProfile.objects.create(
            user=parent_user, occupation="Ingenieure", relation="MOTHER",
        )
        student1.parents.add(parent_profile)
        self._log("PARENT", parent_user.email)

        # --- Mails de demonstration pour Admin Root
        self._create_demo_mailbox(admin, prof1, prof2, parent_user)

        # --- Salles de l'emploi du temps
        rooms = self._create_rooms()

        # --- Emploi du temps (15h+ sur la semaine)
        schedule_count = self._create_schedule(subjects, class_group, [prof1_profile, prof2_profile], rooms)

        # --- Evaluations + Notes
        self._create_evaluations_and_grades(subjects, class_group, term, [prof1_profile, prof2_profile], [student1, student2])

        self._print_summary(schedule_count)

    def _create_demo_mailbox(self, admin, prof1, prof2, parent):
        """Prépare une boîte de réception utile dès la première connexion."""
        incoming = [
            (prof1, "Réunion pédagogique", "Bonjour Admin Root, peut-on prévoir la réunion pédagogique jeudi à 16h ?"),
            (prof2, "Besoin d'une salle", "Bonjour, la salle A202 serait-elle disponible pour le prochain devoir ?"),
            (parent, "Question concernant Lucas", "Bonjour, pouvez-vous me confirmer la date du prochain conseil de classe ?"),
        ]
        for sender, subject, body in incoming:
            conversation = Conversation.objects.create(kind=ConversationKind.MAIL, subject=subject)
            conversation.participants.set([sender, admin])
            message = Message.objects.create(
                conversation=conversation,
                sender=sender,
                subject=subject,
                body=body,
            )
            message.to_recipients.add(admin)

        conversation = Conversation.objects.create(
            kind=ConversationKind.MAIL,
            subject="Rappel de rentrée",
        )
        conversation.participants.set([admin, prof1])
        message = Message.objects.create(
            conversation=conversation,
            sender=admin,
            subject="Rappel de rentrée",
            body="Merci de vérifier les classes et les emplois du temps avant la rentrée.",
        )
        message.to_recipients.add(prof1)

    # ---------- evaluations + notes ----------
    def _create_evaluations_and_grades(self, subjects, class_group, term, teachers, students):
        import random
        random.seed(42)
        evaluations_count = 0
        grades_count = 0
        teacher_by_subject_code = {
            "MATH": teachers[0], "SVT": teachers[0],
            "FR":   teachers[1], "HIST": teachers[1], "ANG": teachers[1],
        }

        forced_status_cycle = [
            Grade.Status.PRESENT,
            Grade.Status.PRESENT,
            Grade.Status.PRESENT,
            Grade.Status.ABSENT,
            Grade.Status.DISPENSED,
            Grade.Status.NOT_SUBMITTED,
        ]
        cycle_idx = 0

        for subject in subjects:
            teacher = teacher_by_subject_code[subject.code]
            eval_count = 3 + random.randint(0, 2)
            for i in range(eval_count):
                title = f"{random.choice(EVAL_TITLES)} - {subject.code}{i+1}"
                coef = random.choice([1, 1, 1, 2, 2.5])
                day = date(2025, 10, 1) + timedelta(days=random.randint(0, 60))
                ev = Evaluation.objects.create(
                    title=title, subject=subject, class_group=class_group,
                    teacher=teacher, term=term, date=day,
                    coefficient=coef, scale_max=20,
                )
                evaluations_count += 1
                for stu in students:
                    status = forced_status_cycle[cycle_idx % len(forced_status_cycle)]
                    cycle_idx += 1
                    if status == Grade.Status.PRESENT:
                        base = 14.0 if stu.student_number == "S0001" else 11.5
                        noise = random.uniform(-3.5, 3.5)
                        value = round(min(20, max(6, base + noise)), 2)
                        Grade.objects.create(
                            evaluation=ev, student=stu,
                            value=value, status=Grade.Status.PRESENT,
                            comment="",
                        )
                    else:
                        Grade.objects.create(
                            evaluation=ev, student=stu,
                            value=None, status=status,
                            comment={
                                Grade.Status.ABSENT: "Absent le jour de l'epreuve",
                                Grade.Status.DISPENSED: "Dispense medical",
                                Grade.Status.NOT_SUBMITTED: "Devoir non rendu",
                            }[status],
                        )
                    grades_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"  >> {evaluations_count} evaluations et {grades_count} notes generees."
        ))

    # ---------- salles ----------
    def _create_rooms(self):
        rooms = []
        for r in ROOM_DEFINITIONS:
            rooms.append(Room.objects.create(**r))
        self.stdout.write(self.style.SUCCESS(f"  >> {len(rooms)} salles creees."))
        return {r.name: r for r in rooms}

    # ---------- emploi du temps ----------
    def _create_schedule(self, subjects, class_group, teachers, rooms):
        """Génère un EDT réaliste : ≥ 15h/semaine pour la classe, réparties
        sur 4 jours. Les profs recoivent les séances qui leur correspondent.
        """
        import random
        random.seed(7)
        prof1, prof2 = teachers
        teacher_by_code = {"MATH": prof1, "SVT": prof1, "FR": prof2, "HIST": prof2, "ANG": prof2}

        # Planning type "collège" : matin 8h-12h, après-midi 14h-16h
        # On vise ~17h pour la classe.
        schedule = [
            # (jour, début, fin, matière, salle)
            ("MON", time(8, 0),  time(9, 0),  "MATH", "A101"),
            ("MON", time(9, 0),  time(10, 0), "FR",   "A101"),
            ("MON", time(10, 15), time(11, 15), "ANG", "A202"),
            ("MON", time(14, 0), time(15, 0),  "HIST", "A101"),
            ("MON", time(15, 0), time(16, 0),  "SVT",  "Labo SVT"),
            ("TUE", time(8, 0),  time(9, 0),  "FR",   "A101"),
            ("TUE", time(9, 0),  time(10, 0),  "MATH", "A101"),
            ("TUE", time(10, 15), time(11, 15), "SVT",  "Labo SVT"),
            ("WED", time(8, 0),  time(9, 0),   "ANG",  "Salle info"),
            ("WED", time(9, 0),  time(10, 0),  "HIST", "A101"),
            ("WED", time(10, 15), time(11, 15), "MATH", "A101"),
            ("WED", time(14, 0), time(15, 30),  "EPS",  "Gymnase"),  # sport via FR/HIST ? on l'attache à HIST pour l'exemple
            ("THU", time(8, 0),  time(9, 0),   "MATH", "A101"),
            ("THU", time(9, 0),  time(10, 0),  "FR",   "A101"),
            ("THU", time(10, 15), time(11, 15), "ANG",  "Salle info"),
            ("THU", time(14, 0), time(15, 0),  "SVT",  "Labo SVT"),
            ("FRI", time(8, 0),  time(9, 0),   "HIST", "A101"),
            ("FRI", time(9, 0),  time(10, 0),  "MATH", "A101"),
            ("FRI", time(10, 15), time(11, 15), "FR",  "A101"),
        ]

        # Crée un sujet "EPS" s'il n'existe pas, pour le créneau sport du mercredi.
        eps_subject, _ = Subject.objects.get_or_create(
            code="EPS",
            defaults={"name": "Éducation physique et sportive", "level": class_group.level},
        )
        # On rattache EPS à prof2 (qui dispense ANG/HIST/FR) pour simplifier
        prof2.subjects.add(eps_subject)

        subjects_by_code = {s.code: s for s in subjects}
        subjects_by_code["EPS"] = eps_subject

        count = 0
        total_minutes = 0
        for day, start_t, end_t, code, room_name in schedule:
            subject = subjects_by_code.get(code)
            if subject is None:
                continue
            teacher = teacher_by_code.get(code, prof2)
            sess = CourseSession.objects.create(
                subject=subject,
                teacher=teacher,
                room=rooms.get(room_name),
                day=day,
                start_time=start_t,
                end_time=end_t,
            )
            sess.class_groups.add(class_group)
            count += 1
            total_minutes += (end_t.hour * 60 + end_t.minute) - (start_t.hour * 60 + start_t.minute)

        # Ajout d'un créneau supplémentaire pour garantir ≥ 15h et colorer
        # davantage l'EDT de prof1 (mathématiques).
        if total_minutes < 15 * 60:
            extra = CourseSession.objects.create(
                subject=subjects_by_code["MATH"],
                teacher=prof1,
                room=rooms["A101"],
                day="FRI",
                start_time=time(14, 0),
                end_time=time(15, 0),
            )
            extra.class_groups.add(class_group)
            count += 1
            total_minutes += 60

        hours = total_minutes // 60
        self.stdout.write(self.style.SUCCESS(
            f"  >> {count} seances creees pour la classe (~{hours} h cumulees)."
        ))
        return count

    # ---------- reset ----------
    def _reset_users(self):
        from academics.models import Grade
        Grade.objects.all().delete()
        Message.objects.all().delete()
        Conversation.objects.all().delete()
        AdminProfile.objects.all().delete()
        StudentProfile.objects.all().delete()
        ParentProfile.objects.all().delete()
        TeacherProfile.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        User.objects.filter(is_superuser=True).delete()

    def _reset_academics(self):
        from schedule.models import CourseSession, Room
        Grade.objects.all().delete()
        Evaluation.objects.all().delete()
        CourseSession.objects.all().delete()
        Room.objects.all().delete()
        Term.objects.all().delete()
        Subject.objects.all().delete()
        ClassGroup.objects.all().delete()
        Level.objects.all().delete()
        AcademicYear.objects.all().delete()

    # ---------- recapitulatif ----------
    def _print_summary(self, schedule_count):
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 64))
        self.stdout.write(self.style.SUCCESS(" Comptes crees (mot de passe commun : password123)"))
        self.stdout.write(self.style.SUCCESS("=" * 64))
        rows = [
            ("ADMIN",   "admin@test.com"),
            ("TEACHER", "prof1@test.com"),
            ("TEACHER", "prof2@test.com"),
            ("STUDENT", "eleve1@test.com"),
            ("STUDENT", "eleve2@test.com"),
            ("PARENT",  "parent1@test.com"),
        ]
        for role, email in rows:
            self.stdout.write(f"  {role:<8} {email:<22}  {PASSWORD}")
        self.stdout.write(self.style.SUCCESS("=" * 64))
        self.stdout.write(self.style.WARNING(f" {schedule_count} seances planifiees pour la classe '6eme A'."))
        self.stdout.write(self.style.WARNING(" Connexion : http://127.0.0.1:8123/login/"))