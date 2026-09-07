"""Partie 2 de l'initial users : StudentProfile et TeacherProfile (dépendent de academics)."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_initial'),
        ('academics', '0002_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudentProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_number', models.CharField(max_length=20, unique=True, verbose_name='numéro étudiant')),
                ('birth_date', models.DateField(blank=True, null=True, verbose_name='date de naissance')),
                ('class_group', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='students', to='academics.classgroup', verbose_name='classe')),
                ('parents', models.ManyToManyField(blank=True, related_name='children', to='users.parentprofile', verbose_name='parents')),
                ('user', models.OneToOneField(limit_choices_to={'role': 'STUDENT'}, on_delete=django.db.models.deletion.CASCADE, related_name='student_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'profil élève',
                'verbose_name_plural': 'profils élèves',
                'ordering': ('user__last_name', 'user__first_name'),
            },
        ),
        migrations.CreateModel(
            name='TeacherProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('employee_number', models.CharField(blank=True, max_length=20, null=True, unique=True, verbose_name='matricule')),
                ('hire_date', models.DateField(blank=True, null=True, verbose_name="date d'embauche")),
                ('subjects', models.ManyToManyField(blank=True, related_name='teachers', to='academics.subject', verbose_name='matières enseignées')),
                ('user', models.OneToOneField(limit_choices_to={'role': 'TEACHER'}, on_delete=django.db.models.deletion.CASCADE, related_name='teacher_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'profil professeur',
                'verbose_name_plural': 'profils professeurs',
            },
        ),
    ]