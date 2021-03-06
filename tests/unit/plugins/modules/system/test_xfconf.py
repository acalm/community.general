# Author: Alexei Znamensky (russoz@gmail.com)
# Largely adapted from test_redhat_subscription by
# Jiri Hnidek (jhnidek@redhat.com)
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

from ansible.module_utils import basic
from ansible_collections.community.general.plugins.modules.system import xfconf

import pytest

TESTED_MODULE = xfconf.__name__


@pytest.fixture
def patch_xfconf(mocker):
    """
    Function used for mocking some parts of redhat_subscribtion module
    """
    mocker.patch('ansible_collections.community.general.plugins.modules.system.xfconf.AnsibleModule.get_bin_path',
                 return_value='/testbin/xfconf-query')


@pytest.mark.parametrize('patch_ansible_module', [{}], indirect=['patch_ansible_module'])
@pytest.mark.usefixtures('patch_ansible_module')
def test_without_required_parameters(capfd, patch_xfconf):
    """
    Failure must occurs when all parameters are missing
    """
    with pytest.raises(SystemExit):
        xfconf.main()
    out, err = capfd.readouterr()
    results = json.loads(out)
    assert results['failed']
    assert 'missing required arguments' in results['msg']


TEST_CASES = [
    # Test the case, when the system is already registered
    [
        {'channel': 'xfwm4', 'property': '/general/inactive_opacity', 'state': 'get'},
        {
            'id': 'test_simple_property_get',
            'run_command.calls': [
                (
                    # Calling of following command will be asserted
                    '/testbin/xfconf-query --channel xfwm4 --property /general/inactive_opacity',
                    # Was return code checked?
                    {'check_rc': False},
                    # Mock of returned code, stdout and stderr
                    (0, '100/n', '',),
                ),
            ],
            'changed': False,
            'value': '100'
        }
    ],
    [
        {'channel': 'xfwm4', 'property': '/general/workspace_names', 'state': 'get'},
        {
            'id': 'test_property_get_array',
            'run_command.calls': [
                (
                    # Calling of following command will be asserted
                    '/testbin/xfconf-query --channel xfwm4 --property /general/workspace_names',
                    # Was return code checked?
                    {'check_rc': False},
                    # Mock of returned code, stdout and stderr
                    (0, 'Value is an array with 3 items:\n\nMain\nWork\nTmp\n', '',),
                ),
            ],
            'changed': False,
            'value': ['Main', 'Work', 'Tmp']
        },
    ],
    [
        {'channel': 'xfwm4', 'property': '/general/use_compositing', 'state': 'get'},
        {
            'id': 'test_property_get_bool',
            'run_command.calls': [
                (
                    # Calling of following command will be asserted
                    '/testbin/xfconf-query --channel xfwm4 --property /general/use_compositing',
                    # Was return code checked?
                    {'check_rc': False},
                    # Mock of returned code, stdout and stderr
                    (0, 'true', '',),
                ),
            ],
            'changed': False,
            'value': True
        },
    ],
    [
        {'channel': 'xfwm4', 'property': '/general/use_compositing', 'state': 'get'},
        {
            'id': 'test_property_get_bool_false',
            'run_command.calls': [
                (
                    # Calling of following command will be asserted
                    '/testbin/xfconf-query --channel xfwm4 --property /general/use_compositing',
                    # Was return code checked?
                    {'check_rc': False},
                    # Mock of returned code, stdout and stderr
                    (0, 'false', '',),
                ),
            ],
            'changed': False,
            'value': False
        },
    ],
    [
        {
            'channel': 'xfwm4',
            'property': '/general/workspace_names',
            'state': 'present',
            'value_type': 'string',
            'value': ['A', 'B', 'C'],
        },
        {
            'id': 'test_property_set_array',
            'run_command.calls': [
                (
                    # Calling of following command will be asserted
                    '/testbin/xfconf-query --channel xfwm4 --property /general/workspace_names',
                    # Was return code checked?
                    {'check_rc': False},
                    # Mock of returned code, stdout and stderr
                    (0, 'Value is an array with 3 items:\n\nMain\nWork\nTmp\n', '',),
                ),
                (
                    # Calling of following command will be asserted
                    "/testbin/xfconf-query --channel xfwm4 --property /general/workspace_names --create "
                    "--force-array --type 'string' --set 'A' --type 'string' --set 'B' --type 'string' --set 'C'",
                    # Was return code checked?
                    {'check_rc': False},
                    # Mock of returned code, stdout and stderr
                    (0, '', '',),
                ),
            ],
            'changed': True,
            'previous_value': ['Main', 'Work', 'Tmp'],
            'value': ['A', 'B', 'C'],
        },
    ],
]
TEST_CASES_IDS = [item[1]['id'] for item in TEST_CASES]


@pytest.mark.parametrize('patch_ansible_module, testcase',
                         TEST_CASES,
                         ids=TEST_CASES_IDS,
                         indirect=['patch_ansible_module'])
@pytest.mark.usefixtures('patch_ansible_module')
def test_xfconf(mocker, capfd, patch_xfconf, testcase):
    """
    Run unit tests for test cases listen in TEST_CASES
    """

    # Mock function used for running commands first
    call_results = [item[2] for item in testcase['run_command.calls']]
    mock_run_command = mocker.patch(
        'ansible_collections.community.general.plugins.modules.system.xfconf.AnsibleModule.run_command',
        side_effect=call_results)

    # Try to run test case
    with pytest.raises(SystemExit):
        xfconf.main()

    out, err = capfd.readouterr()
    results = json.loads(out)
    print("results = %s" % results)
    assert 'changed' in results
    assert results['changed'] == testcase['changed']
    if 'msg' in results:
        assert results.get('msg') == testcase['msg']
    if 'value' in results:
        assert results['value'] == testcase['value']
    if 'previous_value' in results:
        assert results['previous_value'] == testcase['previous_value']

    assert mock_run_command.call_count == len(testcase['run_command.calls'])
    if mock_run_command.call_count:
        call_args_list = [(item[0][0], item[1]) for item in mock_run_command.call_args_list]
        expected_call_args_list = [(item[0], item[1]) for item in testcase['run_command.calls']]
        print("call args list =\n%s" % call_args_list)
        print("expected args list =\n%s" % expected_call_args_list)
        assert call_args_list == expected_call_args_list
