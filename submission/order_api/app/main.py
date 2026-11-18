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
    decode_access_token,
    create_refresh_token,
    decode_refresh_token
)
from database import get_db
from models import User, Product, Order
from schemas import (
    TokenPairOut, AccessTokenOut, RefreshTokenRequest,
    UserCreate, UserOut,
    ProductOut,
    OrderCreate, OrderUpdate, OrderStatus, OrderOut
)

app = FastAPI(title="Orders API")
# oauth2_scheme extracts the token from an incoming request 
# it reads the Authorization header and returns the token portion as a string
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ====================================================
# Authentication
# ====================================================
@app.post("/register", response_model=UserOut, status_code=201,
    description=(
        'Create an account with an email, full name, and password. New accounts receive the '
        'member role. Returns the created user with status **201**; password fields are '
        'excluded from the response. Returns **409** if the email is already registered and '
        '**422** for invalid input. Authentication is not required.'
    ),
)
def register(
    payload: UserCreate,
    db: Session = Depends(get_db),
):
    # check if user exists
    """
    Register a member account with a hashed password.

    Args:
        payload: New user's email, full name, and plaintext password.
        db: Database session supplied by get_db.

    Returns:
        The created user, serialized as UserOut with HTTP status 201.

    Raises:
        HTTPException: With status 409 if the email already exists.

    Invalid request data is rejected by FastAPI with status 422.
    """
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

@app.post("/token", response_model=TokenPairOut,
    description=(
        'Log in using form fields `username` (your email address) and `password`. Returns an '
        'access token, a longer-lived refresh token, and `token_type: bearer`. Send the '
        'access token in the `Authorization: Bearer <access_token>` header for protected '
        'requests. Use the refresh token with `POST /refresh` to obtain another access token. '
        'Returns **401** for incorrect credentials and **422** for invalid or missing form '
        'data.'
    ),
)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate a user and issue access and refresh tokens.

    Submit credentials as form data, using the OAuth2 username field
    for the user's email address. Token lifetimes are defined in auth.py.

    Args:
        form: Login form containing the email and plaintext password.
        db: Database session supplied by get_db.

    Returns:
        Access token, refresh token, and bearer token type as TokenPairOut.

    Raises:
        HTTPException: With status 401 if credentials are incorrect.
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


    return {
        "access_token": create_access_token(user.id),
        "refresh_token": create_refresh_token(user.id),
        "token_type": "bearer",
    }

@app.post("/refresh", response_model=AccessTokenOut,
    description=(
        'Send a JSON body containing `refresh_token` to obtain a new access token without '
        'logging in again. An unexpired access token is not required. Returns **401** if the '
        'refresh token is invalid or expired, or its user no longer exists, and **422** for '
        'invalid input. The refresh token remains reusable until it expires; this endpoint '
        'does not replace or revoke it.'
    ),
)
def refresh_access_token(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Exchange a valid refresh token for a new access token.

    An unexpired access token is not required. The existing refresh token
    is not rotated or revoked by this endpoint.

    Args:
        payload: Request body containing the refresh token.
        db: Database session supplied by get_db.

    Returns:
        A new access token and bearer token type as AccessTokenOut.

    Raises:
        HTTPException: With status 401 if the refresh token is invalid,
            expired, or associated with a user who no longer exists.
    """
    user_id = decode_refresh_token(payload.refresh_token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )

    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists."
        )

    return {
        "access_token": create_access_token(user.id),
        "token_type": "bearer",
    }

def get_current_user(
    token: str = Depends(oauth2_scheme), # extract the bearer token
    db: Session = Depends(get_db),
) -> User: 
    """
    Validate a bearer access token and retrieve its user.

    Args:
        token: Token extracted from the Authorization header by oauth2_scheme.
        db: Database session supplied by get_db.

    Returns:
        The User identified by the validated access token.

    Raises:
        HTTPException: With status 401 if the token is invalid, expired,
            of the wrong type, or associated with a deleted user.

    The oauth2_scheme dependency rejects missing bearer authentication.
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

@app.get("/me", response_model=UserOut,
    description=(
        'Retrieve the account associated with your bearer access token. Returns the user '
        'details defined by `UserOut`, excluding password fields. Returns **401** if '
        'authentication is missing, the token is invalid or expired, or the user no longer '
        'exists. Refresh tokens cannot be used to access this endpoint.'
    ),
)
def read_me(
    current_user: User = Depends(get_current_user),
):
    """
    Return the authenticated user's public account information.

    Args:
        current_user: User supplied by get_current_user after validating
            the bearer access token and looking up the account.

    Returns:
        The current user, serialized as UserOut.

    Authentication failures are rejected with status 401 by dependencies.
    """
    return current_user

# ====================================================
# Orders CRUD 
# ====================================================
def orders_with_total(db: Session = Depends(get_db)):
    """
    Build an order query joined to products with a calculated total.

    Args:
        db: Database session passed by the caller.

    Returns:
        An unexecuted query selecting order fields and total, calculated
        as quantity multiplied by the product's current price. Callers
        must apply authorization filters and execute the query.

    The total is calculated at query time and is not stored on the order.
    """
    return (
        db.query(
            Order.id,
            Order.user_id,
            Order.product_id,
            Order.quantity,
            Order.status,
            Order.created_at,
            (Order.quantity * Product.price).label("total")
        )
        .join(Product, Order.product_id == Product.id)
    )

@app.post("/orders", response_model=OrderOut, status_code=201,
    description=(
        'Create an order for the authenticated user by supplying a product ID and quantity. '
        'The initial status is `pending`; ownership is assigned from your access token. '
        'Returns the created order with status **201**, including `total = quantity * current '
        'product price`. Returns **400** if the product does not exist, **401** for invalid '
        'or missing authentication, and **422** for invalid input. Totals are calculated from '
        'current prices and can change if product prices change.'
    ),
)
def create_order(
    payload: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # check if product exists
    """
    Create a pending order for the authenticated user.

    Args:
        payload: Product ID and quantity for the new order.
        current_user: Authenticated user who will own the order.
        db: Database session supplied by get_db.

    Returns:
        The created order and its total as OrderOut with status 201.
        Total uses quantity multiplied by the product's current price.

    Raises:
        HTTPException: With status 400 if the product does not exist.

    Authentication failures return 401; invalid request data returns 422.
    """
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

    return (
        orders_with_total(db)
        .filter(Order.id == order.id)
        .one()
    )

@app.get("/orders", response_model=list[OrderOut],
    description=(
        'List your orders; admins can list orders belonging to all users. Optionally filter '
        'by `status` and `product_id`; when both are supplied, both must match. Results are '
        'ordered by order ID. Use `skip` (default 0) and `limit` (default 20, maximum 100) '
        'for pagination. Each order includes a total calculated from its quantity and the '
        'current product price. Returns an empty list when no orders match, **401** for '
        'invalid or missing authentication, and **422** for invalid query parameters.'
    ),
)
def list_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: OrderStatus | None = Query(default=None),
    product_id: int | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List authorized orders with optional filters and pagination.

    Members and customers see only their own orders. Admins can see
    all users' orders. Results are ordered by order ID.

    Args:
        skip: Number of matching orders to skip; must be nonnegative.
        limit: Maximum results to return, from 1 to 100; defaults to 20.
        status: Optional order status to match.
        product_id: Optional product ID to match.
        current_user: Authenticated user used to restrict visibility.
        db: Database session supplied by get_db.

    Returns:
        A list of OrderOut records with totals calculated from current
        product prices, or an empty list if no orders match.

    Authentication failures return 401; invalid query parameters return 422.
    """
    query = orders_with_total(db)

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

@app.get("/orders/{id}", response_model=OrderOut,
    description=(
        'Retrieve one order by its ID. The order owner and admins may access it. The response '
        'includes a total calculated from quantity and the current product price. Returns '
        '**404** if the order does not exist, **403** if it belongs to another user and you '
        'are not an admin, **401** for invalid or missing authentication, and **422** for an '
        'invalid path parameter.'
    ),
)
def get_order(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve an order owned by the user or accessible to an admin.

    Args:
        id: Primary key of the order to retrieve.
        current_user: Authenticated user whose access is checked.
        db: Database session supplied by get_db.

    Returns:
        The order as OrderOut, including a total calculated using the
        product's current price.

    Raises:
        HTTPException: With status 404 if the order does not exist, or
            status 403 if a non-admin requests another user's order.

    Authentication failures are rejected with status 401 by dependencies.
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

    return (
        orders_with_total(db)
        .filter(Order.id == order.id)
        .one()      # guarantees data integrity
    )

@app.patch("/orders/{id}", response_model=OrderOut,
    description=(
        'Partially update an order using the fields defined by `OrderUpdate`, such as '
        'quantity or status. Omitted fields retain their values; explicit null values are '
        'rejected. Only the owner or an admin may update the order. Returns the updated order '
        'with a total calculated using the resulting quantity and the current product price. '
        'Returns **404** if the order does not exist, **403** for insufficient permission, '
        '**401** for invalid or missing authentication, and **422** for invalid input.'
    ),
)
def update_order(
    id: int,
    payload: OrderUpdate,
    current_user: User = Depends(get_current_user),
    db : Session = Depends(get_db),
):
    """
    Partially update an order owned by the user or accessible to an admin.

    Only explicitly supplied fields are changed. Explicit null values
    are rejected; omitted fields retain their existing values.

    Args:
        id: Primary key of the order to update.
        payload: Order fields to update, as defined by OrderUpdate.
        current_user: Authenticated user whose access is checked.
        db: Database session supplied by get_db.

    Returns:
        The updated order as OrderOut, including a total calculated from
        the resulting quantity and the product's current price.

    Raises:
        HTTPException: With status 404 if the order does not exist,
            status 403 if a non-admin updates another user's order,
            or status 422 if a supplied field is null.

    Authentication failures return 401; invalid request data returns 422.
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

    return (
        orders_with_total(db)
        .filter(Order.id == order.id)
        .one()      # guarantees data integrity
    )

def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Require the authenticated user to have the admin role.

    Args:
        current_user: Authenticated user supplied by get_current_user.

    Returns:
        The authenticated admin user.

    Raises:
        HTTPException: With status 403 if the user is not an admin.

    Authentication failures are rejected with status 401 by dependencies.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required."
        )

    return current_user

@app.delete("/orders/{id}", status_code=204,
    description=(
        'Permanently delete an order by ID. Requires an authenticated admin account. Returns '
        '**204** with no response body after deletion. Returns **404** if the order does not '
        'exist, **403** if the authenticated user is not an admin, **401** for invalid or '
        'missing authentication, and **422** for an invalid path parameter.'
    ),
)
def delete_order(
    id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Delete an order as an authenticated admin.

    Args:
        id: Primary key of the order to delete.
        admin: Admin user supplied by require_admin.
        db: Database session supplied by get_db.

    Returns:
        An empty response with HTTP status 204 after committing deletion.

    Raises:
        HTTPException: With status 404 if the order does not exist.

    Dependencies reject unauthenticated requests with 401 and requests
    from non-admin users with 403.
    """
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
@app.get("/products", response_model=list[ProductOut],
    description=(
        'List products available as reference data. Any authenticated role may use this '
        'endpoint. Results are ordered by product ID. Use `skip` (default 0) and `limit` '
        '(default 20, maximum 100) for pagination. Returns an empty list if the requested '
        'page has no products, **401** for invalid or missing authentication, and **422** for '
        'invalid query parameters.'
    ),
)
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List products for any authenticated user with pagination.

    Args:
        skip: Number of products to skip; must be nonnegative.
        limit: Maximum results to return, from 1 to 100; defaults to 20.
        current_user: Authenticated user; every role is allowed.
        db: Database session supplied by get_db.

    Returns:
        Products serialized as ProductOut and ordered by product ID,
        or an empty list if no products are found on the requested page.

    Authentication failures return 401; invalid query parameters return 422.
    """
    return (
        db.query(Product)
        .order_by(Product.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

@app.get("/products/{id}", response_model=ProductOut,
    description=(
        'Retrieve product details by product ID. Any authenticated role may use this '
        'endpoint. Returns **404** if the product does not exist, **401** for invalid or '
        'missing authentication, and **422** for an invalid path parameter.'
    ),
)
def get_product(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve one product for any authenticated user.

    Args:
        id: Primary key of the product to retrieve.
        current_user: Authenticated user; every role is allowed.
        db: Database session supplied by get_db.

    Returns:
        The requested product serialized as ProductOut.

    Raises:
        HTTPException: With status 404 if the product does not exist.

    Authentication failures are rejected with status 401 by dependencies.
    """
    product = db.get(Product, id)
    # check if product exists
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found."
        )
    return product