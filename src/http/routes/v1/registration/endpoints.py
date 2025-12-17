from fastapi import APIRouter
from fastapi import Depends
from fastapi import Response
from fastapi import status

from src.application.registration.use_cases.activate_user import ActivateUser
from src.application.registration.use_cases.issue_activation_code import (
    IssueActivationCode,
)
from src.application.registration.use_cases.register_user import RegisterUser
from src.domain.user.entities.user import User
from src.http.dependencies.auth import get_authenticated_user_from_basic_auth
from src.http.dependencies.registration import get_activate_user_use_case
from src.http.dependencies.registration import get_issue_activation_code_use_case
from src.http.dependencies.registration import get_register_user_use_case
from src.http.error_management.error_response import ErrorResponse
from src.http.routes.v1.registration.schemas import ActivateUserRequest
from src.http.routes.v1.registration.schemas import PublicUserResponse
from src.http.routes.v1.registration.schemas import RegisterUserRequest

router = APIRouter()


@router.post(
    "",
    response_model=PublicUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email and password. An activation code will be sent via email.",
    responses={
        status.HTTP_201_CREATED: {
            "model": PublicUserResponse,
            "description": "User successfully registered",
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "User already exists",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "model": ErrorResponse,
            "description": "Validation error",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Internal server error",
        },
    },
)
async def register_user(
    request: RegisterUserRequest,
    register_use_case: RegisterUser = Depends(get_register_user_use_case),
    issue_code_use_case: IssueActivationCode = Depends(get_issue_activation_code_use_case),
) -> PublicUserResponse:
    """Register a new user.

    Args:
        request: Registration request with email and password
        register_use_case: RegisterUser use case instance (injected via dependency)
        issue_code_use_case: IssueActivationCode use case instance (injected via dependency)

    Returns:
        Registration response with user details
    """
    user = await register_use_case.execute(email=request.email, password=request.password)

    # Note: Keeping registration and activation code issuance separate allows for reuse
    # (e.g., resend-code endpoint). In a more complex architecture, this could be
    # submitted to an async worker task queue or FastAPI background tasks.
    await issue_code_use_case.execute(user_id=user.id)

    return PublicUserResponse(
        public_id=str(user.public_id),
        email=user.email,
        status=user.status.value,
    )


@router.post(
    "/activate",
    response_model=PublicUserResponse,
    status_code=status.HTTP_200_OK,
    summary="Activate a user account",
    description="Activate a user account using the 4-digit code received via email. Requires Basic Auth (email:password) to verify the user's identity.",
    responses={
        status.HTTP_200_OK: {
            "model": PublicUserResponse,
            "description": "User successfully activated",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Invalid activation code (wrong or expired)",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Missing or invalid Basic Auth credentials (email:password)",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "User or activation code not found",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "model": ErrorResponse,
            "description": "Validation error",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Internal server error",
        },
    },
)
async def activate_user(
    request: ActivateUserRequest,
    auth_user: User = Depends(get_authenticated_user_from_basic_auth),
    use_case: ActivateUser = Depends(get_activate_user_use_case),
) -> PublicUserResponse:
    """Activate a user account with activation code.

    Args:
        request: Activation request with 4-digit code
        auth_user: Authenticated user from Basic Auth credentials (injected via dependency)
        use_case: ActivateUser use case instance (injected via dependency)

    Returns:
        Activation response with user details
    """
    user = await use_case.execute(user_id=auth_user.id, code=request.code)

    return PublicUserResponse(
        public_id=str(user.public_id),
        email=user.email,
        status=user.status.value,
    )


@router.get(
    "/me",
    response_model=PublicUserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user",
    description="Get the current authenticated user's information. Requires Basic Auth (email:password).",
    responses={
        status.HTTP_200_OK: {
            "model": PublicUserResponse,
            "description": "Current user information",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Missing or invalid Basic Auth credentials (email:password)",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Internal server error",
        },
    },
)
async def get_current_user(
    auth_user: User = Depends(get_authenticated_user_from_basic_auth),
) -> PublicUserResponse:
    """Get the current authenticated user.

    Args:
        auth_user: Authenticated user from Basic Auth credentials (injected via dependency)

    Returns:
        Public user information
    """
    return PublicUserResponse(
        public_id=str(auth_user.public_id),
        email=auth_user.email,
        status=auth_user.status.value,
    )


@router.post(
    "/resend-code",
    status_code=status.HTTP_201_CREATED,
    summary="Resend activation code",
    description="Issue a new activation code for the authenticated user. The code will be sent via email. Requires Basic Auth (email:password).",
    responses={
        status.HTTP_201_CREATED: {
            "description": "New activation code issued and sent via email",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Missing or invalid Basic Auth credentials (email:password)",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "User not found",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Internal server error",
        },
    },
)
async def resend_activation_code(
    auth_user: User = Depends(get_authenticated_user_from_basic_auth),
    use_case: IssueActivationCode = Depends(get_issue_activation_code_use_case),
) -> Response:
    """Resend activation code for the authenticated user.

    Args:
        auth_user: Authenticated user from Basic Auth credentials (injected via dependency)
        use_case: IssueActivationCode use case instance (injected via dependency)

    Returns:
        Empty response with 201 status code
    """
    await use_case.execute(user_id=auth_user.id)
    return Response(status_code=status.HTTP_201_CREATED)

    
