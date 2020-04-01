from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SynoSession',
            fields=[
                ('account', models.CharField(max_length=50, primary_key=True)),
                ('sid', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='LibrarySection',
            fields=[
                ('uuid', models.CharField(max_length=32, primary_key=True)),
                ('title', models.CharField(max_length=50)),
                ('changed_at', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Movie',
            fields=[
                ('guid', models.CharField(max_length=255, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('year', models.IntegerField()),
                ('thumb', models.CharField(max_length=255)),
                ('added_at', models.DateTimeField()),
                ('updated_at', models.DateTimeField()),
                ('section', models.ForeignKey('LibrarySection', on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='Media',
            fields=[
                ('id', models.IntegerField(primary_key=True)),
                ('movie', models.ForeignKey('Movie', on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='MediaPart',
            fields=[
                ('id', models.IntegerField(primary_key=True)),
                ('path', models.CharField(max_length=255)),
                ('best_path', models.CharField(max_length=255)),
                ('media', models.ForeignKey('Media', on_delete=models.CASCADE)),
            ],
        ),
    ]
