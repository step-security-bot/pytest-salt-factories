import socket

import pytest

from saltfactories.utils import ports

pytest.importorskip("docker")


@pytest.fixture(scope="module")
def echo_server_port():
    return ports.get_unused_localhost_port()


@pytest.fixture(scope="module")
@pytest.mark.skip_if_binaries_missing("docker", reason="Docker does not appear to be installed")
def docker_container(request, salt_factories, echo_server_port):
    return salt_factories.spawn_docker_container(
        request,
        "echo-server-test",
        "cjimti/go-echo",
        check_ports=[echo_server_port],
        container_run_kwargs={
            "ports": {"{}/tcp".format(echo_server_port): echo_server_port},
            "environment": {"TCP_PORT": str(echo_server_port), "NODE_NAME": "echo-server-test"},
        },
    )


def test_spawn_docker_container(docker_container, echo_server_port):
    message = b"Hello!\n"
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect(("127.0.0.1", echo_server_port))
        client.settimeout(0.1)
        # Get any welcome message from the server
        while True:
            try:
                data = client.recv(4096)
            except socket.timeout:
                break
        client.send(message)
        while True:
            try:
                response = client.recv(4096)
            except socket.timeout:
                break
        assert response == message
    finally:
        client.close()


def test_docker_container_run(docker_container):
    ret = docker_container.run("echo", "foo")
    assert ret.exitcode == 0
    assert ret.stdout == "foo\n"
    assert ret.stderr is None
    ret = docker_container.run("sh", "-c", ">&2 echo foo")
    assert ret.exitcode == 0
    assert ret.stdout is None
    assert ret.stderr == "foo\n"
