# Generated by Django 4.2.11 on 2024-06-12 14:43

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("posthog", "0429_alter_datawarehousetable_format"),
    ]

    operations = [
        migrations.AddField(
            model_name="batchexport",
            name="model",
            field=models.CharField(
                blank=True,
                choices=[("events", "Events"), ("persons", "Persons")],
                default="events",
                help_text="Which model this BatchExport is exporting.",
                max_length=64,
                null=True,
            ),
        ),
    ]
