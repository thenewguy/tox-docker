import os
import unittest

import docker
from tox_docker import _validate_link_line


class ToxDockerLinksTest(unittest.TestCase):

    def test_links_created(self):
        client = docker.from_env(version="auto")
        registry_container = None
        nginx_container = None
        for container in client.containers.list():
            if registry_container is None and "registry" in container.attrs['Config']['Image']:
                registry_container = container
            
            if nginx_container is None and "nginx" in container.attrs['Config']['Image']:
                nginx_container = container
            
            if all([registry_container, nginx_container]):
                break

        self.assertIsNotNone(registry_container, "could not find registry container")
        self.assertIsNotNone(nginx_container, "could not find nginx container")
        
        registry_name = registry_container.attrs["Name"]
        nginx_name = nginx_container.attrs["Name"]
        
        registry_links = registry_container.attrs["HostConfig"]["Links"]
        nginx_links = nginx_container.attrs["HostConfig"]["Links"]
        
        self.assertIsNone(registry_links)
        
        expected_nginx_links = [
            "{}:{}/{}".format(registry_name, nginx_name, registry_container.id)
        ]
        self.assertEqual(expected_nginx_links, nginx_links)

    def test_registry_link_works(self):
        client = docker.from_env(version="auto")
        nginx_container = None
        for container in client.containers.list():
            if "nginx" in container.attrs['Config']['Image']:
                nginx_container = container
                break
        self.assertIsNotNone(nginx_container)
        exit_code = nginx_container.exec_run("curl --noproxy '*' http://registry:5000")[0]
        self.assertEqual(exit_code, 0)

    def test_validate_link_line_requires_alias(self):
        for line in (
            'some-image-name',
            'some-image-name:',
        ):
            with self.assertRaises(ValueError) as cm:
                _validate_link_line(line)
            self.assertEqual("Linked to 'some-image-name' container without specifying an alias.")
