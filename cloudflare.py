#!/usr/bin/python3

import CloudFlare
import json
import sys
import pickle
from zabbix.api import ZabbixAPI
import configparser

conf = configparser.RawConfigParser()
conf.read('cloudflare.ini')     


cloudflare_user = conf['CREDENTIALS']['cloudflare_user']
cloudflare_token = conf['CREDENTIALS']['cloudflare_token']
zabbix_user = conf['CREDENTIALS']['zabbix_user']
zabbix_password = conf['CREDENTIALS']['zabbix_password']
zabbix_url = conf['CREDENTIALS']['zabbix_url']
zabbix_hosts = conf['HOSTS']['hosts_list']
zabbix_hosts = zabbix_hosts.splitlines()




def create_hostgroup(api):

    try:
        params = {'name': 'Cloudflare_Status_Codes'}
        id = api.do_request('hostgroup.create', params)
        id = id['result']['groupids'][0]
        return id

    except:
        params = {'filter': {'name': ['Cloudflare_Status_Codes']}}
        id = api.do_request('hostgroup.get', params)
        id = id['result'][0]['groupid']
        return id


def create_host(host, group_id, api):

    hostname = host + '_status_codes'
    params = {'host': hostname, 'groups': [{'groupid': group_id}], "interfaces": [
            {
                "type": 1,
                "main": 1,
                "useip": 1,
                "ip": "127.0.0.1",
                "dns": "",
                "port": "10050"
            }
        ]
    }
    hostid = api.do_request('host.create', params)
    hostid = hostid['result']['hostids'][0]

    params_interface = {'hostids': hostid}
    interfaceid = api.do_request('hostinterface.get', params_interface)
    interfaceid = interfaceid['result'][0]['interfaceid']

    key_lld = 'cloudflare.py[-l, ' + host + ']'
    params_lld = {'name': host, 'key_': key_lld, 'hostid': hostid, 'type': 10, 'interfaceid': interfaceid, 'delay': 1500}
    lld_id = api.do_request('discoveryrule.create', params_lld)
    lld_id = lld_id['result']['itemids'][0]

    key_prototype = 'cloudflare.py[ -s, ' + host + ', {#ITEMNAME}]'
    params_prototype = {
                            'name': '{#ITEMNAME}',
                            'key_': key_prototype,
                            'hostid': hostid,
                            'ruleid': lld_id,
                            'type': 10,
                            'value_type': 3,
                            'interfaceid': interfaceid,
                            'delay': 1800
    }

    api.do_request('itemprototype.create', params_prototype)
    stout = 'Host ' + host + ' creado...'

    return stout

def get_status(inputzone, api):

    zone = api.zones.get(params={'name': inputzone})
    zone_id = zone[0]['id']
    response = api.zones.analytics.dashboard.get(zone_id, params={'since': '-30', 'util': '0'})
    status_codes = response['totals']['requests']['http_status']
    return status_codes


def zabbix_discovery_rule(datax):

    status_codes = datax
    lld_list = list()

    for status_name in status_codes.keys():

        itemkey = 'TEMP'
        dictx = {'{#ITEMNAME}': status_name, '{#ITEMKEY}': itemkey}
        lld_list.append(dictx)

    itemkey_500 = 'TEMP'
    percentege_dict = {'{#ITEMNAME}': 'Porcentaje_errores_500', '{#ITEMKEY}': itemkey_500}
    lld_list.append(percentege_dict)
    lld_final = {'data': lld_list}

    return json.dumps(lld_final, indent=3, sort_keys=True)


def percentage_item_get(datax):

    status_codes = datax
    total_errors = sum(list(status_codes.values()))

    errors_500 = list()

    for error in status_codes.keys():

        error_str = str(error)

        if error_str.startswith('5'):
            errors_500.append(int(error))

        else:
            pass

    total_errors_500 = sum(errors_500)

    percentage = total_errors_500 * 100
    percentage = percentage / total_errors
    percentage = int(percentage)
    percentage = {'Porcentaje_errores_500': percentage}

    return percentage


def store_item_values(values, zonename):

    values = values
    percentage = percentage_item_get(values)
    values.update(percentage)
    zone_name = zonename
    filename = '/var/tmp/status_' + zone_name + '.pickle'

    with open(filename, 'wb') as f:
        pickle.dump(values, f)


def get_item_values(zone, statuscode):

    zone_name = zone
    status_key = statuscode
    filename = '/var/tmp/status_' + zone_name + '.pickle'

    with open(filename, 'rb') as f:

        errors = pickle.load(f)

        try:

            error_value = errors[status_key]

        except KeyError:

            error_value = 0

    return error_value


def main():

    if sys.argv[1] == '-l':

        cf = CloudFlare.CloudFlare(email=cloudflare_user, token=cloudflare_token)
        zone = sys.argv[2]
        data_t = get_status(zone, cf)
        data_to_print = zabbix_discovery_rule(data_t)
        print(data_to_print)

        store_item_values(data_t, zone)

    elif sys.argv[1] == '-s':

        zone_name = sys.argv[2]
        status_key = sys.argv[3]
        statuscodes = get_item_values(zone_name, status_key)
        print(statuscodes)

    elif sys.argv[1] == '--create':

        zapi = ZabbixAPI(url=zabbix_url, user=zabbix_user, password=zabbix_password)
        id = create_hostgroup(zapi)

        for host in zabbix_hosts:

            try:
                stout = create_host(host, id, zapi)
                print(stout)

            except:
                error1 = 'Host ' + host + ' ya existe en la base de datos.'
                print(error1)

    else:

        print('Parametro invalido')

if __name__ == '__main__':
    main()
