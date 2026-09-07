from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('messaging', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='kind',
            field=models.CharField(
                choices=[('MAIL', 'Mail'), ('CHAT', 'Chat')],
                db_index=True,
                default='MAIL',
                max_length=4,
            ),
        ),
    ]
