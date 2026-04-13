from functools import cached_property

from django.db import models
from django.contrib.auth.models import User
from commons.models import Base
from catalog.models import Instrument

class Collection(Base):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collections')
    name = models.CharField(max_length=32)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    instruments = models.ManyToManyField(Instrument, related_name='in_collections', blank=True)

    class Meta(Base.Meta):
        unique_together = ('user', 'name')
        verbose_name = 'Collection'
        verbose_name_plural = 'Collections'

    def __str__(self):
        return f"{self.user.username}'s {self.name}"

    def save(self, *args, **kwargs):
        if self.is_default:
            # Ensure only one default collection per user
            Collection.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

def get_user_user_collections_count(self):
    if not self.is_authenticated:
        return 0
    
    return self.collections.count()

user_collections_count_property = cached_property(get_user_user_collections_count)
User.add_to_class('collections_count', user_collections_count_property)
user_collections_count_property.__set_name__(User, 'collections_count')

