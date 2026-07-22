# auth/web-server/rotate_keys.py
#
# Scheduler-friendly command for one deterministic signing-key rotation phase.

import argparse

import init_mongodb  # noqa: F401

from config import Config
from oidc.key_rotation import activate_rotation, prepare_rotation, retire_old_keys


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'activate', 'retire'))
    return parser.parse_args()


def main():
    phase = parse_args().phase
    if phase == 'prepare':
        prepare_rotation()
    elif phase == 'activate':
        activate_rotation(overlap_seconds=Config.SIGNING_KEY_OVERLAP_SECONDS)
    else:
        retire_old_keys(overlap_seconds=Config.SIGNING_KEY_OVERLAP_SECONDS)


if __name__ == '__main__':
    main()
