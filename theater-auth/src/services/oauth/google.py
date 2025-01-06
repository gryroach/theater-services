from functools import lru_cache

import google_auth_oauthlib.flow
from google.auth.transport import requests
from google.oauth2 import id_token
from oauthlib.oauth2 import MismatchingStateError, MissingCodeError

from core.config import settings
from exceptions.auth_exceptions import AuthError


@lru_cache()
def create_flow():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        settings.google_client_file_path,
        scopes=[
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
            "openid",
        ],
    )
    flow.redirect_uri = (
        f"https://{settings.google_redirect_host}"
        f"/api-auth/v1/oauth/google/callback"
    )
    return flow


def get_authorization_url():
    flow = create_flow()
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return authorization_url, state


def get_google_id_info(request_url: str) -> dict:
    flow = create_flow()
    try:
        flow.fetch_token(authorization_response=request_url)
    except (MismatchingStateError, MissingCodeError):
        raise AuthError("Google fetch token error.")

    return id_token.verify_oauth2_token(
        flow.credentials.id_token,
        requests.Request(),
        settings.google_client_id,
        10,
    )
