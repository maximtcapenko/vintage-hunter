import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0006_instrument_is_draft_instrument_is_new'),
        ('users', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='InstrumentFinder',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('name', models.CharField(max_length=100)),
                ('availability', models.CharField(choices=[('all', 'All'), ('buy_it_now', 'Buy It Now Only'), ('auction', 'Auction Only')], default='all', max_length=20)),
                ('vector_text_prompt', models.TextField(blank=True)),
                ('vector_image_prompt', models.ImageField(blank=True, null=True, upload_to='finders/%Y/%m/')),
                ('frequency_minutes', models.PositiveIntegerField(default=60)),
                ('max_results', models.PositiveIntegerField(default=10)),
                ('is_active', models.BooleanField(default=True)),
                ('last_run_at', models.DateTimeField(blank=True, null=True)),
                ('brand', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='finders', to='catalog.brand')),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='finders', to='catalog.category')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='finders', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
                'abstract': False,
            },
        ),
    ]
