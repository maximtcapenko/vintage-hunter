from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import InstrumentFinder
from catalog.models import Brand, Category

class InstrumentFinderTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client = Client()
        self.client.login(username='testuser', password='password')
        self.brand = Brand.objects.create(name='Fender')
        self.category = Category.objects.create(name='Electric Guitar')

    def test_finder_creation(self):
        url = reverse('users:finder_create')
        data = {
            'name': 'Test Finder',
            'brand': self.brand.id,
            'category': self.category.id,
            'availability': 'all',
            'frequency_minutes': 60,
            'max_results': 10,
            'is_active': True,
            'vector_text_prompt': 'Vintage Stratocaster'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(InstrumentFinder.objects.count(), 1)
        finder = InstrumentFinder.objects.first()
        self.assertEqual(finder.name, 'Test Finder')
        self.assertEqual(finder.user, self.user)

    def test_finder_limit(self):
        for i in range(5):
            InstrumentFinder.objects.create(
                user=self.user,
                name=f'Finder {i}',
                availability='all',
                frequency_minutes=60,
                max_results=10
            )

        url = reverse('users:finder_create')
        data = {
            'name': '6th Finder',
            'availability': 'all',
            'frequency_minutes': 60,
            'max_results': 10,
            'is_active': True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'You can only have up to 5 finder configurations.')
        self.assertEqual(InstrumentFinder.objects.count(), 5)

    def test_frequency_limit(self):
        url = reverse('users:finder_create')
        data = {
            'name': 'Fast Finder',
            'availability': 'all',
            'frequency_minutes': 5,
            'max_results': 10,
            'is_active': True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Minimum frequency is 10 minutes.')

    def test_max_results_limit(self):
        url = reverse('users:finder_create')
        data = {
            'name': 'Greedy Finder',
            'availability': 'all',
            'frequency_minutes': 60,
            'max_results': 11,
            'is_active': True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Maximum results is 10.')
