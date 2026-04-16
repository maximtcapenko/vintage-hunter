import json
from functools import cached_property
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from PIL import Image, ImageOps
from pgvector.django import HnswIndex, VectorField

from commons.models import Base

from .managers import InstrumentManager


class Category(Base):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name
    
class Brand(Base):
    name = models.CharField(max_length=100, unique=True)
    origin_country = models.CharField(max_length=100, blank=True)
    history = models.TextField(blank=True, help_text='Brief history for LLM context')

    def __str__(self):
        return self.name

class Instrument(Base):
    CONDITION_CHOICES = [
        ('mint', 'Mint (Like New)'),
        ('excellent', 'Excellent'),
        ('very_good', 'Very Good'),
        ('good', 'Good (Player Grade)'),
        ('fair', 'Fair (Project)'),
    ]
    CONDITION_LABELS = {
        'mint': _('Mint (Like New)'),
        'excellent': _('Excellent'),
        'very_good': _('Very Good'),
        'good': _('Good (Player Grade)'),
        'fair': _('Fair (Project)'),
    }

    objects = InstrumentManager()

    title = models.CharField(max_length=255)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name='instruments')    
    brand = models.ForeignKey(
        Brand, on_delete=models.PROTECT, related_name='instruments')
    year = models.PositiveIntegerField(
        db_index=True
    )
    serial_number = models.CharField(max_length=100, blank=True)
    
    condition = models.CharField(max_length=50, choices=CONDITION_CHOICES)
    is_original = models.BooleanField(default=True, help_text='Are all parts original?')
    has_repairs = models.BooleanField(default=False)
    is_concert_ready = models.BooleanField(default=False)

    specifications = models.JSONField(default=dict, blank=True)
    description = models.TextField()

    price = models.DecimalField(max_digits=12, decimal_places=2)
    is_auction = models.BooleanField(default=False)
    is_sold = models.BooleanField(default=False)
    auction_end_date = models.DateTimeField(null=True, blank=True)


    text_embedding = VectorField(dimensions=768, null=True, blank=True)
    image_embedding = VectorField(dimensions=512, null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True, null=True)

    @cached_property
    def primary_image(self):
        return self.images.filter(is_primary=True).first()
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            HnswIndex(
                name='text_vector_idx',
                fields=['text_embedding'],
                m=16,
                ef_construction=64,
                opclasses=('vector_cosine_ops',)
            ),
            HnswIndex(
                name='image_vector_idx',
                fields=['image_embedding'],
                m=16,
                ef_construction=64,
                opclasses=('vector_cosine_ops',)
            ),
        ]

    def __str__(self):
        return f'{self.year} {self.brand.name} {self.title}'

    @property
    def condition_label(self):
        return self.CONDITION_LABELS.get(self.condition, self.condition)
    
    def get_full_description_for_ai(self):        
        return (
            f'Instrument: {self.year} {self.brand.name} {self.title}. '
            f'Category: {self.category.name}. '
            f'Condition: {self.condition}. '
            f'Technical specs: {json.dumps(self.specifications)}. '
            f'Additional info: {self.description}'
        ).strip()

    def update_embeddings(self, force_image=False):
        from .services import EmbeddingService, ImageVectorService
        
        text_data = self.get_full_description_for_ai()
        self.text_embedding = EmbeddingService.encode(text_data)
        
        primary_img = self.images.filter(is_primary=True).first()
        if primary_img and (self.image_embedding is None or force_image):
            self.image_embedding = ImageVectorService.encode(primary_img.image)
            
        self.save(update_fields=['text_embedding', 'image_embedding'])


class InstrumentImage(Base):
    instrument = models.ForeignKey(
        Instrument, 
        related_name='images', 
        on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to='instruments/%Y/%m/')
    is_primary = models.BooleanField(default=False)
    alt_text = models.CharField(max_length=255, blank=True)

    def save(self, *args, **kwargs):
        if self.image:
            img = Image.open(self.image)
            img = ImageOps.exif_transpose(img)

            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            buffer = BytesIO()
            img.save(buffer, format="JPEG", quality=85, optimize=True, progressive=True)

            self.image.save(self.image.name, ContentFile(buffer.getvalue()), save=False)

        super().save(*args, **kwargs)
    
    def __str__(self):
        return f'Image for {self.instrument.title}'
