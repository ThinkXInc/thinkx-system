from __future__ import annotations

import os
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, List, Union

import requests

try:
    from requests_oauthlib import OAuth1  # type: ignore
except Exception:
    OAuth1 = None  # requests-oauthlib が無い場合


class XAPIError(RuntimeError):
    def __init__(
        self,
        status_code: int,
        message: str,
        payload: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload or {}
        self.headers = headers or {}


def _safe_json(resp: requests.Response) -> Optional[Dict[str, Any]]:
    try:
        return resp.json()
    except Exception:
        return None


def _format_error(resp: requests.Response) -> str:
    j = _safe_json(resp)
    if j is None:
        txt = (resp.text or "").strip()
        return txt[:2000] if txt else "(no body)"

    parts: List[str] = []
    for k in ("title", "detail", "reason", "type", "required_enrollment"):
        v = j.get(k)
        if v:
            parts.append(f"{k}={v}")

    if "errors" in j and isinstance(j["errors"], list):
        parts.append(f"errors={j['errors']}")

    if not parts:
        parts.append(json.dumps(j, ensure_ascii=False)[:2000])
    return " | ".join(parts)


def _rate_limit_summary(headers: Dict[str, str]) -> str:
    """
    X公式: x-rate-limit-* を見て reset まで待つのが推奨 :contentReference[oaicite:4]{index=4}
    """
    limit = headers.get("x-rate-limit-limit", "")
    remaining = headers.get("x-rate-limit-remaining", "")
    reset = headers.get("x-rate-limit-reset", "")
    retry_after = headers.get("retry-after", "")

    parts: List[str] = []
    if limit or remaining:
        parts.append(f"rate_limit(limit={limit or '?'}, remaining={remaining or '?'})")

    if reset:
        try:
            reset_epoch = int(float(reset))
            wait = int(reset_epoch - time.time())
            # wait は負になることもある（直後に回復した等）
            parts.append(f"reset={reset_epoch} (in ~{max(wait,0)}s)")
        except Exception:
            parts.append(f"reset={reset}")

    if retry_after:
        parts.append(f"retry-after={retry_after}")

    return " | ".join(parts)


def _project_root() -> Path:
    # /.../scripts/utils/x_api.py -> parents[2] == project root
    return Path(__file__).resolve().parents[2]


def _load_dotenv_if_exists() -> None:
    """
    依存ライブラリ無しで .env を読む（補助）。
    - 既に環境変数にあるキーは上書きしない
    - 形式: KEY=VALUE / export KEY=VALUE
    """
    env_path = _project_root() / ".env"
    if not env_path.exists():
        return

    try:
        for raw in env_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export ") :].strip()
            if "=" not in line:
                continue

            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip()

            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                v = v[1:-1]

            if k and k not in os.environ:
                os.environ[k] = v
    except Exception:
        return


def _env_any(*names: str) -> str:
    for n in names:
        v = (os.getenv(n) or "").strip()
        if v:
            return v
    return ""


def _normalize_exclude(exclude: Optional[Union[str, List[str]]]) -> Optional[str]:
    if exclude is None:
        return None
    if isinstance(exclude, str):
        s = exclude.strip()
        return s or None
    items = [str(x).strip() for x in exclude if str(x).strip()]
    return ",".join(items) if items else None


@dataclass
class XClient:
    base_url: str
    bearer_token: Optional[str] = None  # OAuth2 user token or app bearer (header is same)
    oauth1: Optional[Any] = None        # OAuth1.0a user context

    @classmethod
    def from_env(cls) -> "XClient":
        _load_dotenv_if_exists()

        base_url = _env_any("X_API_BASE_URL", "API_BASE_URL") or "https://api.x.com"
        base_url = base_url.rstrip("/")

        # 1) OAuth2 user token（あれば最優先）
        bearer = _env_any("X_USER_ACCESS_TOKEN", "USER_ACCESS_TOKEN")
        if bearer:
            return cls(base_url=base_url, bearer_token=bearer, oauth1=None)

        # 2) OAuth1.0a user context（あなたの .env: X_ACCESS_SECRET を許容）
        api_key = _env_any("X_API_KEY", "API_KEY", "CONSUMER_KEY")
        api_secret = _env_any("X_API_SECRET", "API_SECRET", "CONSUMER_SECRET")
        access_token = _env_any("X_ACCESS_TOKEN", "ACCESS_TOKEN", "OAUTH_TOKEN")
        access_secret = _env_any(
            "X_ACCESS_TOKEN_SECRET", "X_ACCESS_SECRET",  # ★互換
            "ACCESS_TOKEN_SECRET", "OAUTH_TOKEN_SECRET"
        )

        if api_key and api_secret and access_token and access_secret:
            if OAuth1 is None:
                raise RuntimeError(
                    "OAuth1.0a を使うには requests-oauthlib が必要です:\n"
                    "  pip install requests-oauthlib\n"
                )
            auth = OAuth1(api_key, api_secret, access_token, access_secret)
            return cls(base_url=base_url, bearer_token=None, oauth1=auth)

        # 3) App-only bearer（読み取りだけ試したい場合のフォールバック）
        app_bearer = _env_any("X_BEARER_TOKEN", "BEARER_TOKEN", "X_APP_BEARER_TOKEN")
        if app_bearer:
            return cls(base_url=base_url, bearer_token=app_bearer, oauth1=None)

        raise RuntimeError(
            "X API credentials not set.\n"
            "Set either:\n"
            "  - X_USER_ACCESS_TOKEN (OAuth2 user token)\n"
            "or OAuth1.0a:\n"
            "  - X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET(or X_ACCESS_SECRET)\n"
            "or (read-only fallback):\n"
            "  - X_BEARER_TOKEN\n"
            f"\n.env loaded from: {(_project_root() / '.env')}\n"
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        url = f"{self.base_url}{path}"
        headers = dict(kwargs.pop("headers", {}) or {})
        headers.setdefault("Accept", "application/json")
        kwargs["headers"] = headers
        kwargs.setdefault("timeout", 30)

        if self.bearer_token:
            headers["Authorization"] = f"Bearer {self.bearer_token}"
        if self.oauth1 is not None:
            kwargs["auth"] = self.oauth1

        resp = requests.request(method, url, **kwargs)

        if resp.status_code >= 400:
            msg = _format_error(resp)

            # ★ レート制限情報を付与
            hdrs = {k.lower(): v for k, v in resp.headers.items()}
            rl = _rate_limit_summary(hdrs)
            if rl:
                msg = f"{msg} | {rl}"

            raise XAPIError(
                resp.status_code,
                f"X API error {resp.status_code} {resp.reason}: {msg}",
                _safe_json(resp),
                headers=hdrs,
            )

        return resp

    # ---- v2 endpoints ----

    def create_tweet(self, text: str) -> str:
        payload = {"text": text}
        resp = self._request(
            "POST",
            "/2/tweets",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        j = resp.json()
        return j["data"]["id"]

    def get_me(self) -> Dict[str, Any]:
        resp = self._request("GET", "/2/users/me")
        return resp.json()

    def get_user_by_username(self, username: str) -> Dict[str, Any]:
        resp = self._request("GET", f"/2/users/by/username/{username}")
        return resp.json()

    def fetch_user_tweets(
        self,
        user_id: str,
        max_results: int = 100,
        exclude: Optional[Union[str, List[str]]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"max_results": max_results}
        ex = _normalize_exclude(exclude)
        if ex:
            params["exclude"] = ex
        for k, v in kwargs.items():
            if v is not None:
                params[k] = v

        resp = self._request("GET", f"/2/users/{user_id}/tweets", params=params)
        return resp.json()

    # ---- compatibility aliases ----

    def get_user_id(self, username: str) -> str:
        j = self.get_user_by_username(username)
        data = j.get("data") or {}
        uid = data.get("id")
        if not uid:
            raise RuntimeError(f"Could not resolve user id for username={username}: {j}")
        return str(uid)

    def get_user_tweets(
        self,
        user_id: str,
        max_results: int = 100,
        exclude: Optional[Union[str, List[str]]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        return self.fetch_user_tweets(user_id=user_id, max_results=max_results, exclude=exclude, **kwargs)
