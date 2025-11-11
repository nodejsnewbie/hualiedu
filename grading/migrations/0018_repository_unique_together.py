# Generated manually to set unique_together on Repository

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("grading", "0017_add_homework_model"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="repository",
            unique_together={("owner", "name")},
        ),
    ]
