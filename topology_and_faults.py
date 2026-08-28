"""
Week 1-2 Starter: Basic Mininet Topology + Fault Injection

Project: Two-Stage Network Troubleshooting Agent
(ML Detection + LLM Diagnosis)

Requirements:
- Ubuntu with Linux networking
- Mininet installed
- Run with:
    sudo python3 topology_and_faults.py

This script:
1. Creates 4 hosts connected to 1 switch.
2. Collects normal ping telemetry.
3. Injects packet loss.
4. Injects link failure.
5. Injects high latency.
6. Saves telemetry as JSON files.
"""

from mininet.net import Mininet
from mininet.node import OVSBridge
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.cli import CLI

import time
import json
import os


LOG_DIR = "telemetry_logs"
os.makedirs(LOG_DIR, exist_ok=True)


def build_topology():
    """
    Creates:

        h1
         \
        h2 --- s1 --- h3
         /
        h4

    Four hosts connected to one switch.
    """

    print("*** Creating Mininet network")

    net = Mininet(
        controller=None,
        switch=OVSBridge,
        link=TCLink
    )

    print("*** Adding hosts")

    h1 = net.addHost(
        "h1",
        ip="10.0.0.1/24"
    )

    h2 = net.addHost(
        "h2",
        ip="10.0.0.2/24"
    )

    h3 = net.addHost(
        "h3",
        ip="10.0.0.3/24"
    )

    h4 = net.addHost(
        "h4",
        ip="10.0.0.4/24"
    )

    print("*** Adding switch")

    s1 = net.addSwitch("s1")

    print("*** Creating links")

    net.addLink(h1, s1)
    net.addLink(h2, s1)
    net.addLink(h3, s1)
    net.addLink(h4, s1)

    print("*** Starting network")

    net.start()

    return net


def log_telemetry(net, label, filename):
    """
    Collects ping telemetry between every pair of hosts.
    """

    snapshot = {
        "label": label,
        "timestamp": time.time(),
        "pings": {}
    }

    print(f"*** Collecting telemetry: {label}")

    hosts = net.hosts

    for src in hosts:
        for dst in hosts:

            if src != dst:

                print(
                    f"    Pinging {src.name} -> {dst.name}"
                )

                result = src.cmd(
                    f"ping -c 3 -W 1 {dst.IP()}"
                )

                snapshot["pings"][
                    f"{src.name}->{dst.name}"
                ] = result

    filepath = os.path.join(
        LOG_DIR,
        filename
    )

    with open(filepath, "w") as f:
        json.dump(
            snapshot,
            f,
            indent=2
        )

    print(
        f"*** Telemetry logged to {filepath}"
    )

    return snapshot


def inject_packet_loss(
    net,
    host_name="h2",
    loss_percent=40
):
    """
    Injects packet loss on a host interface.
    """

    host = net.get(host_name)
    intf = host.intf()

    print(
        f"*** Injecting FAULT: "
        f"{loss_percent}% packet loss on {host_name}"
    )

    host.cmd(
        f"tc qdisc add dev {intf} root "
        f"netem loss {loss_percent}%"
    )


def inject_high_latency(
    net,
    host_name="h2",
    delay_ms=200
):
    """
    Injects network latency on a host interface.
    """

    host = net.get(host_name)
    intf = host.intf()

    print(
        f"*** Injecting FAULT: "
        f"{delay_ms}ms latency on {host_name}"
    )

    host.cmd(
        f"tc qdisc add dev {intf} root "
        f"netem delay {delay_ms}ms"
    )


def inject_link_failure(
    net,
    host_name="h2"
):
    """
    Takes the link between the host and switch down.
    """

    print(
        f"*** Injecting FAULT: "
        f"link failure on {host_name}"
    )

    net.configLinkStatus(
        host_name,
        "s1",
        "down"
    )


def restore_link(
    net,
    host_name="h2"
):
    """
    Restores a failed link.
    """

    net.configLinkStatus(
        host_name,
        "s1",
        "up"
    )

    print(
        f"*** Restored link on {host_name}"
    )


def clear_faults(
    net,
    host_name="h2"
):
    """
    Removes traffic-control faults.
    """

    host = net.get(host_name)
    intf = host.intf()

    host.cmd(
        f"tc qdisc del dev {intf} root"
    )

    print(
        f"*** Cleared traffic-control faults "
        f"on {host_name}"
    )


def main():

    setLogLevel("info")

    net = build_topology()

    try:

        # --------------------------------------
        # NORMAL / BASELINE
        # --------------------------------------

        print(
            "\n=== Capturing NORMAL telemetry ==="
        )

        log_telemetry(
            net,
            "normal",
            "baseline_normal.json"
        )

        # --------------------------------------
        # PACKET LOSS
        # --------------------------------------

        print(
            "\n=== Injecting PACKET LOSS ==="
        )

        inject_packet_loss(
            net,
            "h2",
            loss_percent=40
        )

        time.sleep(2)

        log_telemetry(
            net,
            "fault_packet_loss",
            "fault_packet_loss.json"
        )

        clear_faults(
            net,
            "h2"
        )

        # --------------------------------------
        # LINK FAILURE
        # --------------------------------------

        print(
            "\n=== Injecting LINK FAILURE ==="
        )

        inject_link_failure(
            net,
            "h2"
        )

        time.sleep(2)

        log_telemetry(
            net,
            "fault_link_failure",
            "fault_link_failure.json"
        )

        restore_link(
            net,
            "h2"
        )

        # --------------------------------------
        # HIGH LATENCY
        # --------------------------------------

        print(
            "\n=== Injecting HIGH LATENCY ==="
        )

        inject_high_latency(
            net,
            "h2",
            delay_ms=200
        )

        time.sleep(2)

        log_telemetry(
            net,
            "fault_high_latency",
            "fault_high_latency.json"
        )

        clear_faults(
            net,
            "h2"
        )

        # --------------------------------------
        # FINISHED
        # --------------------------------------

        print(
            "\n*** All telemetry experiments completed."
        )

        print(
            "*** Telemetry files are in:"
        )

        print(
            f"*** {LOG_DIR}/"
        )

        print(
            "\n*** Starting Mininet CLI."
        )

        print(
            "*** Type 'exit' to quit."
        )

        CLI(net)

    finally:

        print("*** Stopping Mininet network")

        net.stop()


if __name__ == "__main__":
    main()
