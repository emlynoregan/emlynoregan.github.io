"""Explicit, guarded migration of the root hostname to an existing edge."""

import argparse
import copy
import hashlib
import http.client
import json
from pathlib import Path
import socket

import boto3
from botocore.config import Config

ACCOUNT = '214770884410'
DISTRIBUTION = 'E7XLBZDR5GVHB'
ZONE = 'Z01363303HJW7MS0Z4BB4'
DOMAIN = 'd1yyu588p4ns2m.cloudfront.net'
FUNCTION = 'emlynoregan-root-to-everything'
DESTINATION = 'https://everything.emlynoregan.com/guide'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path, value):
    path.write_text(json.dumps(value, indent=2, default=str), encoding='utf-8')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def root_record(dns):
    rows = dns.list_resource_record_sets(
        HostedZoneId=ZONE, StartRecordName='emlynoregan.com.',
        StartRecordType='A', MaxItems='1',
    )['ResourceRecordSets']
    assert rows and rows[0]['Name'] == 'emlynoregan.com.' and rows[0]['Type'] == 'A'
    return rows[0]


def direct_proof():
    result = []
    for secure, path in [(True, '/'), (False, '/content/old-page?old=1')]:
        port = 443 if secure else 80
        connection = (http.client.HTTPSConnection if secure else http.client.HTTPConnection)(
            'emlynoregan.com', port, timeout=20,
        )
        # Keep the original Host header and TLS SNI, but connect to the inspected edge.
        connection._create_connection = lambda address, timeout, source_address=None: socket.create_connection(
            (DOMAIN, port), timeout, source_address,
        )
        connection.request('HEAD', path)
        response = connection.getresponse()
        row = {'scheme': 'https' if secure else 'http', 'path': path,
               'status': response.status, 'location': response.getheader('Location')}
        response.read()
        connection.close()
        assert row['status'] == 301 and row['location'] == DESTINATION, row
        result.append(row)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['edge', 'status', 'dns', 'rollback-dns'])
    parser.add_argument('--state-dir', required=True, type=Path)
    args = parser.parse_args()
    state = args.state_dir.resolve()
    assert state.is_dir()
    session = boto3.Session(profile_name='legacy-existing', region_name='us-east-1')
    config = Config(retries={'total_max_attempts': 1}, connect_timeout=5, read_timeout=30)
    identity = session.client('sts', config=config).get_caller_identity()
    assert identity['Account'] == ACCOUNT
    cf = session.client('cloudfront', config=config)
    dns = session.client('route53', config=config)
    current = cf.get_distribution(Id=DISTRIBUTION)
    actual = current['Distribution']['DistributionConfig']
    before = read(state / 'distribution-before.json')
    inventory = read(state / 'inventory.json')
    old_record = next(r for r in inventory['records'] if r['Name'] == 'emlynoregan.com.' and r['Type'] == 'A')
    assert actual['Aliases']['Items'] == ['emlynoregan.com']

    if args.command == 'edge':
        journal = state / 'edge-journal.json'
        assert not journal.exists(), 'Inspect existing edge journal; never blindly replay a mutation.'
        assert digest(actual) == digest(before['config']), 'Distribution changed since inspection.'
        assert not actual['Enabled']
        assert root_record(dns) == old_record
        code = (Path(__file__).parent / 'function.js').read_bytes()
        entry = {'account': ACCOUNT, 'distribution': DISTRIBUTION,
                 'before_sha256': digest(actual), 'function_sha256': hashlib.sha256(code).hexdigest(),
                 'phase': 'creating-function'}
        save(journal, entry)
        created = cf.create_function(Name=FUNCTION,
            FunctionConfig={'Comment': 'Redirect retired emlynoregan.com to Everything', 'Runtime': 'cloudfront-js-2.0'},
            FunctionCode=code)
        entry.update(phase='function-created', function_arn=created['FunctionSummary']['FunctionMetadata']['FunctionARN'],
                     function_etag=created['ETag'])
        save(journal, entry)
        event = {'version': '1.0', 'context': {'eventType': 'viewer-request'},
                 'viewer': {'ip': '192.0.2.1'}, 'request': {'method': 'GET', 'uri': '/',
                 'querystring': {}, 'headers': {'host': {'value': 'emlynoregan.com'}}, 'cookies': {}}}
        tested = cf.test_function(Name=FUNCTION, IfMatch=created['ETag'], Stage='DEVELOPMENT',
                                  EventObject=json.dumps(event).encode())['TestResult']
        assert not tested.get('FunctionErrorMessage'), tested
        output = json.loads(tested['FunctionOutput'])
        response = output.get('response', output)
        assert response['statusCode'] == 301 and response['headers']['location']['value'] == DESTINATION, output
        entry['test'] = {'status': response['statusCode'], 'location': response['headers']['location']['value']}
        entry['phase'] = 'publishing-function'
        save(journal, entry)
        cf.publish_function(Name=FUNCTION, IfMatch=created['ETag'])
        desired = copy.deepcopy(actual)
        desired['Enabled'] = True
        for behavior in [desired['DefaultCacheBehavior'], *desired.get('CacheBehaviors', {}).get('Items', [])]:
            assert behavior.get('FunctionAssociations', {}).get('Quantity', 0) == 0
            assert behavior.get('LambdaFunctionAssociations', {}).get('Quantity', 0) == 0
            behavior['FunctionAssociations'] = {'Quantity': 1, 'Items': [
                {'FunctionARN': entry['function_arn'], 'EventType': 'viewer-request'}]}
            behavior['ViewerProtocolPolicy'] = 'allow-all'
        save(state / 'distribution-desired.json', desired)
        entry['phase'] = 'updating-distribution'
        save(journal, entry)
        changed = cf.update_distribution(Id=DISTRIBUTION, IfMatch=current['ETag'], DistributionConfig=desired)
        entry.update(phase='distribution-update-accepted', status=changed['Distribution']['Status'])
        save(journal, entry)
        print(json.dumps(entry))
        return

    if args.command == 'status':
        result = {'status': current['Distribution']['Status'], 'enabled': actual['Enabled'],
                  'root_record': root_record(dns)}
        if current['Distribution']['Status'] == 'Deployed' and actual['Enabled']:
            assert digest(actual) == digest(read(state / 'distribution-desired.json'))
            result['direct_host_proofs'] = direct_proof()
            save(state / 'edge-ready.json', result)
        print(json.dumps(result))
        return

    assert current['Distribution']['Status'] == 'Deployed'
    target = {'Name': 'emlynoregan.com.', 'Type': 'A', 'AliasTarget': {
        'HostedZoneId': 'Z2FDTNDATAQYW2', 'DNSName': DOMAIN + '.', 'EvaluateTargetHealth': False}}
    if args.command == 'dns':
        journal = state / 'dns-journal.json'
        assert not journal.exists(), 'Inspect the existing DNS journal before any further write.'
        assert digest(actual) == digest(read(state / 'distribution-desired.json'))
        proofs = direct_proof()
        assert root_record(dns) == old_record
        save(journal, {'phase': 'changing-dns', 'previous': old_record, 'desired': target, 'proofs': proofs})
        result = dns.change_resource_record_sets(HostedZoneId=ZONE, ChangeBatch={
            'Comment': 'Owner-requested root site retirement to Everything',
            'Changes': [{'Action': 'UPSERT', 'ResourceRecordSet': target}]})['ChangeInfo']
        save(journal, {'phase': 'dns-change-accepted', 'previous': old_record, 'desired': target, 'change': result})
        print(json.dumps(result, default=str))
        return

    assert root_record(dns) == target, 'Unexpected live DNS; inspect rather than overwrite.'
    result = dns.change_resource_record_sets(HostedZoneId=ZONE, ChangeBatch={
        'Comment': 'Restore saved GitHub Pages root DNS',
        'Changes': [{'Action': 'UPSERT', 'ResourceRecordSet': old_record}]})['ChangeInfo']
    save(state / 'dns-rollback.json', result)
    print(json.dumps(result, default=str))


if __name__ == '__main__':
    main()
