# Generated by Django 4.0.5 on 2022-07-14 22:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('tom_targets', '0019_auto_20210811_0018'),
    ]

    operations = [
        migrations.CreateModel(
            name='TargetClassification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.TextField(blank=True, default='')),
                ('level', models.TextField(blank=True, default='')),
                ('classification', models.TextField(blank=True, default='')),
                ('probability', models.FloatField(blank=True, null=True)),
                ('mjd', models.FloatField(blank=True, null=True)),
                ('target', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tom_targets.target')),
            ],
        ),
    ]
