from fastapi import FastAPI, Depends, HTTPException, status, Query, Response
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
    UserOut,
    ProductOut,
    OrderCreate,
    OrderUpdate,
    OrderStatus,
    OrderOut
)

app = FastAPI(title="Orders API")
# oauth2_scheme extracts the token from an incoming request 
# it reads the Authorization header and returns the token portion as a string
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ====================================================
# Authentication
# ====================================================
@app.post("/register", response_model=UserOut, status_code=201)
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
    token: str = Depends(oauth2_scheme), # validates token
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

def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Check if the role of user is admin.

    Args: 
        current_user: SQLAlchemy ORM model User supplied by get_current_user dependency.
    
    Returns:
        current_user: SQLAlchemy ORM model User supplied by get_current_user dependency.

    Raises:
        HTTPException: With status 403 if the user is not admin.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required."
        )

    return current_user

@app.get("/me", response_model=UserOut)
def read_me(
    current_user: User = Depends(get_current_user),
):
    return current_user

# ====================================================
# Orders CRUD 
# ====================================================
@app.post("/orders", response_model=OrderOut, status_code=201)
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
    """
    Get list of orders of the user, if user is admin then all orders.
    """
    query = db.query(Order)

    # Non-admin users can only see their orders
    if current_user.role != "admin":
        query = query.filter(Order.user_id == current_user.id)

    # filter status if not none
    if status is not None:
        query = query.filter(Order.status == status.value)

    # filter product if not none
    if product_id is not None:
        query = query.filter(Order.product_id == product_id)

    return (
        query
        .order_by(Order.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

@app.get("/orders/{id}", response_model=OrderOut)
def get_order(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get order given the order id.
    """
    order = db.get(Order, id)
    # check if order exists
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found."
        )
    # check if the user is admin or the user is accessing their own order
    if order.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can view the order of another user."
        )

    return order

@app.patch("/orders/{id}", response_model=OrderOut)
def update_order(
    id: int,
    payload: OrderUpdate,
    current_user: User = Depends(get_current_user),
    db : Session = Depends(get_db),
):
    """
    Update order given the order id.
    """
    order = db.get(Order, id)
    # check if order exists
    if order is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail="Order not found."
        )

    # check if the user is admin or the user is accessing their own order
    if order.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not allowed to update this order.",
        )

    changes = payload.model_dump(exclude_unset=True)

    # reject explicit none in status and quantity field
    for field, value in changes.items():
        if value is None:
            raise HTTPException(
                status_code=422,
                detail=f"{field} cannot be null.",
            )
    
    # update order
    for field, value in changes.items():
        setattr(order, field, value)

    db.commit()
    db.refresh(order)

    return order

@app.delete("/orders/{id}", status_code=204)
def delete_order(
    id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    order = db.get(Order, id)
    # check if order exists
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found."
        )
    
    # delete order and commit
    db.delete(order)
    db.commit()

    return Response(status_code=204)

# ====================================================
# Read-Only Reference Data 
# ====================================================
@app.get("/products", response_model=list[ProductOut])
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Product)
        .order_by(Product.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

@app.get("/products/{id}", response_model=ProductOut)
def get_product(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.get(Product, id)
    # check if product exists
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found."
        )
    return product