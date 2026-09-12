import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vie_scolaire", "0002_observation"),
        ("attendance", "0003_initial_justification"),
    ]

    operations = [
        migrations.AddField(
            model_name="retard",
            name="source",
            field=models.CharField(choices=[("MANUEL", "Déclaré manuellement"), ("APPEL", "Généré depuis l'appel")], default="MANUEL", max_length=10, verbose_name="Origine"),
        ),
        migrations.AddField(
            model_name="retard",
            name="attendance_record",
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="retard", to="attendance.attendancerecord", verbose_name="Séance d'origine (appel)"),
        ),
    ]