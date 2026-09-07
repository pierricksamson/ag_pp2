"""Partie 2 de l'initial academics : Evaluation et Grade (dépendent de users)."""

import django.core.validators
import django.db.models.deletion
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0002_initial'),
        ('users', '0003_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Evaluation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=120, verbose_name='titre')),
                ('date', models.DateField(verbose_name="date de l'épreuve")),
                ('coefficient', models.DecimalField(decimal_places=2, default=Decimal('1.00'), max_digits=4, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))], verbose_name='coefficient')),
                ('scale_max', models.DecimalField(decimal_places=2, default=Decimal('20.00'), max_digits=5, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))], verbose_name='note maximale')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='créée le')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='modifiée le')),
                ('class_group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evaluations', to='academics.classgroup', verbose_name='classe')),
                ('teacher', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='evaluations', to='users.teacherprofile', verbose_name='professeur')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='evaluations', to='academics.subject', verbose_name='matière')),
                ('term', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evaluations', to='academics.term', verbose_name='trimestre')),
            ],
            options={
                'verbose_name': 'évaluation',
                'verbose_name_plural': 'évaluations',
                'ordering': ('-date', '-id'),
            },
        ),
        migrations.CreateModel(
            name='Grade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.DecimalField(blank=True, decimal_places=2, help_text="Note sur la valeur maximale de l'évaluation.", max_digits=5, null=True, verbose_name='note')),
                ('status', models.CharField(choices=[('PRESENT', 'Présent'), ('ABSENT', 'Absent'), ('DISPENSED', 'Dispensé'), ('NOT_SUBMITTED', 'Non rendu')], default='PRESENT', max_length=15, verbose_name='statut')),
                ('comment', models.CharField(blank=True, max_length=255, verbose_name='appréciation / commentaire')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='créée le')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='modifiée le')),
                ('evaluation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='grades', to='academics.evaluation', verbose_name='évaluation')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='grades', to='users.studentprofile', verbose_name='élève')),
            ],
            options={
                'verbose_name': 'note',
                'verbose_name_plural': 'notes',
                'ordering': ('student__user__last_name', 'student__user__first_name'),
                'unique_together': {('evaluation', 'student')},
            },
        ),
    ]