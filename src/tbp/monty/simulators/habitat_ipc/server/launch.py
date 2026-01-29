from __future__ import annotations

import argparse

from tbp.monty.simulators.habitat_ipc.server.server import HabitatServer
from tbp.monty.simulators.habitat_ipc.transport import ZmqTransport


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=5555)
    p.add_argument("--host", default="127.0.0.1")
    args = p.parse_args()

    transport = ZmqTransport(port=args.port, host=args.host)
    HabitatServer(transport).start()


if __name__ == "__main__":
    main()
