#!/usr/bin/env python
import os
import argparse

from ironicclient import client

try:
    import json
except ImportError:
    import simplejson as json


class OpenshiftInventory(object):

    OPENSHIFT_IMAGE_TAG = 'v3.6.0-alpha.1'
    OPENSHIFT_DEPLOYMENT_T = 'origin'

    def __init__(self):
        self.inventory = {}
        self.read_cli_args()

        # Called with `--list`.
        if self.args.list:
            # self.inventory = self.example_inventory()
            self.inventory = self.ironic_inventory()
        # Called with `--examplelist`.
        elif self.args.examplelist:
            self.inventory = self.example_inventory()
        # Called with `--host [hostname]`.
        elif self.args.host:
            # Not implemented, since we return _meta info `--list`.
            self.inventory = self.empty_inventory()
        else:
            self.inventory = self.empty_inventory()

        print json.dumps(self.inventory)

    def ironic_inventory(self):
        inventory = {
            'group': {
                'hosts': [],
                'vars': {
                    'ansible_ssh_user': 'root',
                    'containerized': True,
                    'openshift_deployment_type': self.OPENSHIFT_DEPLOYMENT_T,
                    'openshift_disable_check': 'memory_availability',
                    'openshift_image_tag': self.OPENSHIFT_IMAGE_TAG,
                    'openshift_storage_glusterfs_timeout': '900',
                    'openshift_hosted_registry_storage_kind': 'glusterfs',
                }
            },
            'masters': [],
            'etcd': [],
            'nodes': [],
            'glusterfs': [],
            '_meta': {
                'hostvars': {}
            }
        }
        kwargs = {
            'os_ironic_api_version': os.environ['IRONIC_API_VERSION'],
            'os_auth_token': os.environ['OS_AUTH_TOKEN'],
            'ironic_url': os.environ['IRONIC_URL'],
        }
        ironic = client.get_client(1, **kwargs)
        ironic_nodes = [
            n.to_dict() for n in ironic.node.list()
            if n.power_state == 'power on' and
            n.provision_state == 'active' and
            not n.maintenance
        ]
        for n in ironic_nodes:
            node = ironic.node.get(n['uuid'])
            inspector_data_path = node.extra['inspector_data_path']
            is_master = node.resource_class == 'openshift_master'
            if inspector_data_path:
                with open(inspector_data_path) as inspect_file:
                    inspect_data = json.load(inspect_file)
                    # TODO: let the user explictly declare it somehow
                    node_address = [
                        inspect_data['all_interfaces'][i]['ip']
                        for i in inspect_data['all_interfaces']
                        if not inspect_data['all_interfaces'][i]['pxe'] and
                        inspect_data['all_interfaces'][i]['ip']
                    ][0]
                    root_disk = inspect_data['root_disk']['name']
                    glusterfs_devices = [
                        d['name']
                        for d in inspect_data['inventory']['disks']
                        if d['name'] != root_disk
                    ]
                    inventory['group']['hosts'].append(node_address)
                    inventory['nodes'].append(node_address)
                    inventory['_meta']['hostvars'][node_address] = {}
                    if is_master:
                        inventory['masters'].append(node_address)
                        inventory['etcd'].append(node_address)
                        inventory['_meta']['hostvars'][node_address][
                            'openshift_schedulable'
                        ] = False
                        inventory['_meta']['hostvars'][node_address][
                            'master'
                        ] = True
                        inventory['_meta']['hostvars'][node_address][
                            'storage'
                        ] = True
                    else:
                        inventory['_meta']['hostvars'][node_address][
                            'openshift_schedulable'
                        ] = True
                        inventory['_meta']['hostvars'][node_address][
                            'node_labels'
                        ] = {'region': 'infra'}
                    if glusterfs_devices:
                        inventory['glusterfs'].append(node_address)
                        inventory['_meta']['hostvars'][node_address][
                            'glusterfs_devices'
                        ] = glusterfs_devices
        # check if it satisfies minimum requirements for glusterfs,
        # otherwise filter out
        if len(inventory['glusterfs']) < 3:
            del inventory['glusterfs']
            del inventory['group']['vars'][
                'openshift_storage_glusterfs_timeout'
            ]
            del inventory['group']['vars'][
                'openshift_hosted_registry_storage_kind'
            ]
            for n in inventory['_meta']['hostvars']:
                if 'glusterfs_devices' in inventory['_meta']['hostvars'][n]:
                    del inventory['_meta']['hostvars'][n]['glusterfs_devices']
        return inventory

    # Example inventory for testing.
    def example_inventory(self):
        return {
            'group': {
                'hosts': [
                    'ocpmaster.localdomain',
                    'ocpnode1.localdomain',
                    'ocpnode2.localdomain',
                    'ocpnode3.localdomain'
                ],
                'vars': {
                    'ansible_ssh_user': 'root',
                    'containerized': True,
                    'openshift_deployment_type': self.OPENSHIFT_DEPLOYMENT_T,
                    'openshift_disable_check': 'memory_availability',
                    'openshift_image_tag': self.OPENSHIFT_IMAGE_TAG,
                    'openshift_storage_glusterfs_timeout': '900',
                    'openshift_hosted_registry_storage_kind': 'glusterfs',
                }
            },
            'masters': ['ocpmaster.localdomain'],
            'etcd': ['ocpmaster.localdomain'],
            'nodes': [
                'ocpmaster.localdomain',
                'ocpnode1.localdomain',
                'ocpnode2.localdomain',
                'ocpnode3.localdomain'
            ],
            'glusterfs': [
                'ocpnode1.localdomain',
                'ocpnode2.localdomain',
                'ocpnode3.localdomain'
            ],
            '_meta': {
                'hostvars': {
                    'ocpmaster.localdomain': {
                        'storage': True,
                        'master': True,
                        'openshift_schedulable': False,
                    },
                    'ocpnode1.localdomain': {
                        'openshift_node_labels': {'region': 'infra'},
                        'openshift_schedulable': True,
                        'glusterfs_devices': ["/dev/sdb"],
                    },
                    'ocpnode2.localdomain': {
                        'openshift_node_labels': {'region': 'infra'},
                        'openshift_schedulable': True,
                        'glusterfs_devices': ["/dev/sdb"],
                    },
                    'ocpnode3.localdomain': {
                        'openshift_node_labels': {'region': 'infra'},
                        'openshift_schedulable': True,
                        'glusterfs_devices': ["/dev/sdb"],
                    },
                }
            }
        }

    # Empty inventory for testing.
    def empty_inventory(self):
        return {'_meta': {'hostvars': {}}}

    # Read the command line args passed to the script.
    def read_cli_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--list', action='store_true')
        parser.add_argument('--host', action='store')
        parser.add_argument('--examplelist', action='store_true')
        self.args = parser.parse_args()

# Get the inventory.
OpenshiftInventory()
