from datetime import datetime

from django.db import migrations, models
from pytz import utc


class Migration(migrations.Migration):
    dependencies = [
        ('movies', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='SynoSession',
            name='timestamp',
            field=models.DateTimeField(auto_now=True, default=datetime.min.replace(tzinfo=utc)),
        )
    ]
