from django.test import TestCase
from django.urls import reverse


class CoreViewsTestCase(TestCase):
    def test_index_view_status_code(self):
        """Verifica se a página inicial retorna o status code 200."""
        url = reverse("core:index")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
