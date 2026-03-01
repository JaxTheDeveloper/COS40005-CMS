from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_remove_formsubmission_submitted_at_and_more'),
        ('academic', '0006_intake_and_offering_intake'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='target_all_students',
            field=models.BooleanField(default=False, help_text='If set, event is sent to all students regardless of other targets'),
        ),
        migrations.AddField(
            model_name='event',
            name='target_students',
            field=models.ManyToManyField(blank=True, related_name='targeted_events', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='event',
            name='target_offerings',
            field=models.ManyToManyField(blank=True, related_name='targeted_events', to='academic.SemesterOffering'),
        ),
        migrations.AddField(
            model_name='event',
            name='target_intakes',
            field=models.ManyToManyField(blank=True, related_name='targeted_events', to='academic.Intake'),
        ),
    ]
