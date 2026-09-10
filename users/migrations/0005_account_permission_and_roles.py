from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0004_alter_user_groups"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("ADMIN", "Administrateur"),
                    ("TEACHER", "Professeur"),
                    ("STUDENT", "Élève"),
                    ("PARENT", "Parent"),
                    ("NURSE", "Infirmier / infirmière"),
                    ("SCHOOL_LIFE", "Vie scolaire"),
                    ("DIRECTOR", "Directeur / directrice"),
                    ("SECRETARY", "Secrétaire"),
                    ("ADMINISTRATION", "Administration"),
                ],
                db_index=True,
                default="STUDENT",
                max_length=20,
                verbose_name="rôle",
            ),
        ),
        migrations.AlterModelOptions(
            name="user",
            options={
                "ordering": ("last_name", "first_name"),
                "permissions": (("can_create_accounts", "Peut créer des comptes"),),
                "verbose_name": "utilisateur",
                "verbose_name_plural": "utilisateurs",
            },
        ),
    ]