from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("academics", "0003_initial"),
        ("users", "0005_account_permission_and_roles"),
    ]

    operations = [
        migrations.AddField(
            model_name="teacherprofile",
            name="class_groups",
            field=models.ManyToManyField(
                blank=True,
                related_name="teachers",
                to="academics.classgroup",
                verbose_name="classes suivies",
            ),
        ),
    ]