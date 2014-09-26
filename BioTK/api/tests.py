from django.test import TestCase, Client

class MatrixTest(TestCase):
    def test_get_sample(self):
        uri = "/api/matrix/9606/sample/GSM102136/1/"
        c = Client()
        response = c.get(uri)
        assert(response.status_code == 200)
