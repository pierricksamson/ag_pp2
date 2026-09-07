# Ademi Project Memory

Updated: 2026-09-07T17:39:34.586Z
Project: ag_pp2
Project path: \\?\C:\Users\Pierrick\Documents\MainFolder\projets\ag_pp2

## Purpose

This file preserves the working brief for Ademi runs. Use it to remember earlier user intent, requirements, and follow-up context when the chat message is short.

## Operating Rules

- Treat short user follow-ups as continuations of the same project brief.
- If previous context plus the current request is enough to act, build instead of asking the same clarification again.
- Keep this file current when the user changes the goal, product, audience, copy, design direction, or technical requirements.
- For example, if the user first asks for a landing page and later says "on Algeria", build a landing page about Algeria.

## Current Request

Étape 6 : Système d'Appel (Absences) & Messagerie Interne/Externe

Nous allons implémenter deux modules vitaux : le suivi des absences en temps réel et un système de messagerie pour la communication entre les utilisateurs.

1. Module d'Absences & Retards (attendance/models.py & Vues)
Modèle AbsenceRecord :

Lié à une CourseSession (la séance de l'EDT) et un StudentProfile.

Statut : PRESENT, LATE (Retard), ABSENT.

minutes_late (entier, optionnel).

justified (booléen) et justification_reason (texte).

Interface "Faire l'appel" pour le Professeur :

Sur la page d'accueil du prof, affiche une carte "Cours en cours / Prochain cours" (basée sur l'heure actuelle) avec un bouton "Faire l'appel".

L'interface d'appel doit ressembler à celle des notes (Excel-like) : la liste des élèves avec des boutons radio géants ou des raccourcis clavier pour marquer rapidement "Présent", "Absent" ou "Retard".

Interface "Vie Scolaire / Parents" :

Le parent voit les absences de son enfant sur son dashboard avec un bouton "Justifier" (qui envoie une justification à valider).

2. Module Messagerie Interne/Externe (messaging/models.py)
Nous voulons un système de tickets/conversations, similaire à l'interface Pronote.

Modèles :

Conversation : Sujet, participants (ManyToMany User).

Message : Auteur, contenu, date, lié à une Conversation.

Interface (/messaging/) :

Une boîte de réception de style "Webmail" (liste des conversations à gauche, contenu du message à droite).

Possibilité de créer une nouvelle conversation en choisissant les destinataires (ex: un parent cherche à écrire aux professeurs de son enfant).

Passerelle Email (Externe) :

Pour simuler la réception d'emails depuis l'extérieur (sans configurer un serveur SMTP complet pour le moment), crée un endpoint d'API sécurisé (/messaging/api/incoming_mail/) ou une commande de management (python manage.py fetch_emails).

Explique dans les commentaires (ou le README) comment relier cela plus tard à un webhook (ex: SendGrid/Mailgun Inbound Parse).

3. Seeder (seed_db.py)
Ajoute quelques absences non justifiées à eleve1 pour tester l'interface parent.

Crée une conversation de test entre parent1 et prof1.

4. Mise à jour du README.md
Mets à jour le README.md avec ces nouvelles fonctionnalités.

Explique brièvement la logique choisie pour les emails entrants.

Fournis l'ensemble du code (modèles, vues, templates) et les instructions de migration.

## Conversation Context

[USER 2026-09-07T17:39:34.586Z]
Étape 6 : Système d'Appel (Absences) & Messagerie Interne/Externe

Nous allons implémenter deux modules vitaux : le suivi des absences en temps réel et un système de messagerie pour la communication entre les utilisateurs.

1. Module d'Absences & Retards (attendance/models.py & Vues)
Modèle AbsenceRecord :

Lié à une CourseSession (la séance de l'EDT) et un StudentProfile.

Statut : PRESENT, LATE (Retard), ABSENT.

minutes_late (entier, optionnel).

justified (booléen) et justification_reason (texte).

Interface "Faire l'appel" pour le Professeur :

Sur la page d'accueil du prof, affiche une carte "Cours en cours / Prochain cours" (basée sur l'heure actuelle) avec un bouton "Faire l'appel".

L'interface d'appel doit ressembler à celle des notes (Excel-like) : la liste des élèves avec des boutons radio géants ou des raccourcis clavier pour marquer rapidement "Présent", "Absent" ou "Retard".

Interface "Vie Scolaire / Parents" :

Le parent voit les absences de son enfant sur son dashboard avec un bouton "Justifier" (qui envoie une justification à valider).

2. Module Messagerie Interne/Externe (messaging/models.py)
Nous voulons un système de tickets/conversations, similaire à l'interface Pronote.

Modèles :

Conversation : Sujet, participants (ManyToMany User).

Message : Auteur, contenu, date, lié à une Conversation.

Interface (/messaging/) :

Une boîte de réception de style "Webmail" (liste des conversations à gauche, contenu du message à droite).

Possibilité de créer une nouvelle conversation en choisissant les destinataires (ex: un parent cherche à écrire aux professeurs de son enfant).

Passerelle Email (Externe) :

Pour simuler la réception d'emails depuis l'extérieur (sans configurer un serveur SMTP complet pour le moment), crée un endpoint d'API sécurisé (/messaging/api/incoming_mail/) ou une commande de management (python manage.py fetch_emails).

Explique dans les commentaires (ou le README) comment relier cela plus tard à un webhook (ex: SendGrid/Mailgun Inbound Parse).

3. Seeder (seed_db.py)
Ajoute quelques absences non justifiées à eleve1 pour tester l'interface parent.

Crée une conversation de test entre parent1 et prof1.

4. Mise à jour du README.md
Mets à jour le README.md avec ces nouvelles fonctionnalités.

Explique brièvement la logique choisie pour les emails entrants.

Fournis l'ensemble du code (modèles, vues, templates) et les instructions de migration.
