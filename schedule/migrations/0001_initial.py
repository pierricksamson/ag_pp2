# Initial migration for the new CourseSession model (start_time/end_time, M2M classes).

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('academics', '0001_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=60, unique=True, verbose_name='nom')),
                ('capacity', models.PositiveSmallIntegerField(default=30, verbose_name='capacité')),
                ('location', models.CharField(blank=True, help_text='Indication libre, ex : « Bâtiment A, 1er étage ».', max_length=120, verbose_name='bâtiment / étage')),
            ],
            options={
                'verbose_name': 'salle',
                'verbose_name_plural': 'salles',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='CourseSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, help_text="Optionnel : ex « CM1+CM2 », « Amphi L1 Info ». Laisser vide pour utiliser la matière.", max_length=120, verbose_name='intitulé')),
                ('day', models.CharField(choices=[('MON', 'Lundi'), ('TUE', 'Mardi'), ('WED', 'Mercredi'), ('THU', 'Jeudi'), ('FRI', 'Vendredi'), ('SAT', 'Samedi')], max_length=3, verbose_name='jour')),
                ('start_time', models.TimeField(verbose_name='heure de début')),
                ('end_time', models.TimeField(verbose_name='heure de fin')),
                ('color', models.CharField(blank=True, help_text='Classe Tailwind « bg-* » optionnelle pour la carte.', max_length=20, verbose_name='couleur')),
                ('class_groups', models.ManyToManyField(help_text='Une ou plusieurs classes (CMI, TD regroupés, amphi partagé…).', related_name='sessions', to='academics.classgroup', verbose_name='classes')),
                ('room', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sessions', to='schedule.room', verbose_name='salle')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='academics.subject', verbose_name='matière')),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='users.teacherprofile', verbose_name='professeur')),
            ],
            options={
                'verbose_name': 'séance',
                'verbose_name_plural': 'séances',
                'ordering': ('day', 'start_time', 'subject__name'),
            },
        ),
        migrations.AddIndex(
            model_name='coursesession',
            index=models.Index(fields=['day', 'start_time'], name='schedule_co_day_8c4841_idx'),
        ),
    ]