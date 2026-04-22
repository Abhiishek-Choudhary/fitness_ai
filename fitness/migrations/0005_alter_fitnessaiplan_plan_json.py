from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fitness', '0004_fitnessaiplan'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fitnessaiplan',
            name='plan_json',
            field=models.JSONField(default=dict),
        ),
    ]
