#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: aci_epg
short_description: Manage End Point Groups (EPG) on Cisco ACI fabrics (fv:AEPg)
description:
- Manage End Point Groups (EPG) on Cisco ACI fabrics.
- More information from the internal APIC class I(fv:AEPg) at
  U(https://developer.cisco.com/docs/apic-mim-ref/).
author:
- Swetha Chunduri (@schunduri)
version_added: '2.4'
notes:
- The C(tenant) and C(app_profile) used must exist before using this module in your playbook.
  The M(aci_tenant) and M(aci_ap) modules can be used for this.
options:
  tenant:
    description:
    - Name of an existing tenant.
    aliases: [ tenant_name ]
  ap:
    description:
    - Name of an existing application network profile, that will contain the EPGs.
    required: yes
    aliases: [ app_profile, app_profile_name ]
  epg:
    description:
    - Name of the end point group.
    required: yes
    aliases: [ name, epg_name ]
  bd:
    description:
    - Name of the bridge domain being associated with the EPG.
    required: yes
    aliases: [ bd_name, bridge_domain ]
  priority:
    description:
    - QoS class.
    choices: [ level1, level2, level3, unspecified ]
    default: unspecified
  intra_epg_isolation:
    description:
    - Intra EPG Isolation.
    choices: [ enforced, unenforced ]
    default: unenforced
  description:
    description:
    - Description for the EPG.
    aliases: [ descr ]
  fwd_control:
    description:
    - The forwarding control used by the EPG.
    - The APIC defaults new EPGs to C(none).
    choices: [ none, proxy-arp ]
    default: none
  preferred_group:
    description:
    - Whether ot not the EPG is part of the Preferred Group and can communicate without contracts.
    - This is very convenient for migration scenarios, or when ACI is used for network automation but not for policy.
    type: bool
    default: 'no'
    version_added: '2.5'
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
'''

EXAMPLES = r'''
- name: Add a new EPG
  aci_epg:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    ap: intranet
    epg: web_epg
    description: Web Intranet EPG
    bd: prod_bd
    preferred_group: yes

- aci_epg:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    ap: ticketing
    epg: "{{ item.epg }}"
    description: Ticketing EPG
    bd: "{{ item.bd }}"
    priority: unspecified
    intra_epg_isolation: unenforced
    state: present
  with_items:
    - epg: web
      bd: web_bd
    - epg: database
      bd: database_bd

- name: Remove an EPG
  aci_epg:
    host: apic
    username: admin
    password: SomeSecretPassword
    validate_certs: false
    tenant: production
    app_profile: intranet
    epg: web_epg
    state: absent

- name: Query an EPG
  aci_epg:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    ap: ticketing
    epg: web_epg
    state: query

- name: Query all EPGs
  aci_epg:
    host: apic
    username: admin
    password: SomeSecretPassword
    state: query

- name: Query all EPGs with a Specific Name
  aci_epg:
    host: apic
    username: admin
    password: SomeSecretPassword
    validate_certs: false
    epg: web_epg
    state: query

- name: Query all EPGs of an App Profile
  aci_epg:
    host: apic
    username: admin
    password: SomeSecretPassword
    validate_certs: false
    ap: ticketing
    state: query
'''

RETURN = r'''
#
'''

from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = aci_argument_spec()
    argument_spec.update(
        epg=dict(type='str', aliases=['name', 'epg_name']),
        bd=dict(type='str', aliases=['bd_name', 'bridge_domain']),
        ap=dict(type='str', aliases=['app_profile', 'app_profile_name']),
        tenant=dict(type='str', aliases=['tenant_name']),
        description=dict(type='str', aliases=['descr']),
        priority=dict(type='str', choices=['level1', 'level2', 'level3', 'unspecified']),
        intra_epg_isolation=dict(choices=['enforced', 'unenforced']),
        fwd_control=dict(type='str', choices=['none', 'proxy-arp']),
        preferred_group=dict(type='bool'),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        method=dict(type='str', choices=['delete', 'get', 'post'], aliases=['action'], removed_in_version='2.6'),  # Deprecated starting from v2.6
        protocol=dict(type='str', removed_in_version='2.6'),  # Deprecated in v2.6
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['ap', 'epg', 'tenant']],
            ['state', 'present', ['ap', 'epg', 'tenant']],
        ],
    )

    aci = ACIModule(module)

    epg = module.params['epg']
    bd = module.params['bd']
    description = module.params['description']
    priority = module.params['priority']
    intra_epg_isolation = module.params['intra_epg_isolation']
    fwd_control = module.params['fwd_control']
    preferred_group = aci.boolean(module.params['preferred_group'], 'include', 'exclude')
    state = module.params['state']
    tenant = module.params['tenant']
    ap = module.params['ap']

    aci.construct_url(
        root_class=dict(
            aci_class='fvTenant',
            aci_rn='tn-{0}'.format(tenant),
            filter_target='eq(fvTenant.name, "{0}")'.format(tenant),
            module_object=tenant,
        ),
        subclass_1=dict(
            aci_class='fvAp',
            aci_rn='ap-{0}'.format(ap),
            filter_target='eq(fvAp.name, "{0}")'.format(ap),
            module_object=ap,
        ),
        subclass_2=dict(
            aci_class='fvAEPg',
            aci_rn='epg-{0}'.format(epg),
            filter_target='eq(fvAEPg.name, "{0}")'.format(epg),
            module_object=epg,
        ),
        child_classes=['fvRsBd'],
    )

    aci.get_existing()

    if state == 'present':
        # Filter out module parameters with null values
        aci.payload(
            aci_class='fvAEPg',
            class_config=dict(
                name=epg,
                descr=description,
                prio=priority,
                pcEnfPref=intra_epg_isolation,
                fwdCtrl=fwd_control,
                prefGrMemb=preferred_group,
            ),
            child_configs=[
                dict(fvRsBd=dict(attributes=dict(tnFvBDName=bd))),
            ],
        )

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='fvAEPg')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
