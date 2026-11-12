import argparse
import psutil
import subprocess
import sys

VISUALIZER_EXECUTABLE = "bopmux-visualizer"
VISUALIZER_LINK_PATH = "/usr/local/bin/bopmux-visualizer"
RUNNER_LOG = "runner.log"


def start_visualizer(theme):
    with open(RUNNER_LOG, "w") as log_file:
        process = subprocess.Popen(
            [VISUALIZER_EXECUTABLE, theme],
            start_new_session=True,  # Disconnects from the parent terminal group
            stdout=log_file,  # Silences output so it doesn't break the shell
            stderr=log_file,
        )
        print(process.pid)
        sys.exit(0)


def stop_visualizer():
    for proc in psutil.process_iter():
        try:
            positions = proc.cmdline()
            for position in positions:
                if position == VISUALIZER_LINK_PATH:
                    print(f"Stopping bopmux process {proc.pid}")
                    proc.terminate()
                    return
        except psutil.AccessDenied, psutil.ZombieProcess:
            pass


def run():
    parser = argparse.ArgumentParser(description="bopmux")
    subparsers = parser.add_subparsers(
        dest="command", required=True, help="start or stop"
    )

    start = subparsers.add_parser("start", help="Start bopmux")
    start.add_argument(
        "theme",
        choices=["gray", "blue", "pink", "orange", "yellow"],
        default="gray",
        help="Pick a theme.",
    )
    start = subparsers.add_parser("stop", help="Stop bopmux")

    # subparsers.add_parser("stop", help="Stop bopmux")
    args = parser.parse_args()
    if args.command == "start":
        stop_visualizer()
        start_visualizer(args.theme)
        return

    if args.command == "stop":
        stop_visualizer()
