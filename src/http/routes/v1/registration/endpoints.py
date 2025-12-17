from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status

from src.application.registration.use_cases.register_user import RegisterUser
from src.domain.user.errors import UserAlreadyExistsError
from src.http.dependencies.registration import get_register_user_use_case
from src.http.routes.v1.registration.schemas import RegisterUserRequest
from src.http.routes.v1.registration.schemas import RegisterUserResponse

router = APIRouter()


@router.post(
    "",
    response_model=RegisterUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email and password. An activation code will be sent via email.",
)
async def register_user(
    request: RegisterUserRequest,
    use_case: RegisterUser = Depends(get_register_user_use_case),
) -> RegisterUserResponse:
    """Register a new user.

    Args:
        request: Registration request with email and password
        use_case: RegisterUser use case instance (injected via dependency)

    Returns:
        Registration response with user details

    Raises:
        HTTPException: 400 if email already exists or validation fails
    """
    try:
        user = await use_case.execute(email=request.email, password=request.password)
        return RegisterUserResponse(
            public_id=str(user.public_id),
            email=user.email,
            status=user.status.value,
        )
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        ) from e
