=================
splitwood-ansible
=================

Ansible playbooks and roles for splitwood.

Prerequisites
-------------

These commands require ansible to be installed. They've been tested with
ansible 2.2.0.0.

If tripleo-quickstart (or tripleo-virt-quickstart) was used to create the
virtual environment, then there is already an ansible virtualenv installation
that can be used on the virthost. As the non-root user you can activate the
virtualenv by::

    cd
    source .quickstart/bin/activate


Inventory file
--------------

Create an ansible inventory file for the ``mgmt-server`` host. An example
looks like::

    mgmt-server ansible_host=192.168.23.18 ansible_port=22 ansible_ssh_private_key_file=/home/centos/.quickstart/id_rsa_undercloud ansible_user=stack

The rest of the examples in the doc assume the inventory file is in the current
directory and is simply called ``inventory``.

Get playbooks and roles
-----------------------

Clone this repository::

    git clone https://github.com/splitwood/splitwood-ansible.git

The rest of the examples assume this repo is cloned into a
``splitwood-ansible`` directory in the current working directory.

Images
======

The following command will download and stage the necessary images on the
mgmt-server host. Note that the ansible variable atomic_image is required. If
you don't know the correct url, ask around on irc::

    ansible-playbook -i inventory splitwood-ansible/ironic-images.yml -e atomic_image=<ATOMIC_IMAGE_URL>

Configure DHCP on the provisioning network
==========================================

The provisioning network needs to be configured in order to PXE boot nodes via
DHCP.

See https://github.com/splitwood/splitwood-ansible/blob/master/roles/ironic-dnsmasq-dhcp/defaults/main.yml for the ansible configuration variables that need to be configured. If using a tripleo-virt-quickstart environment the defaults should just work.

Run the playbook to apply the configuration::

    ansible-playbook -i inventory splitwood-ansible/ironic-dnsmasq-dhcp.yml [-e var=value] ...

Registering Nodes
=================

.. note::

    If using an environment created by tripleo-quickstart (or
    tripleo-virt-quickstart), you will need to first edit the nodes json file
    and add the correct mac address for each node. You can get the mac address
    from the libvirt xml on the virthost. See
    https://gist.github.com/slagle/916e53d1e3ced9038872dfe4321ce60f for more
    info.

The following command will register nodes using a nodes json file
(``instackenv.json``) as created by tripleo-quickstart::

    ansible-playbook -i inventory splitwood-ansible/ironic-node-registration.yml -e nodes_json_file=/home/stack/instackenv.json

If not using a nodes json file, see
https://github.com/splitwood/splitwood-ansible/blob/master/roles/ironic-node-registration/defaults/main.yml
for specifying a yaml format of nodes data in an Ansible variable.
An example is provided in ``nodes.json.example``, copy and edit as needed.

Inspecting Nodes
================

Use the following command to inspect a node::

    ansible-playbook -i inventory splitwood-ansible/ironic-node-inspect.yml -e node_name=baremetal-0

The basic cpu/memory/disk/cpu_flags/etc properties will be updated in Ironic
directly after successful inspection. The rest of the inspection data is stored
on the mgmt-server filesystem. You can get the path of the stored data by
looking in the ``extra`` field of the ironic node.

Use ``ironic node-show ...`` to see the updated properties::

    ironic node-show baremetal-0

Example output::

    # <snip>
		| extra                  | {u'inspector_data_path': u'/var/lib/ironic/inspector-store-           |
		|                        | local/d1fa1a73-fa0a-4c38-b32e-caead6b3549a'}                          |
    # <snip>

Then look at
``/var/lib/ironic/inspector-store-local/d1fa1a73-fa0a-4c38-b32e-caead6b3549a``
to see the stored data.

While inspection runs, you can see a log of its progress using:

    sudo docker logs -f ironic_inspector

Provisioning Nodes
==================

The followig command will provision a node::

    ansible-playbook -i inventory splitwood-ansible/ironic-node-provision.yml -e node_name=baremetal-0 -e node_ip=192.168.24.15

Note that ``node_name`` and ``node_ip`` must be specified. For the other
variables, the default values are shown. For more info see
https://github.com/splitwood/splitwood-ansible/blob/master/roles/ironic-node-provision/defaults/main.yml

The default login will be user ``cloud-user`` and password ``redhat``. The
password along with an optional public ssh key can be specified with ansible
variables. See https://github.com/splitwood/splitwood-ansible/blob/master/roles/ironic-node-provision/defaults/main.yml.

While provisioning runs, you can see a log of its progress using:

    sudo docker logs -f ironic_conductor
