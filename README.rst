=================
splitwood-ansible
=================

Ansible playbooks and roles for splitwood.

Prerequisites
=============

Images
------

Create the ``/var/lib/ironic/images`` directory on the mgmt-server
(undercloud)::

    sudo mkdir /var/lib/ironic/images

Download the following images and copy them to the ``/var/lib/ironic/images``
directory on the mgmt-server (undercloud)::

    https://slagle.fedorapeople.org/woodshed-images/ironic-python-agent.initramfs
    https://slagle.fedorapeople.org/woodshed-images/ironic-python-agent.kernel
    rhel-atomic-cloud-7.3.5-7.x86_64.qcow2

If you don't know where to download the image for rhel-atomic, ask around on
irc.

Install ``python2-shade`` on the mgmt-server::

    sudo yum -y install https://trunk.rdoproject.org/centos7/current/python2-shade-1.21.0-0.20170531171812.ba0e945.el7.centos.noarch.rpm

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

Registering Nodes
=================

The following command will register nodes using a nodes json file
(``instackenv.json``) as created by tripleo-quickstart::

..note::

    If using an environment created by tripleo-quickstart (or
    tripleo-virt-quickstart), you will need to first edit the nodes json file
    and add the correct mac address for each node. You can get the mac address
    from the libvirt xml on the virthost. See
    https://gist.github.com/slagle/916e53d1e3ced9038872dfe4321ce60f for more
    info.

    ansible-playbook -i inventory splitwood-ansible/ironic-node-registration.yml -e nodes_json_file=/home/stack/instackenv.json

If not using a nodes json file, see
https://github.com/splitwood/splitwood-ansible/blob/master/roles/ironic-node-registration/defaults/main.yml
for specifying a yaml format of nodes data in an Ansible variable.

Provisioning Nodes
==================

The followig command will provision a node::

    ansible-playbook -i inventory splitwood-ansible/ironic-node-provision.yml -e node_name=baremetal-0 -e node_ip=192.168.24.15

Note that ``node_name`` and ``node_ip`` must be specified.

The default login will be user ``cloud-user`` and password ``redhat``. The
password along with an optional public ssh key can be specified with ansible
variables. See https://github.com/splitwood/splitwood-ansible/blob/master/roles/ironic-node-provision/defaults/main.yml.
