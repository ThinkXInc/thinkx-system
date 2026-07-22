# auth/web-server/process_revocations.py
#
# Deterministic worker entry point for retrying pending revocation webhooks.

import init_mongodb  # noqa: F401

from revocation import deliver_pending_revocations


def main():
    results = deliver_pending_revocations()
    if results and not all(results):
        raise RuntimeError('one or more revocation webhooks remain pending')


if __name__ == '__main__':
    main()
