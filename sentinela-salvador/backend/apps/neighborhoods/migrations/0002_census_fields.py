from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('neighborhoods', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='neighborhood',
            name='elevation_mean',
            field=models.FloatField(default=30.0),
        ),
        migrations.AddField(
            model_name='neighborhood',
            name='pop_density',
            field=models.FloatField(default=6000.0),
        ),
        migrations.AddField(
            model_name='neighborhood',
            name='pct_sem_esgoto',
            field=models.FloatField(default=30.0),
        ),
    ]
