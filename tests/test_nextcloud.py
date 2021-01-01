import pytest

from nextcloudinflux import NextCloud


def test_nextcloud_init():
    """Test object initialization"""
    config = {"name": "sut",
              "user": "username",
              "password": "SuperSecr3t",
              "url": "http://here.example"}
    sut = NextCloud(**config)

    assert hasattr(sut, "name")
    assert hasattr(sut, "user")
    assert hasattr(sut, "password")
    assert hasattr(sut, "url")

    assert "sut" == sut.name
    assert "username" == sut.user
    assert "SuperSecr3t" == sut.password
    assert "http://here.example" == sut.url
    assert 10 == sut.timeout
    assert True == sut.verify_ssl


@pytest.mark.vcr()
def test_nextcloud_get_data():
    """Test getting data from API endpoint"""
    config = {"name": "sut",
              "user": "admin",
              "password": "T3z1qnj#*^2wtgYU",
              "url": "http://192.168.0.201:8080/ocs/v2.php/apps/serverinfo/api/v1/info"}
    sut = NextCloud(**config)

    response = sut.get_data()
    assert "nextcloud.system.version" in response
    assert "server.webserver" in response
    assert "activeUsers.last5minutes" in response


def test_nextcloud_format_payload():
    payload_example = {
        'ocs': {
            'meta': {
                'status': 'ok',
                'statuscode': 200,
                'message': 'OK'},
            'data': {
                'nextcloud': {
                    'system': {
                        'version': '18.0.6.0',
                        'theme': '',
                        'enable_avatars': 'yes',
                        'enable_previews': 'yes',
                        'memcache.local': '\\OC\\Memcache\\APCu',
                        'memcache.distributed': 'none',
                        'filelocking.enabled': 'yes',
                        'memcache.locking': 'none',
                        'debug': 'no',
                        'freespace': 735814049792,
                        'cpuload': [0.6064453125, 0.62158203125, 0.5634765625],
                        'mem_total': 8135448,
                        'mem_free': 7589060,
                        'swap_total': 4194300,
                        'swap_free': 4149756,
                        'apps': {
                            'num_installed': 23,
                            'num_updates_available': 0,
                            'app_updates': []
                        }
                    },
                    'storage': {
                        'num_users': 2,
                        'num_files': 145225,
                        'num_storages': 3,
                        'num_storages_local': 1,
                        'num_storages_home': 2,
                        'num_storages_other': 0
                    },
                    'shares': {
                        'num_shares': 8,
                        'num_shares_user': 0,
                        'num_shares_groups': 0,
                        'num_shares_link': 8,
                        'num_shares_mail': 0,
                        'num_shares_room': 0,
                        'num_shares_link_no_password': 8,
                        'num_fed_shares_sent': 0,
                        'num_fed_shares_received': 0,
                        'permissions_3_1': '7',
                        'permissions_3_17': '1'
                    }
                },
                'server': {
                    'webserver': 'nginx/1.18.0',
                    'php': {
                        'version': '7.3.20',
                        'memory_limit': 7516192768,
                        'max_execution_time': 3600,
                        'upload_max_filesize': 10737418240
                    },
                    'database': {
                        'type': 'mysql',
                        'version': '10.4.13',
                        'size': 78274560
                    }
                },
                'activeUsers': {
                    'last5minutes': 1,
                    'last1hour': 1,
                    'last24hours': 1
                }
            }
        }
    }
    formatted_response = NextCloud.format_payload(payload_example)

    assert formatted_response is not payload_example
    assert "nextcloud.system.version" in formatted_response
    assert "nextcloud.system.cpuload" in formatted_response
    assert isinstance(formatted_response["nextcloud.system.cpuload"], list)
    assert "nextcloud.system.app.app_updates" in formatted_response
    assert isinstance(formatted_response["nextcloud.system.app.app_updates"], list)
