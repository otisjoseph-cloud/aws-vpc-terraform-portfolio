"""Check a saved EC2 describe-route-tables response. No network or writes."""
import argparse
import ipaddress
import json
import sys
from collections import Counter
from pathlib import Path


def check_routes(data, vpc_id, nat_enabled=False):
    if not isinstance(data, dict) or not isinstance(data.get('RouteTables'), list):
        raise ValueError('Expected an object containing a RouteTables list')
    if data.get('NextToken'):
        raise ValueError('Incomplete paginated response: collect all pages first')
    errors, counts, seen = [], Counter(), set()
    for table in data['RouteTables']:
        if not isinstance(table, dict):
            raise ValueError('Each route table must be an object')
        if table.get('VpcId') != vpc_id:
            continue
        tags = table.get('Tags', [])
        if not isinstance(tags, list) or any(not isinstance(t, dict) for t in tags):
            raise ValueError('Tags must be a list of objects')
        if sum(t.get('Key') == 'Tier' for t in tags) > 1:
            raise ValueError('Duplicate Tier tags are ambiguous')
        tier = next((t.get('Value') for t in tags if t.get('Key') == 'Tier'), None)
        if tier not in {'public', 'application', 'database'}:
            # Terraform leaves the VPC's untagged main table unmanaged.
            continue
        table_id = table.get('RouteTableId')
        if not isinstance(table_id, str) or not table_id or table_id in seen:
            raise ValueError('Missing or duplicate managed RouteTableId')
        seen.add(table_id)
        counts[tier] += 1
        routes = table.get('Routes')
        if not isinstance(routes, list) or not routes:
            raise ValueError(f'{table_id}: missing Routes list')
        local_count, default_count = 0, 0
        for route in routes:
            if not isinstance(route, dict):
                raise ValueError(f'{table_id}: malformed route')
            destinations = [k for k in route if k.startswith('Destination')]
            if len(destinations) != 1:
                raise ValueError(f'{table_id}: expected exactly one route destination')
            destination = route.get('DestinationCidrBlock')
            if destinations == ['DestinationCidrBlock']:
                if not isinstance(destination, str):
                    raise ValueError(f'{table_id}: IPv4 destination must be a string')
                ipaddress.IPv4Network(destination)
            if route.get('State') != 'active':
                errors.append(f'{table_id}: route is not active')
            targets = [(k, v) for k, v in route.items()
                       if k.endswith('Id') and k not in {'RouteTableId'} and v]
            if any(not isinstance(v, str) for _, v in targets):
                raise ValueError(f'{table_id}: route targets must be strings')
            if destination == '10.0.0.0/16' and targets == [('GatewayId', 'local')]:
                local_count += 1
                continue
            if destination == '0.0.0.0/0':
                default_count += 1
                if tier == 'public' and len(targets) == 1 and targets[0][0] == 'GatewayId' and targets[0][1].startswith('igw-'):
                    continue
                if tier == 'application' and nat_enabled and len(targets) == 1 and targets[0][0] == 'NatGatewayId' and targets[0][1].startswith('nat-'):
                    continue
            errors.append(f'{table_id}: {tier} has unexpected non-local route')
        if local_count != 1:
            errors.append(f'{table_id}: expected exactly one VPC local route')
        expected_defaults = int(tier == 'public' or (tier == 'application' and nat_enabled))
        if default_count != expected_defaults:
            errors.append(f'{table_id}: expected {expected_defaults} default route(s), found {default_count}')
    for tier, expected in [('public', 1), ('application', 2), ('database', 2)]:
        if counts[tier] != expected:
            errors.append(f'{tier}: expected {expected} tagged tables, found {counts[tier]}')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot', type=Path)
    parser.add_argument('--vpc-id', required=True)
    parser.add_argument('--nat-enabled', action='store_true')
    args = parser.parse_args()
    try:
        with args.snapshot.open(encoding='utf-8-sig') as stream:
            errors = check_routes(json.load(stream), args.vpc_id, args.nat_enabled)
    except (OSError, ValueError, TypeError, AttributeError) as error:
        print(f'INPUT ERROR: {error}', file=sys.stderr)
        return 2
    for error in errors:
        print(f'FAIL: {error}')
    if not errors:
        print('PASS: five tagged route tables match the selected routing policy')
    return int(bool(errors))


if __name__ == '__main__':
    sys.exit(main())
