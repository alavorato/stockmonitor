from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Stock",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("ticker", models.CharField(max_length=15, unique=True)),
                ("name", models.CharField(blank=True, max_length=100)),
                ("quantity", models.DecimalField(decimal_places=2, max_digits=12)),
                ("avg_price", models.DecimalField(decimal_places=4, max_digits=10)),
                ("min_profit_pct", models.DecimalField(decimal_places=2, default=5.0, max_digits=5)),
                ("max_profit_pct", models.DecimalField(decimal_places=2, default=10.0, max_digits=5)),
                ("active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Ativo",
                "verbose_name_plural": "Ativos",
                "ordering": ["ticker"],
            },
        ),
    ]
