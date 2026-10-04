from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

import config
from supabase_client import get_profile

bearer_scheme = HTTPBearer(auto_error=False)

_jwks_client = None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        url = config.require(config.SUPABASE_URL, "SUPABASE_URL")
        service_key = config.require(config.SUPABASE_SERVICE_ROLE_KEY, "SUPABASE_SERVICE_ROLE_KEY")
        # Supabase's API gateway requires an `apikey` header on every
        # /auth/v1/ request, including this public JWKS endpoint - without
        # it, the gateway itself returns 401 before the key data is served.
        _jwks_client = PyJWKClient(
            f"{url.rstrip('/')}/auth/v1/.well-known/jwks.json",
            headers={"apikey": service_key},
        )
    return _jwks_client


def _decode_supabase_jwt(token: str) -> dict:
    """
    Supabase projects sign auth tokens one of two ways depending on when the
    project was created / its signing-key settings:
      - Legacy: HS256, verified with the shared SUPABASE_JWT_SECRET
      - Newer:  ES256 (or RS256), verified against Supabase's public JWKS

    We inspect the token's own header to know which path to take, rather
    than assuming one - this keeps the backend working regardless of which
    signing method a given Supabase project uses.
    """
    header = jwt.get_unverified_header(token)
    alg = header.get("alg")

    if alg == "HS256":
        secret = config.require(config.SUPABASE_JWT_SECRET, "SUPABASE_JWT_SECRET")
        return jwt.decode(token, secret, algorithms=["HS256"], audience="authenticated")

    # Asymmetric signing key - fetch the matching public key from Supabase's JWKS
    signing_key = _get_jwks_client().get_signing_key_from_jwt(token)
    return jwt.decode(token, signing_key.key, algorithms=[alg], audience="authenticated")


@dataclass
class CurrentUser:
    id: str
    email: str
    tier: str
    business_location: str | None = None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header.",
        )

    try:
        payload = _decode_supabase_jwt(credentials.credentials)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired session: {exc}",
        )

    user_id = payload.get("sub")
    email = payload.get("email", "")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")

    profile = get_profile(user_id)
    tier = profile["tier"] if profile else "free"
    business_location = profile.get("business_location") if profile else None

    return CurrentUser(id=user_id, email=email, tier=tier, business_location=business_location)


def require_tier(*allowed_tiers: str):
    """Dependency factory: raises 403 unless the user's tier is allowed."""

    def _dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.tier not in allowed_tiers:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"This feature requires one of: {', '.join(allowed_tiers)}. "
                    f"Your current plan is '{current_user.tier}'."
                ),
            )
        return current_user

    return _dependency
