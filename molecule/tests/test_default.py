import os
import pytest

import testinfra.utils.ansible_runner


testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']
).get_hosts('all')


@pytest.fixture(scope='module')
def grafana_user(host):
    ansible_vars = host.ansible.get_variables()
    user = ansible_vars.get('grafana_os_user', 'grafana')
    group = ansible_vars.get('grafana_os_group', 'grafana')

    return {'user': user, 'group': group}


@pytest.mark.parametrize('pkg', [
    'podman',
    'firewalld'
    # 'libselinux-python'
])
def test_grafana_packages_installed(host, pkg):
    package = host.package(pkg)
    assert package.is_installed


def test_grafana_systemd_config(host):
    data = host.file('/etc/systemd/system/grafana-service.service')

    assert data.exists
    assert data.user == 'root'
    assert data.group == 'root'


def test_grafana_user(host, grafana_user):

    user = host.user(grafana_user['user'])

    assert user.group == grafana_user['group']


def test_grafana_config(host, grafana_user):

    for fname in ['/etc/grafana',
                  '/etc/grafana/env']:
        data = host.file(fname)

        assert data.exists
        assert data.user == grafana_user['user']
        assert data.group == grafana_user['group']


@pytest.mark.parametrize('srv', [
    'grafana-service',
    'firewalld'
])
def test_grafana_running(host, srv):
    service = host.service(srv)

    assert service.is_running
    assert service.is_enabled


def test_grafana_operating(host):
    curl = host.ansible('uri', 'url=https://localhost:3000 '
                        'validate_certs=False',
                        check=False)
    assert(curl['status'] == 200)

    r = host.socket('tcp://0.0.0.0:3000')
    assert(r.is_listening)
