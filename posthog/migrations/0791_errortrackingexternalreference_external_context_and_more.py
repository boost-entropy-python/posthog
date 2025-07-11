# Generated by Django 4.2.22 on 2025-07-11 09:46

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("posthog", "0790_alter_integration_kind"),
    ]

    operations = [
        migrations.AddField(
            model_name="errortrackingexternalreference",
            name="external_context",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="errortrackingexternalreference",
            name="external_id",
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name="errortrackingexternalreference",
            name="provider",
            field=models.TextField(null=True),
        ),
    ]
