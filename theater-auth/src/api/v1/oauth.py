from typing import Annotated

from core.enums import OauthRequestTypes
from db.db import get_session
from dependencies.auth import JWTBearer
from exceptions.auth_exceptions import InvalidProviderError
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from schemas.jwt import JwtTokenPayload
from schemas.login import (
    LoginPasswordResponse,
    OauthState,
    OauthTokenResponse,
    SocialNetworkAttachedResponse,
)
from schemas.oauth import OAuthCodeRequest
from schemas.user import UserOauthRegister
from services.auth import AuthService, get_auth_service
from services.oauth import get_oauth_provider
from services.user import UserService, get_user_service
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse
from utils import decode_state, encode_state

router = APIRouter()


@router.get("/{provider}/login")
async def login(provider: str):
    """
    Генерация URL для авторизации через указанный провайдер.
    """
    try:
        oauth_provider = get_oauth_provider(provider)
        state = encode_state(
            OauthState(request_type=OauthRequestTypes.login).model_dump()
        )
        return RedirectResponse(
            oauth_provider.get_authorization_url(state=state)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{provider}/link")
async def link(
    provider: str,
    token_payload: Annotated[JwtTokenPayload, Depends(JWTBearer())],
):
    """
    Генерация URL для привязывания социальной сети через указанный провайдер.
    """
    try:
        oauth_provider = get_oauth_provider(provider)
        state = encode_state(
            OauthState(
                request_type=OauthRequestTypes.link, user_id=token_payload.user
            ).model_dump()
        )
        return RedirectResponse(
            oauth_provider.get_authorization_url(state=state)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{provider}/callback",
    response_model=LoginPasswordResponse | SocialNetworkAttachedResponse,
)
async def callback(
    provider: str,
    request: Request,
    state: str,
    code: str = Query(description="Код авторизации OAuth-провайдера"),
    db: AsyncSession = Depends(get_session),
    user_service: UserService = Depends(get_user_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Коллбэк для обработки ответа от провайдера OAuth.
    В зависимости от типа запроса (записан в state) происходит либо привязка социальной сети,
    либо аутентификация пользователя. В последнем случае, если пользователь не существует - он создается.
    Для новых пользователей возвращается сгенерированные логины и пароль, чтобы он мог их поменять.
    """
    try:
        oauth_provider = get_oauth_provider(provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    try:
        user_info = await oauth_provider.get_user_info(
            url=str(request.url), code=code
        )
    except Exception as e:
        raise HTTPException(
            status_code=403, detail=f"Authorization failed: {e}"
        )

    try:
        state = OauthState(**decode_state(state))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if state.request_type == OauthRequestTypes.link:
        await user_service.attach_social_network(
            db,
            state.user_id,
            provider,
            user_info.get("email", user_info.get("login")),
        )
        return SocialNetworkAttachedResponse(
            detail=f"Provider '{provider}' successfully attached"
        )

    try:
        user, password = await user_service.register_user_by_oauth(
            db,
            UserOauthRegister(
                first_name=user_info.get("first_name", ""),
                last_name=user_info.get("last_name", ""),
                provider_id=user_info.get("email", user_info.get("login")),
            ),
            provider,
        )
    except InvalidProviderError as e:
        raise HTTPException(status_code=400, detail=str(e))

    auth_tokens = await auth_service.login(
        db,
        user.login,
        password,
        ip_address=request.client.host,
        user_agent=request.headers.get("User-Agent", "Unknown"),
        user=user,
    )
    return LoginPasswordResponse(
        login=user.login,
        password=password,
        **auth_tokens.model_dump(),
    )


@router.post(
    "/{provider}/exchange-tokens",
    response_model=OauthTokenResponse,
    dependencies=[Depends(JWTBearer())],
)
async def exchange_tokens(
    provider: str,
    request: Request,
    code: str = Query(description="Код авторизации OAuth-провайдера"),
):
    """
    Обмен кода авторизации на токены для OAuth-провайдеров.
    """
    try:
        oauth_provider = get_oauth_provider(provider)
        tokens = await oauth_provider.exchange_code_for_tokens(
            code=code, url=str(request.url)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return OauthTokenResponse(oauth_tokens=tokens)


@router.post("/{provider}/revoke-tokens")
async def revoke_tokens(provider: str, access_token: str):
    """
    Отзыв токенов у провайдера.
    """
    try:
        oauth_provider = get_oauth_provider(provider)
        await oauth_provider.revoke_tokens(access_token)
        return {
            "detail": f"Tokens for provider '{provider}' successfully revoked."
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to revoke tokens: {e}"
        )
