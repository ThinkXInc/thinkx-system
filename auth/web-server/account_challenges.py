# auth/web-server/account_challenges.py
#
# One-time email challenge issuance and atomic consumption.

from datetime import datetime, timedelta
import hashlib
import hmac
import secrets

import pytz

from models.data.verification_challenge import VerificationChallenge


MAX_ATTEMPTS = 5


def challenge_code_hash(code):
    return hashlib.sha256(code.encode('utf-8')).hexdigest()


def issue_email_challenge(*, purpose, destination, lifetime_seconds, deliver):
    VerificationChallenge.objects(
        purpose=purpose, channel='email', destination=destination
    ).delete()
    code = secrets.token_urlsafe(32)
    challenge = VerificationChallenge(
        purpose=purpose,
        channel='email',
        code_hash=challenge_code_hash(code),
        destination=destination,
        expires_at=datetime.now(pytz.utc) + timedelta(seconds=lifetime_seconds),
    ).save()
    try:
        deliver(destination=destination, code=code, purpose=purpose)
    except Exception:
        challenge.delete()
        raise
    return challenge


def consume_email_challenge(*, purpose, destination, code):
    challenge = VerificationChallenge.objects(
        purpose=purpose,
        channel='email',
        destination=destination,
    ).order_by('-created_at').first()
    if not challenge:
        return False
    expires_at = challenge.expires_at
    if expires_at.tzinfo is None:
        expires_at = pytz.utc.localize(expires_at)
    if expires_at <= datetime.now(pytz.utc) or challenge.attempts >= MAX_ATTEMPTS:
        challenge.delete()
        return False
    if not hmac.compare_digest(challenge.code_hash, challenge_code_hash(code)):
        challenge.update(inc__attempts=1)
        return False
    consumed = VerificationChallenge._get_collection().find_one_and_delete({
        '_id': challenge.id,
        'code_hash': challenge.code_hash,
    })
    return consumed is not None
