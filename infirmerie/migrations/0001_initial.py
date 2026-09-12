import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("users", "0006_teacherprofile_class_groups"),
    ]

    operations = [
        migrations.CreateModel(
            name="InfirmerieVisit",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("arrival_time", models.DateTimeField(default=django.utils.timezone.now, verbose_name="Arrivée")),
                ("departure_time", models.DateTimeField(blank=True, null=True, verbose_name="Sortie")),
                ("reason", models.CharField(choices=[("MALAISE", "Malaise"), ("BLESSURE", "Blessure"), ("MAUX_TETE", "Maux de tête"), ("MAUX_VENTRE", "Maux de ventre"), ("TRAUMATISME", "Traumatisme"), ("AUTRE", "Autre")], default="AUTRE", max_length=20, verbose_name="Motif")),
                ("reason_detail", models.CharField(blank=True, max_length=255, verbose_name="Précision")),
                ("care_given", models.TextField(blank=True, max_length=1000, verbose_name="Soins prodigués")),
                ("outcome", models.CharField(choices=[("EN_COURS", "Prise en charge en cours"), ("RETOUR_CLASSE", "Retour en cours"), ("RENVOYE_DOMICILE", "Renvoyé au domicile"), ("HOPITAL", "Transféré vers un hôpital")], default="EN_COURS", max_length=20, verbose_name="Suite donnée")),
                ("parent_notified", models.BooleanField(default=False, verbose_name="Parents prévenus")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Créé le")),
                ("recorded_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="infirmerie_visits_recorded", to="users.user", verbose_name="Saisi par")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="infirmerie_visits", to="users.studentprofile", verbose_name="Élève")),
            ],
            options={
                "verbose_name": "Passage infirmerie",
                "verbose_name_plural": "Passages infirmerie",
                "ordering": ("-arrival_time",),
            },
        ),
    ]