from __future__ import annotations

import argparse

from tbp.monty.simulators.habitat_ipc.server.server import HabitatServer
from tbp.monty.simulators.habitat_ipc.transport import ZmqTransport


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--channel-name", required=True)
    args = p.parse_args()

    transport = ZmqTransport(args.channel_name)
    HabitatServer(transport).start()


if __name__ == "__main__":
    main()
