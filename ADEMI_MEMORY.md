# Ademi Project Memory

Updated: 2026-09-07T17:09:59.188Z
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

Étape 5 : Emploi du Temps Universel & Saisie des Notes "Façon Excel"

Notre application doit convenir de l'école primaire jusqu'aux études supérieures. Nous allons maintenant implémenter l'emploi du temps (schedule) et optimiser drastiquement l'interface de saisie des notes pour les professeurs.

Voici les tâches à accomplir :

1. Module Emploi du Temps (schedule/models.py & Vues)
Modèles flexibles :

Room (Salle) : nom, capacité.

CourseSession (Séance de cours) : liée à une ClassGroup (ou plusieurs pour les TD/Amphis), un TeacherProfile, un Subject, une Room.

Champs de CourseSession : Jour de la semaine (Lundi à Samedi), Heure de début, Heure de fin (pour gérer aussi bien des cours de 55 min au collège que des amphis de 4h dans le supérieur).

Interface de l'Emploi du Temps (Tailwind CSS Grid) :

Crée une vue /schedule/ qui s'adapte au rôle :

L'élève voit l'emploi du temps de sa classe.

Le professeur voit son propre emploi du temps.

L'admin a des filtres pour chercher par classe, prof ou salle.

Le design doit afficher une grille hebdomadaire intuitive (lundi au samedi en colonnes, heures en lignes) avec des cartes colorées par matière pour chaque cours.

2. Optimisation "Excel-like" de la saisie des notes (academics/templates/)
Refonds complètement le template /academics/evaluations/<id>/entry/ pour qu'il soit le plus rapide possible à utiliser.

Comportement attendu (via JavaScript / Alpine.js) :

Un tableau minimaliste (Nom de l'élève, Note, Statut).

Navigation au clavier : Le professeur doit pouvoir taper une note, appuyer sur Entrée ou Tab pour passer instantanément à la ligne de l'élève suivant.

S'il tape "ABS" ou "DISP", cela change automatiquement le statut de l'élève.

Bouton "Sauvegarder tout" collant (sticky) en bas ou en haut de l'écran, ou une sauvegarde automatique en asynchrone (AJAX/Fetch) à chaque changement de case.

3. Seeder (seed_db.py)
Mets à jour la commande seed_db pour générer :

5 salles (Ex: A101, Labo SVT, Gymnase...).

Un emploi du temps complet et logique pour la classe de eleve1 et pour prof1 (au moins 15 heures de cours réparties dans la semaine).

4. Documentation (OBLIGATOIRE)
Crée ou mets à jour un fichier README.md à la racine du projet.

Ce README doit contenir :

Les commandes d'installation et de lancement.

La liste complète des comptes de test actuels (avec mots de passe).

L'architecture globale (rôle de chaque app).

L'explication du fonctionnement de l'emploi du temps et des évaluations.

Fournis l'ensemble du code, les instructions de migration, et le contenu du README.md.

## Conversation Context

[USER 2026-09-07T17:09:59.188Z]
Étape 5 : Emploi du Temps Universel & Saisie des Notes "Façon Excel"

Notre application doit convenir de l'école primaire jusqu'aux études supérieures. Nous allons maintenant implémenter l'emploi du temps (schedule) et optimiser drastiquement l'interface de saisie des notes pour les professeurs.

Voici les tâches à accomplir :

1. Module Emploi du Temps (schedule/models.py & Vues)
Modèles flexibles :

Room (Salle) : nom, capacité.

CourseSession (Séance de cours) : liée à une ClassGroup (ou plusieurs pour les TD/Amphis), un TeacherProfile, un Subject, une Room.

Champs de CourseSession : Jour de la semaine (Lundi à Samedi), Heure de début, Heure de fin (pour gérer aussi bien des cours de 55 min au collège que des amphis de 4h dans le supérieur).

Interface de l'Emploi du Temps (Tailwind CSS Grid) :

Crée une vue /schedule/ qui s'adapte au rôle :

L'élève voit l'emploi du temps de sa classe.

Le professeur voit son propre emploi du temps.

L'admin a des filtres pour chercher par classe, prof ou salle.

Le design doit afficher une grille hebdomadaire intuitive (lundi au samedi en colonnes, heures en lignes) avec des cartes colorées par matière pour chaque cours.

2. Optimisation "Excel-like" de la saisie des notes (academics/templates/)
Refonds complètement le template /academics/evaluations/<id>/entry/ pour qu'il soit le plus rapide possible à utiliser.

Comportement attendu (via JavaScript / Alpine.js) :

Un tableau minimaliste (Nom de l'élève, Note, Statut).

Navigation au clavier : Le professeur doit pouvoir taper une note, appuyer sur Entrée ou Tab pour passer instantanément à la ligne de l'élève suivant.

S'il tape "ABS" ou "DISP", cela change automatiquement le statut de l'élève.

Bouton "Sauvegarder tout" collant (sticky) en bas ou en haut de l'écran, ou une sauvegarde automatique en asynchrone (AJAX/Fetch) à chaque changement de case.

3. Seeder (seed_db.py)
Mets à jour la commande seed_db pour générer :

5 salles (Ex: A101, Labo SVT, Gymnase...).

Un emploi du temps complet et logique pour la classe de eleve1 et pour prof1 (au moins 15 heures de cours réparties dans la semaine).

4. Documentation (OBLIGATOIRE)
Crée ou mets à jour un fichier README.md à la racine du projet.

Ce README doit contenir :

Les commandes d'installation et de lancement.

La liste complète des comptes de test actuels (avec mots de passe).

L'architecture globale (rôle de chaque app).

L'explication du fonctionnement de l'emploi du temps et des évaluations.

Fournis l'ensemble du code, les instructions de migration, et le contenu du README.md.
