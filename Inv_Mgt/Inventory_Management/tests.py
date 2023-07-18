from django.test import TestCase
from .models import MyModel

class MyModelTest(TestCase):
    def test_create(self):
        instance = MyModel.objects.create(name="Test")
        self.assertEqual(instance.name, "Test")
