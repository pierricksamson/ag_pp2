import django.core.validators
import django.db.models.deletion
import drive.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('academics', '0003_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='StorageQuota',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('ADMIN', 'Administrateur'), ('TEACHER', 'Professeur'), ('STUDENT', 'Élève'), ('PARENT', 'Parent'), ('NURSE', 'Infirmier / infirmière'), ('SCHOOL_LIFE', 'Vie scolaire'), ('DIRECTOR', 'Directeur / directrice'), ('SECRETARY', 'Secrétaire'), ('ADMINISTRATION', 'Administration')], max_length=20, unique=True, verbose_name='rôle')),
                ('max_mb', models.PositiveIntegerField(verbose_name='quota (Mo)')),
            ],
            options={
                'verbose_name': 'quota de stockage',
                'verbose_name_plural': 'quotas de stockage',
                'ordering': ('role',),
            },
        ),
        migrations.CreateModel(
            name='DriveFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to=drive.models._user_drive_path, validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['pdf'])], verbose_name='fichier')),
                ('original_name', models.CharField(max_length=255, verbose_name='nom original')),
                ('size_bytes', models.PositiveBigIntegerField(default=0, verbose_name='taille (octets)')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True, verbose_name='déposé le')),
                ('class_group', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='drive_files', to='academics.classgroup', verbose_name='classe (si partagé)')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='drive_files', to=settings.AUTH_USER_MODEL, verbose_name='propriétaire')),
            ],
            options={
                'verbose_name': 'fichier',
                'verbose_name_plural': 'fichiers',
                'ordering': ('-uploaded_at',),
            },
        ),
    ]