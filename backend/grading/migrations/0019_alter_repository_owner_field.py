# Generated manually to fix repository owner field

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("grading", "0018_repository_unique_together"),
    ]

    operations = [
        # Only alter the field if it exists (it should exist from 0004)
        migrations.AlterField(
            model_name="repository",
            name="owner",
            field=models.ForeignKey(
                blank=True,
                null=True,
                help_text="仓库所有者",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="repositories",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
