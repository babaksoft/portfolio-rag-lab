"""Browser authentication-session routes."""

from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

from portfolio_rag.api.dependencies import get_api_settings
from portfolio_rag.api.settings import ApiSettings

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/logout", include_in_schema=False)
async def logout(
    settings: Annotated[ApiSettings, Depends(get_api_settings)],
) -> RedirectResponse:
    """Expire ALB session cookies and redirect through Cognito sign-out."""
    if (
        settings.authentication_mode != "alb_cognito"
        or settings.cognito_domain is None
        or settings.cognito_client_id is None
        or settings.application_url is None
    ):
        return RedirectResponse(url="/", status_code=303)

    query = urlencode(
        {
            "client_id": settings.cognito_client_id,
            "logout_uri": settings.application_url,
        }
    )
    response = RedirectResponse(
        url=f"https://{settings.cognito_domain}/logout?{query}",
        status_code=303,
    )
    for suffix in ("", "-0", "-1", "-2", "-3"):
        response.delete_cookie(
            key=f"AWSELBAuthSessionCookie{suffix}",
            path="/",
            secure=True,
            httponly=True,
            samesite="lax",
        )
    return response
