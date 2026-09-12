# Espace scolaire

Application web Django pour gérer un établissement scolaire, de l'école
primaire aux études supérieures. L'authentification se fait par **email**
(pas de nom d'utilisateur) et chaque utilisateur a un **rôle**
(`ADMIN`, `TEACHER`, `STUDENT`, `PARENT`) qui conditionne l'accès aux
différentes rubriques.

Le projet en est à l'**étape 5** : emploi du temps hebdomadaire universel
+ saisie des notes façon tableur.

---

## Sommaire

1. [Installation & lancement](#installation--lancement)
2. [Comptes de test](#comptes-de-test)
3. [Architecture](#architecture)
4. [Emploi du temps (`schedule`)](#emploi-du-temps-schedule)
5. [Évaluations & saisie de notes (`academics`)](#évaluations--saisie-de-notes-academics)
6. [Internationalisation](#internationalisation)

---

## Installation & lancement

### Prérequis
- Python 3.12 (testé sur la version fournie par Microsoft Store)
- Windows (le script `run_dev.bat` lance le serveur sur Windows)

### Mise en route

```bash
# 1. Créer l'environnement virtuel (déjà présent dans le repo sous .venv/)
python -m venv .venv

# 2. Installer les dépendances
.venv\Scripts\pip.exe install -r requirements.txt

# 3. Appliquer les migrations
.venv\Scripts\python.exe manage.py migrate

# 4. (Optionnel) Charger un jeu de démonstration complet
.venv\Scripts\python.exe manage.py seed_db

# 5. Lancer le serveur de développement
.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8123
# ou plus simplement :
run_dev.bat
```

L'application est ensuite accessible à l'adresse :
**http://127.0.0.1:8123/**

> La commande `seed_db` réinitialise *toute* la base de démonstration.
> Ajoutez `--keep-academics` pour ne conserver que les comptes.

---

## Comptes de test

Tous les comptes utilisent le même mot de passe : **`password123`**.

Le compte propriétaire super-administrateur est : **`admin@test.com`** / **`password123`**.
L'application refuse de démarrer si aucun compte super-administrateur n'existe.

| Rôle       | Email               | Mot de passe   | Accès                                                         |
|------------|---------------------|----------------|---------------------------------------------------------------|
| Admin      | `admin@test.com`    | `password123`  | Tout, dont filtres sur l'emploi du temps + admin Django.      |
| Professeur | `prof1@test.com`    | `password123`  | Ses séances, ses évaluations, saisie des notes.               |
| Professeur | `prof2@test.com`    | `password123`  | Idem.                                                         |
| Élève      | `eleve1@test.com`   | `password123`  | EDT de sa classe (`6ème A`), ses notes.                        |
| Élève      | `eleve2@test.com`   | `password123`  | Idem.                                                         |
| Parent     | `parent1@test.com`  | `password123`  | Notes de ses enfants (sélecteur si plusieurs).                |

L'admin Django (`/admin/`) est accessible avec n'importe quel compte
`is_staff=True` — pratique : `admin@test.com`.

---

## Architecture

```
ag_pp2/
├── config/                # Réglages Django (settings, urls racine)
├── users/                 # Authentification, rôles, profils 1-1
├── academics/             # Année, niveaux, classes, matières, évaluations, notes
├── schedule/              # Salles + séances hebdomadaires (étape 5)
├── attendance/            # Appels (FK vers CourseSession)
├── messaging/             # Messagerie interne
├── templates/             # Templates HTML globaux (base.html, dashboards…)
│   ├── base.html
│   ├── academics/         # Liste / création / saisie des évaluations
│   ├── schedule/          # Grille hebdomadaire
│   └── users/             # Dashboards + login
├── static/                # (réservé aux assets statiques futurs)
├── manage.py
├── run_dev.bat            # Lance le serveur sur 127.0.0.1:8123
├── requirements.txt
└── db.sqlite3             # Base SQLite locale
```

### Rôle de chaque app

| App         | Rôle                                                                          |
|-------------|-------------------------------------------------------------------------------|
| `users`     | Modèle `User` (email = identifiant), `Role`, profils 1-1 (`StudentProfile`, `TeacherProfile`, `ParentProfile`, `AdminProfile`). Gère login/logout/redirect par rôle. |
| `academics` | Référentiels (AcademicYear, Level, Subject, ClassGroup, Term) + évaluations + notes. Calcule moyennes simples et pondérées. |
| `schedule`  | Salles et séances hebdomadaires (Room, CourseSession). Vue hebdomadaire adaptée au rôle. |
| `attendance`| Appels : une `AttendanceRecord` par (élève, séance). FK vers `schedule.CourseSession`. |
| `messaging` | Fils de discussion / annonces internes.                                       |

---

## Emploi du temps (`schedule`)

### Modèles (`schedule/models.py`)

- **`Room`** : nom unique, capacité, indication libre de localisation.
- **`CourseSession`** : séance hebdomadaire caractérisée par :
  - un intitulé (optionnel — sinon on prend le nom de la matière),
  - **plusieurs `ClassGroup`** (relation `ManyToMany`) → utile pour les
    cours magistraux, les cours pluriannuels (CM1+CM2) ou les TD regroupés,
  - une `Subject` (matière),
  - un `TeacherProfile` (enseignant),
  - une `Room` (salle),
  - un `day` (Lundi → Samedi) + **`start_time` / `end_time`** directement,
  - une couleur optionnelle (classe Tailwind).

Les horaires sont stockés en `TimeField` (et non via un créneau fixe) pour
supporter aussi bien des cours de 55 minutes au collège que des amphis
de 4 h dans le supérieur.

### Vue `weekly_schedule` (`schedule/views.py`)

URL : **`/schedule/`**

La grille est rendue par `templates/schedule/weekly.html` qui utilise
CSS Grid pour placer les cartes (`grid-row-start` calculé depuis
`start_time`).

| Rôle          | Comportement                                                                                 |
|---------------|----------------------------------------------------------------------------------------------|
| **Élève**     | Affiche automatiquement l'EDT de la classe associée à son profil.                          |
| **Professeur**| Affiche ses propres séances (filtrées sur `teacher=self`).                                  |
| **Admin**     | Affiche un panneau de filtres (classe, professeur, salle) qui combine des `Q()` objects.    |
| **Parent**    | Redirige vers la page notes (sélection d'enfant).                                            |

L'interface est **entièrement responsive** : sur petit écran, une
barre de scroll horizontal apparaît si nécessaire. La grille couvre
Lundi → Samedi, de 08h00 à 19h00 par pas de 30 min.

### Carte de séance

Chaque cours est une carte colorée automatiquement (palette déterministe
basée sur le code matière) contenant :
- horaires (`08:00 — 09:00`),
- intitulé ou nom de matière,
- salle (icône 📍),
- professeur (icône 👤),
- liste des classes si plusieurs.

---

## Évaluations & saisie de notes (`academics`)

### Modèles (`academics/models.py`)

- **`Evaluation`** : titre, matière, classe, professeur, trimestre, date,
  coefficient, note maximale. Des propriétés calculent moyenne / min / max
  en direct.
- **`Grade`** : une ligne par (élève, évaluation), avec :
  - `value` (note),
  - `status` parmi `PRESENT`, `ABSENT`, `DISPENSED`, `NOT_SUBMITTED`,
  - `comment` (appréciation).

### Saisie « façon Excel »

URL : **`/academics/evaluations/<id>/entry/`**

Le template `templates/academics/evaluation_entry.html` a été refondu
pour offrir la saisie la plus rapide possible :

- Une ligne par élève avec : **note** (texte court), **statut** (select),
  **commentaire** (texte libre), indicateur d'état visuel.
- **Navigation au clavier** :
  - `Entrée` ou `Tab` sur une note → focus sur la ligne suivante et
    sauvegarde en AJAX.
  - Raccourcis saisis dans la note :
    - `ABS` / `A` → statut **Absent** + sauvegarde auto.
    - `DISP` / `D` → statut **Dispensé**.
    - `NR` / `N` → statut **Non rendu**.
    - sinon la valeur est parsée comme nombre décimal (virgule acceptée).
- **Sauvegarde AJAX** : `POST /academics/api/grade/<id>/save/` met à
  jour la note, puis renvoie les statistiques live (moyenne, min, max,
  présence) qui sont rafraîchies dans les cartes en haut de la page.
- **Bouton collant en bas** : `Sauvegarder toutes les notes` (toujours
  visible) ; un clic sauvegarde tous les élèves encore modifiés en
  parallèle. Raccourci : `Ctrl/Cmd + S`.
- **Compteurs live** : nombre de saisies modifiées + nombre de
  sauvegardes effectuées.
- **Indicateur visuel d'état** : 🟠 modifié · 🔵 sauvegarde · 🟢 sauvé · 🔴 erreur.

En cas de JavaScript désactivé, le formulaire se soumet normalement en
POST (mode bulk) et toutes les notes sont enregistrées en une seule
transaction Django.

### Endpoint AJAX — `grade_save_ajax`

`POST /academics/api/grade/<grade_id>/save/`

Payload :
```json
{ "value": "12.5", "status": "PRESENT", "comment": "Bon travail" }
```

Réponse :
```json
{
  "ok": true,
  "grade": { "id": 42, "value": 12.5, "status": "PRESENT", "comment": "..." },
  "stats": { "average": 13.4, "min": 7.5, "max": 18.0, "present": 18, "total": 22, "attendance_rate": 81.8 }
}
```

La vue refuse les requêtes d'un professeur qui n'est pas propriétaire
de l'évaluation.

### Vue « relevé » (élève / parent)

`/academics/grades/` — affiche la moyenne par matière, la moyenne
générale pondérée, le min/max de chaque évaluation, et un sélecteur de
trimestre.

---

## Internationalisation

`LANGUAGE_CODE = "fr-fr"`, `TIME_ZONE = "UTC"`. Tous les libellés
utilisent `gettext_lazy`. Le frontend reste en français.

---

## Commandes utiles

```bash
# Créer un super-utilisateur à la main
.venv\Scripts\python.exe manage.py createsuperuser

# Réinitialiser uniquement la base
rm db.sqlite3 && .venv\Scripts\python.exe manage.py migrate

# Juste recharger les données de démo
.venv\Scripts\python.exe manage.py seed_db

# Recharger en gardant les comptes
.venv\Scripts\python.exe manage.py seed_db --keep-academics

# Lancer les tests
.venv\Scripts\python.exe manage.py test
```

---

## Roadmap

- [x] Étape 1 — Modèle `User` + rôles
- [x] Étape 2 — Académique : niveaux, classes, matières
- [x] Étape 3 — Évaluations + notes (vue prof)
- [x] Étape 4 — Relevé de notes élève/parent
- [x] **Étape 5 — Emploi du temps + saisie Excel-like** ← vous êtes ici
- [ ] Étape 6 — Appels (attendance)
- [ ] Étape 7 — Messagerie interne

