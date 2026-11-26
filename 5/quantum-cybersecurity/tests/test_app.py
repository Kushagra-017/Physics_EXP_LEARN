import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
import database
from app import app


class AppTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        database.DB_PATH = os.path.join(self.temp.name, 'test.sqlite3')
        self.client = app.test_client()

    def tearDown(self):
        self.temp.cleanup()

    def test_shor_and_history(self):
        response = self.client.post('/api/simulate/shor', json={'number': 15})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['factors'], [3, 5])
        self.assertEqual(response.json['period'], 4)
        self.assertEqual(len(self.client.get('/api/history').json['simulations']), 1)

    def test_prime_even_and_input_validation(self):
        self.assertEqual(self.client.post('/api/simulate/shor', json={'number': 13}).json['status'], 'prime')
        self.assertEqual(self.client.post('/api/simulate/shor', json={'number': 12}).json['factors'], [2, 6])
        for value in [True, 1000, '15', -1]:
            self.assertEqual(self.client.post('/api/simulate/shor', json={'number': value}).status_code, 400)
        self.assertEqual(self.client.post('/api/history', json={'input_number':15, 'factors':[3, 7]}).status_code, 400)

    def test_rsa_round_trip(self):
        encrypted = self.client.post('/api/encrypt/rsa', json={'message': 'Hello 🌍'}).json
        response = self.client.post('/api/decrypt/rsa', json={'ciphertext': encrypted['ciphertext'], 'private_key': encrypted['private_key']})
        self.assertEqual(response.json['message'], 'Hello 🌍')
        self.assertEqual(self.client.post('/api/decrypt/rsa', json={'ciphertext': [999999], 'private_key': encrypted['private_key']}).status_code, 400)

    def test_headers_and_static(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn("default-src 'self'", response.headers['Content-Security-Policy'])
        self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')


if __name__ == '__main__':
    unittest.main()
