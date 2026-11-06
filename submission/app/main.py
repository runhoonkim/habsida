from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
)
from sqlalchemy.orm import Session
from auth import (
    hash_password,
    verify_password, 
    create_access_token,
    decode_access_token
)
from database import get_db
from models import User, Product, Order
from schemas import (
    UserCreate,
    OrderCreate,
    OrderUpdate,
    OrderStatus,
    OrderOut
)

app = FastAPI(title="App API")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/register")
def register(
    payload: UserCreate,
    db: Session = Depends(get_db),
):
    # check if user exists
    existing_user = (
        db.query(User)
        .filter(User.email == payload.email)
        .first()
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists."
        )

    # create an user
    user = User(
        email = payload.email,
        full_name = payload.full_name,
        hashed_password = hash_password(payload.password),
        role = "member",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user

@app.post("/token")
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate a user and issue a JWT access token.

    Credentials must be submitted as form data, using the OAuth2
    "username" field for the user's email address.

    Args:
        form: Login form containing the email and plaintext password.
        db: Database session supplied by the get_db dependency.

    Returns:
        A dictionary containing the access token and its bearer type.

    Raises:
        HTTPException: If the user does not exist or the password is
            incorrect, with HTTP status 401.
    """
    user = (
        db.query(User)
        .filter(User.email == form.username)
        .first()
    )

    # raise error if user is not found or the password is incorrect
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # create a token
    token = create_access_token(user.id)

    return {
        "access_token": token,
        "token_type": "bearer",
    }

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User: 
    """
    Validate a bearer token and retrieve the authenticated user.

    Args:
        token: Access token extracted from the Authorization header
            by oauth2_scheme.
        db: Database session supplied by the get_db dependency.

    Returns:
        The User object identified by the validated token.

    Raises:
        HTTPException: With status 401 if the token is invalid or
            expired, or the associated user no longer exists.
    """
    user_id = decode_access_token(token)
    # check if user_id exists
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token."
        )

    user = db.get(User, user_id)
    # check if user exists
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists."
        )

    return user

@app.get("/me")
def read_me(
    current_user: User = Depends(get_current_user),
):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role
    }

@app.post("/orders")
def create_order(
    payload: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # check if product exists
    product = db.get(Product, payload.product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product not found.",
        )


    # create an order
    order = Order(
        **payload.model_dump(),
        user_id=current_user.id, 
        status="pending", # status added at the endpoint
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    return order

@app.get("/orders", response_model=list[OrderOut])
def list_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: OrderStatus | None = Query(default=None),
    product_id: int | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Order)

    # Non-admin users can only see their orders
    if current_user.role != "admin":
        query = query.filter(Order.user_id == current_user.id)

    if status is not None: