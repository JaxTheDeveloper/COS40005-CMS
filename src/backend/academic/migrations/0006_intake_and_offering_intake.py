from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    initial = False

    dependencies = [
        ('academic', '0005_courseunit'),
    ]

    operations = [
        migrations.CreateModel(
            name='Intake',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('semester', models.CharField(choices=[('S1', 'Spring'), ('S2', 'Fall'), ('S3', 'Third'), ('SS', 'Summer'), ('WS', 'Winter')], max_length=2)),
                ('year', models.IntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, blank=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True, blank=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='academic_intake_created', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='academic_intake_updated', to=settings.AUTH_USER_MODEL)),
                ('deleted_at', models.DateTimeField(null=True, blank=True)),
                ('is_deleted', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['-year', 'semester'],
            },
        ),
        migrations.AddField(
            model_name='semesteroffering',
            name='intake',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='offerings', to='academic.intake'),
        ),
        migrations.AlterUniqueTogether(
            name='intake',
            unique_together={('semester', 'year')},
        ),
    ]
