from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("stocks", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="stock",
            name="quantity",
            field=models.PositiveIntegerField(),
        ),
    ]
