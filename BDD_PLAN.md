# Plan BDD - Ag PP2 (Espace Scolaire)

## Vue d'Ensemble

Projet : **Ag PP2** - Système de gestion scolaire (Django)
Version actuelle : Étape 5 (Emploi du temps hebdomadaire)

## Schéma de la Base de Données

### 1. Utilisateurs (users)

| Modèle | Description | Clés principales |
|--------|-------------|------------------|
| **User** | Utilisateur principal (email = identifiant) | `email` (unique), `username` (vide), `first_name`, `last_name`, `role`, `phone`, `is_active`, `created_at`, `updated_at` |
| **Role** | Choix de rôle | `ADMIN`, `TEACHER`, `STUDENT`, `PARENT` |
| **TeacherProfile** | Profil du professeur (1:1 avec User TEACHER) | `user` (OneToOne), `employee_number`, `subjects` (ManyToMany), `hire_date` |
| **StudentProfile** | Profil de l'élève (1:1 avec User STUDENT) | `user` (OneToOne), `student_number`, `birth_date`, `class_group` (ManyToMany), `parents` (ManyToMany) |
| **ParentProfile** | Profil du parent (1:1 avec User PARENT) | `user` (OneToOne), `occupation`, `relation` (Mère/Father/Tuteur/Lautre) |
| **AdminProfile** | Profil de l'administrateur (1:1 avec User ADMIN) | `user` (OneToOne), `department`, `is_superuser` |

### 2. Académique (academics)

| Modèle | Description | Clés principales |
|--------|-------------|------------------|
| **AcademicYear** | Année scolaire | `label`, `start_date`, `end_date`, `is_current` |
| **Level** | Niveau scolaire (6ème, 5ème, etc.) | `name`, `order` |
| **Subject** | Matière enseignée | `code`, `name`, `level` (ForeignKey) |
| **ClassGroup** | Classe (ex: 6ème A) | `name`, `level`, `academic_year`, `class_groups` (ManyToMany) |
| **Term** | Trimestre / période | `name`, `academic_year`, `start_date`, `end_date`, `is_current` |
| **Evaluation** | Épreuve notée | `title`, `subject`, `class_group`, `teacher` (ForeignKey), `term`, `date`, `coefficient`, `scale_max`, `created_at`, `updated_at` |
| **Grade** | Note d'un élève | `student` (ForeignKey), `evaluation`, `value`, `status` (PRESENT/ABSENT/DISPENSED/NOT_SUBMITTED), `comment`, `created_at`, `updated_at` |

### 3. Planning (schedule)

| Modèle | Description | Clés principales |
|--------|-------------|------------------|
| **Room** | Salle physique | `name` (unique), `capacity`, `location` |
| **CourseSession** | Séance hebdomadaire | `day` (LUN/MAR/WEC/THU/FRI/SAT), `title`, `class_groups` (ManyToMany), `subject`, `teacher`, `room` (optional), `start_time`, `end_time`, `color` (Tailwind class) |

### 4. Présence (attendance)

| Modèle | Description | Clés principales |
|--------|-------------|------------------|
| **AttendanceRecord** | Feuille de présence (élève × séance) | `student` (ForeignKey), `session` (ForeignKey), `status` (PRESENT/LATE/ABSENT/EXCUSED), `minutes_late`, `reason`, `justified`, `recorded_at`, `recorded_by` (ForeignKey) |
| **AbsenceJustification** | Justification d'absence | `attendance` (ForeignKey), `submitted_by` (ForeignKey), `reason`, `status` (PENDING/APPROVED/REJECTED) |

### 5. Messagerie (messaging)

| Modèle | Description | Clés principales |
|--------|-------------|------------------|
| **Conversation** | Groupe de discussion | `subject` (optional), `participants` (ManyToMany), `created_at` |
| **Message** | Message dans une conversation | `sender` (ForeignKey), `body`, `sent_at`, `read_at` |

## Relations Principales

- **User** ↔ **Role** (choice)
- **User** ↔ **TeacherProfile** (1:1, role=TEACHER)
- **User** ↔ **StudentProfile** (1:1, role=STUDENT)
- **User** ↔ **ParentProfile** (1:1, role=PARENT)
- **TeacherProfile** ↔ **CourseSession** (1:many)
- **StudentProfile** ↔ **ClassGroup** (1:many)
- **CourseSession** ↔ **AttendanceRecord** (1:many)
- **AttendanceRecord** ↔ **AbsenceJustification** (1:many)
- **CourseSession** ↔ **Schedule.Room** (optional)
- **CourseSession** ↔ **Academics.Subject** (foreign key)
- **Evaluation** ↔ **Grade** (1:many)
- **Evaluation** ↔ **CourseSession** (1:many)
- **Grade** ↔ **User** (via StudentProfile)

## Migration Actuelle

- 5 migrations existantes (0001-0005) dans `users/migrations/`
- Base de données SQLite (`db.sqlite3`) prête
- Commande `seed_db` disponible pour réinitialiser la base

## Étapes Restantes (Roadmap)

1. **Étape 6** – Appels (Attendance) – Implémenter la saisie des présences
2. **Étape 7** – Messagerie interne – Compléter le système de discussions
3. **Étape 8** – Intégration complète et tests

## Plan d'Action pour 21h40

- Valider le schéma BDD ci-dessus
- Vérifier que toutes les migrations sont appliquées
- S'assurer que la base de données est prête pour la mise en production
- Documenter les relations clés pour la maintenance future

---

*Plan BDD généré le 2026-9-7 21h40*
