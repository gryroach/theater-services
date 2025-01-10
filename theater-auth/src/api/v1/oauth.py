from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse

from db.db import get_session
from exceptions.auth_exceptions import InvalidProviderError
from schemas.login import LoginPasswordResponse
from schemas.user import UserEmailRegister
from services.auth import AuthService, get_auth_service
from services.oauth import get_oauth_provider
from services.user import UserService, get_user_service

router = APIRouter()


@router.get("/{provider}/login")
async def login(provider: str):
    """
    Генерация URL для авторизации через указанный провайдер.
    """
    try:
        oauth_provider = get_oauth_provider(provider)
        return RedirectResponse(oauth_provider.get_authorization_url())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{provider}/callback",
    response_model=LoginPasswordResponse,
)
async def callback(
    provider: str,
    request: Request,
    db: AsyncSession = Depends(get_session),
    user_service: UserService = Depends(get_user_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Коллбэк для обработки ответа от провайдера OAuth.
    """
    try:
        oauth_provider = get_oauth_provider(provider)
        user_info = await oauth_provider.get_user_info(str(request.url))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=403, detail=f"Authorization failed: {e}"
        )

    try:
        user, password = await user_service.register_user_by_oauth(
            db,
            UserEmailRegister(
                first_name=user_info.get("first_name", ""),
                last_name=user_info.get("last_name", ""),
                email=user_info["email"],
            ),
            provider
        )
    except InvalidProviderError as e:
        raise HTTPException(status_code=400, detail=str(e))

    ip_address = request.client.host
    user_agent = request.headers.get("User-Agent", "Unknown")
    tokens = await auth_service.login(
        db, user.login, user.password, ip_address, user_agent, user
    )
    return LoginPasswordResponse(login=user.login, password=password, **tokens.model_dump())


@router.post(
    "/{provider}/exchange-tokens",
    response_model=LoginPasswordResponse,
)
async def exchange_tokens(
    provider: str,
    code: str,
    db: AsyncSession = Depends(get_session),
    user_service: UserService = Depends(get_user_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Обмен кода авторизации на токены для OAuth-провайдеров.
    """
    try:
        oauth_provider = get_oauth_provider(provider)
        tokens = await oauth_provider.exchange_code_for_tokens(code)

        user_info = await oauth_provider.get_user_info(tokens["access_token"])
        try:
            user, password = await user_service.register_user_by_oauth(
                db,
                UserEmailRegister(
                    first_name=user_info.get("first_name", ""),
                    last_name=user_info.get("last_name", ""),
                    email=user_info.get("email", user_info.get("login")),
                ),
                provider
            )
        except InvalidProviderError as e:
            raise HTTPException(status_code=400, detail=str(e))

        auth_tokens = await auth_service.login(
            db,
            user.login,
            password,
            ip_address="N/A",
            user_agent="OAuthClient",
            user=user,
        )
        return LoginPasswordResponse(
            login=user.login,
            password=password,
            oauth_tokens=tokens,
            **auth_tokens.model_dump(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=403, detail=f"Token exchange failed: {e}"
        )


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
