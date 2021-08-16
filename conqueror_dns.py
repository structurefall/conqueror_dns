#!/usr/bin/env python3

from boto3 import session
from datetime import datetime
from re import sub
from requests import get
import logging

COMPUTERNAME = 'somehost.somezone.com'
AWS_PROFILE = 'profile_name'
HOSTED_ZONE = 'somezone.com'

logging.basicConfig(level='INFO')


def check_current_conqueror_value(client, zone_id):
    '''Check the current IP in Route53.'''
    sets = client.list_resource_record_sets(HostedZoneId=zone_id)
    record_array = [
                        r for r in sets['ResourceRecordSets']
                        if r['Name'] == f'{COMPUTERNAME}.'
                   ]
    if len(record_array) > 0:
        value = record_array[0]['ResourceRecords'][0]['Value']
    else:
        value = 'NOT FOUND'
    return value

def check_current_public_ip():
    '''Check the current IP address for the house. Depends on ipify.org.'''
    ipify_json = get('https://api.ipify.org?format=json')
    ip = ipify_json.json()['ip']
    return ip

def get_zone(client):
    '''Get the zone ID for the hosted zone.'''
    zones = client.list_hosted_zones()
    zone = [
                z for z in zones['HostedZones']
                if z['Name'] == f'{HOSTED_ZONE}.'
           ][0]
    zone_id = sub(r'^/hostedzone/', '', zone['Id'])
    return zone_id


def update_dns(client, zone_id, ip):
    '''Upsert a record with the values we want.'''
    now = datetime.strftime(datetime.now(), format='%I:%M%p, %B %d, %Y')
    ChangeBatch={
        'Comment': f'Updating via conqueror_dns script at {now}',
        'Changes': [
            {
                'Action': 'UPSERT',
                'ResourceRecordSet': {
                    'Name': 'conqueror.everythinggoescold.com.',
                    'Type': 'A',
                    'TTL': 300,
                    'ResourceRecords': [
                        {
                            'Value': ip
                        },
                    ]
                }
            },
        ]
    }
    resp = client.change_resource_record_sets(HostedZoneId=zone_id,
                                              ChangeBatch=ChangeBatch)
    return(resp)


def main():
    my_session = session.Session(profile_name=AWS_PROFILE)
    client = my_session.client('route53')
    zone_id = get_zone(client)
    current_conqueror_value = check_current_conqueror_value(client, zone_id)
    current_public_ip = check_current_public_ip()
    logging.info(f'Public IP is {current_public_ip}. Address for '
                 f'{COMPUTERNAME} in Route53 is {current_conqueror_value}.')
    if current_conqueror_value != current_public_ip:
        logging.warn('Update needed. Updating Route53...')
        resp = update_dns(client, zone_id, current_public_ip)
        logging.info('Route53 update request submitted. Response is:')
        logging.info(resp)
        exit()
    else:
        logging.info('IPs match. Exiting.')
        exit()


if __name__ == '__main__':
    main()
