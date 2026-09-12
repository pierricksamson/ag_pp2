import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vie_scolaire", "0001_initial"),
        ("academics", "0002_initial"),
        ("users", "0006_teacherprofile_class_groups"),
    ]

    operations = [
        migrations.CreateModel(
            name="Observation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("type", models.CharField(choices=[("ENCOURAGEMENT", "Encouragement"), ("AVERTISSEMENT_TRAVAIL", "Avertissement travail"), ("AVERTISSEMENT_CONDUITE", "Avertissement conduite"), ("PUNITION", "Punition"), ("SANCTION", "Sanction"), ("NOTE", "Observation / note libre")], db_index=True, default="NOTE", max_length=30, verbose_name="Type")),
                ("title", models.CharField(blank=True, max_length=120, verbose_name="Titre")),
                ("description", models.TextField(blank=True, max_length=1000, verbose_name="Description")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Créée le")),
                ("author", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="observations_written", to="users.user", verbose_name="Rédigé par")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="observations", to="users.studentprofile", verbose_name="Élève")),
                ("subject", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="observations", to="academics.subject", verbose_name="Matière concernée")),
            ],
            options={
                "verbose_name": "Observation",
                "verbose_name_plural": "Observations",
                "ordering": ("-created_at",),
            },
        ),
    ]