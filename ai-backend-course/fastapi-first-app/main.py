from fastapi import Depends, FastAPI, HTTPException, status, Query, Response, Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import get_db
from models import Order, Product, User
from schemas import OrderCreate, OrderOut, OrderUpdate
from auth import verify_password, create_access_token, decode_access_token
import os
from dotenv import load_dotenv
import json

load_dotenv()
api_key_str = os.environ["VALID_API_KEYS"]
valid_api_keys = json.loads(api_key_str)   # load from env / DB in real code

app = FastAPI(title="Secure Orders API")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def require_api_key(x_api_key: str = Header(...)) -> str:
    if x_api_key not in valid_api_keys.values():
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

# auto_error=False: return None instead of raising when no token is present
optional_oauth2 = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


def user_or_service(
    token: str | None = Depends(optional_oauth2),
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User | str:
    if token:                                   # a human with a valid JWT...
        user_id = decode_access_token(token)
        if user_id is not None:
            user = db.get(User, user_id)
            if user is not None:
                return user
    if x_api_key in valid_api_keys.values():     # ...or a trusted service with a valid key
        return x_api_key
    raise HTTPException(status_code=401, detail="Provide a valid token or API key")


@app.post("/token")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username).first()
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    user_id = decode_access_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User no longer exists")
    return user


@app.get("/me")
def read_me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "email": current_user.email, "role": current_user.role}


# CREATE - Create a new order
@app.post("/orders", response_model=OrderOut, status_code=201)
def create_order(payload: OrderCreate, db: Session=Depends(get_db)):
    order = Order(**payload.model_dump(), status="pending") 
    # model_dump() converts a pydantic payload object to a regular python dictionary
    # ** unpacks the dictionary to into named arguments
    db.add(order)
    db.commit()
    db.refresh(order)        # reload server-generated fields like id and created_at
    return order



@app.get("/orders", response_model=list[OrderOut])
def list_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return db.query(Order).order_by(Order.id).offset(skip).limit(limit).all()




@app.get("/orders/{order_id}", response_model=OrderOut)
def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not allowed to view this order")
    return order


@app.patch("/orders/{order_id}", response_model=OrderOut)
def update_order(order_id: int, payload: OrderUpdate, db: Session=Depends(get_db)):
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        # model_dump changes pydantic object to regular python dictionary
        setattr(order, field, value)

    db.commit()
    db.refresh(order)
    return order


@app.delete("/orders/{order_id}", status_code=204)
def delete_order(order_id: int, db: Session=Depends(get_db)):
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    db.delete(order)
    db.commit()
    return Response(status_code=204)






