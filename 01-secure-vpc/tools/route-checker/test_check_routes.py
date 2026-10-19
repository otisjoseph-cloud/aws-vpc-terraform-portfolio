import copy
import json
import unittest
from pathlib import Path
from check_routes import check_routes

FIXTURES = Path(__file__).parent / 'fixtures'


class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.good = json.loads((FIXTURES / 'good.json').read_text())

    def test_default_policy(self):
        self.assertEqual([], check_routes(self.good, 'vpc-synthetic'))

    def test_bad_database_fixture(self):
        bad = json.loads((FIXTURES / 'bad-database-route.json').read_text())
        self.assertTrue(any('database has unexpected' in e for e in check_routes(bad, 'vpc-synthetic')))

    def test_missing_inventory_fails(self):
        self.assertTrue(check_routes({'RouteTables': []}, 'vpc-synthetic'))

    def test_wrong_vpc_fails(self):
        self.assertTrue(check_routes(self.good, 'vpc-wrong'))

    def test_blackhole_fails(self):
        self.good['RouteTables'][0]['Routes'][1]['State'] = 'blackhole'
        self.assertTrue(any('not active' in e for e in check_routes(self.good, 'vpc-synthetic')))

    def test_nat_requirement_change(self):
        self.assertTrue(check_routes(self.good, 'vpc-synthetic', True))
        for t in self.good['RouteTables']:
            if t['Tags'][0]['Value'] == 'application':
                t['Routes'].append({'DestinationCidrBlock': '0.0.0.0/0', 'NatGatewayId': 'nat-synthetic', 'State': 'active'})
        self.assertEqual([], check_routes(self.good, 'vpc-synthetic', True))
        self.assertTrue(check_routes(self.good, 'vpc-synthetic', False))

    def test_ipv6_bypass_fails(self):
        self.good['RouteTables'][-1]['Routes'].append({'DestinationIpv6CidrBlock': '::/0', 'GatewayId': 'igw-synthetic', 'State': 'active'})
        self.assertTrue(check_routes(self.good, 'vpc-synthetic'))

    def test_incomplete_input_errors(self):
        for data in [{}, {'RouteTables': [], 'NextToken': 'synthetic'}]:
            with self.assertRaises(ValueError):
                check_routes(data, 'vpc-synthetic')

    def test_duplicate_table_errors(self):
        self.good['RouteTables'].append(copy.deepcopy(self.good['RouteTables'][0]))
        with self.assertRaises(ValueError):
            check_routes(self.good, 'vpc-synthetic')


class InputAndCliTests(unittest.TestCase):
    def setUp(self):
        self.good = json.loads((FIXTURES / 'good.json').read_text())

    def test_conflicting_destinations_rejected(self):
        self.good['RouteTables'][-1]['Routes'][0]['DestinationIpv6CidrBlock'] = '::/0'
        with self.assertRaisesRegex(ValueError, 'exactly one route destination'):
            check_routes(self.good, 'vpc-synthetic')

    def test_duplicate_tier_rejected(self):
        self.good['RouteTables'][0]['Tags'].append({'Key': 'Tier', 'Value': 'database'})
        with self.assertRaisesRegex(ValueError, 'Duplicate Tier'):
            check_routes(self.good, 'vpc-synthetic')

    def test_malformed_tags_rejected(self):
        self.good['RouteTables'][0]['Tags'] = 'public'
        with self.assertRaisesRegex(ValueError, 'Tags must'):
            check_routes(self.good, 'vpc-synthetic')

    def test_invalid_cidr_rejected(self):
        self.good['RouteTables'][0]['Routes'][0]['DestinationCidrBlock'] = 'not-a-cidr'
        with self.assertRaises(ValueError):
            check_routes(self.good, 'vpc-synthetic')

    def test_nonstring_target_rejected(self):
        self.good['RouteTables'][0]['Routes'][1]['GatewayId'] = 42
        with self.assertRaisesRegex(ValueError, 'targets must be strings'):
            check_routes(self.good, 'vpc-synthetic')

    def test_wrong_gateway_fails(self):
        self.good['RouteTables'][0]['Routes'][1]['GatewayId'] = 'nat-synthetic'
        self.assertTrue(check_routes(self.good, 'vpc-synthetic'))

    def test_missing_local_route_fails(self):
        self.good['RouteTables'][0]['Routes'].pop(0)
        self.assertTrue(any('local route' in e for e in check_routes(self.good, 'vpc-synthetic')))

    def test_more_specific_database_route_fails(self):
        self.good['RouteTables'][-1]['Routes'].append({
            'DestinationCidrBlock': '192.0.2.0/24', 'GatewayId': 'igw-synthetic', 'State': 'active'})
        self.assertTrue(check_routes(self.good, 'vpc-synthetic'))

    def test_prefix_list_route_fails(self):
        self.good['RouteTables'][-1]['Routes'].append({
            'DestinationPrefixListId': 'pl-synthetic', 'GatewayId': 'vpce-synthetic', 'State': 'active'})
        self.assertTrue(check_routes(self.good, 'vpc-synthetic'))

    def test_cli_exit_codes_and_no_fixture_mutation(self):
        import subprocess
        import sys
        script = Path(__file__).with_name('check_routes.py')
        for filename, code, message in [
            ('good.json', 0, 'PASS:'),
            ('bad-database-route.json', 1, 'database has unexpected non-local route'),
            ('missing.json', 2, 'INPUT ERROR:'),
        ]:
            with self.subTest(filename=filename):
                path = FIXTURES / filename
                before = path.read_bytes() if path.exists() else None
                result = subprocess.run([sys.executable, str(script), str(path), '--vpc-id', 'vpc-synthetic'],
                                        text=True, capture_output=True, check=False)
                self.assertEqual(code, result.returncode)
                self.assertIn(message, result.stdout + result.stderr)
                self.assertEqual(before, path.read_bytes() if path.exists() else None)

    def test_bom_and_invalid_json_cli(self):
        import subprocess
        import sys
        import tempfile
        script = Path(__file__).with_name('check_routes.py')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'snapshot.json'
            for content, code in [('\ufeff' + json.dumps(self.good), 0), ('{invalid', 2)]:
                path.write_text(content, encoding='utf-8')
                result = subprocess.run([sys.executable, str(script), str(path), '--vpc-id', 'vpc-synthetic'],
                                        text=True, capture_output=True, check=False)
                self.assertEqual(code, result.returncode)


if __name__ == '__main__':
    unittest.main()
