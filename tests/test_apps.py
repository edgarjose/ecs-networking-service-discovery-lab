import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

import requests

ROOT = Path(__file__).resolve().parents[1]


def load_app(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'apps' / name / 'app.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.app.config['TESTING'] = True
    return module


orders = load_app('orders')
payments = load_app('payments')


class ApplicationTests(unittest.TestCase):
    def test_orders_health(self):
        response = orders.app.test_client().get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['service'], 'orders')

    def test_payments_health(self):
        self.assertEqual(payments.app.test_client().get('/health').status_code, 200)

    def test_payment_identifies_responder(self):
        with patch.object(payments.socket, 'gethostname', return_value='task-test'), patch.object(payments.socket, 'gethostbyname', return_value='10.20.11.5'):
            response = payments.app.test_client().get('/payment')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['ip'], '10.20.11.5')
        self.assertEqual(response.json['status'], 'approved')

    def test_checkout_calls_configured_endpoint_with_timeout(self):
        downstream = Mock()
        downstream.json.return_value = {'service': 'payments', 'status': 'approved'}
        with patch.object(orders, 'PAYMENTS_URL', 'http://payments.lab.internal:5000/'), patch.object(orders.requests, 'get', return_value=downstream) as get:
            response = orders.app.test_client().get('/checkout')
        get.assert_called_once_with('http://payments.lab.internal:5000/payment', timeout=5)
        downstream.raise_for_status.assert_called_once()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'completed')

    def test_downstream_timeout_is_a_gateway_error(self):
        with patch.object(orders.requests, 'get', side_effect=requests.Timeout('internal detail')):
            response = orders.app.test_client().get('/checkout')
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json['error'], 'Payment service unavailable')
        self.assertNotIn('internal detail', response.get_data(as_text=True))


if __name__ == '__main__':
    unittest.main()
