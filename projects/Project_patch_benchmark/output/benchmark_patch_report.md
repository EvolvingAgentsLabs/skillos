# Patch Benchmark V2 Report

**Generated**: 2026-04-12 15:49
**Task**: Fix 2 bugs in a ~993-line Python service using precision edits

## Summary

| Metric | Plain Claude | SkillOS + strict-patch | Delta |
|---|---|---|---|
| Output tokens | 10,286 | 224 | **-97.8%** |
| Input tokens | 3 | 3 | — |
| Cache creation | 12,031 | 15,514 | — |
| Cost (USD) | $0.3417 | $0.1119 | $-0.2298 |
| Duration (s) | 107.3 | 6.9 | — |
| Turns | 1 | 1 | — |

## Quality Verification (Automated — no LLM judge)

| Check | Plain Claude | SkillOS + strict-patch |
|---|---|---|
| Compiles (`ast.parse`) | Yes | Yes |
| Bug 1 fixed (SQL injection) | Yes | Yes |
| Bug 2 fixed (off-by-one) | Yes | Yes |
| **Bugs fixed** | **2/2** | **2/2** |
| Lines changed vs original | 10 | 9 |

## Key Findings

- **Output token reduction**: 97.8% fewer tokens with SkillOS strict-patch
- **Bugs fixed**: Plain 2/2, SkillOS 2/2
- **Lines changed**: Plain 10 vs SkillOS 9 (strict-patch targets only bug lines)
- **Approach**: Plain Claude rewrites entire ~993-line file; SkillOS emits only patch ops for changed lines

## Errors

### Plain Claude
None

### SkillOS + strict-patch
None

### Patch Application Errors
None

## Raw Outputs

### Plain Claude Output

<details>
<summary>Click to expand (10,286 output tokens)</summary>



```python
"""
Legacy User & Order Management Service
=======================================
A monolithic service handling user accounts, orders, and related operations.
Uses raw SQLite for persistence and basic HTTP for the API layer.
"""

import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

# ── Constants ────────────────────────────────────────────────────────────────

DB_PATH = os.environ.get("SERVICE_DB_PATH", "/var/data/service.db")
MAX_POOL_SIZE = int(os.environ.get("MAX_POOL_SIZE", "10"))
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
PASSWORD_MIN_LENGTH = 8
TOKEN_EXPIRY_HOURS = 24
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30

logger = logging.getLogger(__name__)

# ── Custom Exceptions ────────────────────────────────────────────────────────

class ServiceError(Exception):
    """Base exception for all service errors."""
    pass

class DatabaseError(ServiceError):
    """Raised when a database operation fails."""
    pass

class ValidationError(ServiceError):
    """Raised when input validation fails."""
    pass

class AuthenticationError(ServiceError):
    """Raised when authentication fails."""
    pass

class AuthorizationError(ServiceError):
    """Raised when authorization check fails."""
    pass

# ── Enums ────────────────────────────────────────────────────────────────────

class UserRole(Enum):
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"
    READONLY = "readonly"

class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

# ── Database Pool ────────────────────────────────────────────────────────────

class DatabasePool:
    """Simple connection pool for SQLite."""

    def __init__(self, db_path: str = DB_PATH, max_size: int = MAX_POOL_SIZE):
        self.db_path = db_path
        self.max_size = max_size
        self._pool: List[sqlite3.Connection] = []
        self._in_use: int = 0
        logger.info(f"DatabasePool initialized: path={db_path}, max_size={max_size}")

    def acquire(self) -> sqlite3.Connection:
        """Acquire a connection from the pool."""
        if self._pool:
            conn = self._pool.pop()
            self._in_use += 1
            return conn
        if self._in_use < self.max_size:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            self._in_use += 1
            return conn
        raise DatabaseError("Connection pool exhausted")

    def release(self, conn: sqlite3.Connection) -> None:
        """Return a connection to the pool."""
        self._in_use -= 1
        if len(self._pool) < self.max_size:
            self._pool.append(conn)
        else:
            conn.close()

    def close_all(self) -> None:
        """Close all pooled connections."""
        for conn in self._pool:
            conn.close()
        self._pool.clear()
        logger.info("All pooled connections closed")


# ── User Service ─────────────────────────────────────────────────────────────

class UserService:
    """Handles user CRUD, authentication, and search."""

    def __init__(self, pool: DatabasePool):
        self.pool = pool

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a single user by ID."""
        conn = self.pool.acquire()
        try:
            cursor = conn.execute(
                "SELECT id, username, email, role, created_at, updated_at "
                "FROM users WHERE id = ?",
                (user_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return dict(row)
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to fetch user {user_id}: {e}")
        finally:
            self.pool.release(conn)

    def create_user(
        self, username: str, email: str, password: str, role: UserRole = UserRole.USER
    ) -> Dict[str, Any]:
        """Create a new user account."""
        validate_email(email)
        validate_password(password)
        if not username or len(username) < 3:
            raise ValidationError("Username must be at least 3 characters")

        password_hash = hash_password(password)
        conn = self.pool.acquire()
        try:
            cursor = conn.execute(
                "INSERT INTO users (username, email, password_hash, role, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (username, email, password_hash, role.value, datetime.utcnow().isoformat(),
                 datetime.utcnow().isoformat()),
            )
            conn.commit()
            return {"id": cursor.lastrowid, "username": username, "email": email, "role": role.value}
        except sqlite3.IntegrityError:
            raise ValidationError(f"Username '{username}' or email '{email}' already exists")
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to create user: {e}")
        finally:
            self.pool.release(conn)

    def delete_user(self, user_id: int) -> bool:
        """Soft-delete a user account."""
        conn = self.pool.acquire()
        try:
            cursor = conn.execute(
                "UPDATE users SET deleted_at = ?, updated_at = ? WHERE id = ? AND deleted_at IS NULL",
                (datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), user_id),
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to delete user {user_id}: {e}")
        finally:
            self.pool.release(conn)

    def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user and return a session token."""
        conn = self.pool.acquire()
        try:
            cursor = conn.execute(
                "SELECT id, username, email, password_hash, role, login_attempts, locked_until "
                "FROM users WHERE username = ? AND deleted_at IS NULL",
                (username,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            user = dict(row)

            if user.get("locked_until"):
                locked_until = datetime.fromisoformat(user["locked_until"])
                if datetime.utcnow() < locked_until:
                    raise AuthenticationError(
                        f"Account locked until {locked_until.isoformat()}"
                    )
                conn.execute(
                    "UPDATE users SET login_attempts = 0, locked_until = NULL WHERE id = ?",
                    (user["id"],),
                )

            if not verify_password(password, user["password_hash"]):
                attempts = (user.get("login_attempts") or 0) + 1
                updates = {"login_attempts": attempts}
                if attempts >= MAX_LOGIN_ATTEMPTS:
                    lockout = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                    updates["locked_until"] = lockout.isoformat()
                conn.execute(
                    "UPDATE users SET login_attempts = ?, locked_until = ? WHERE id = ?",
                    (updates["login_attempts"], updates.get("locked_until"), user["id"]),
                )
                conn.commit()
                return None

            token = generate_session_token()
            expiry = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS)
            conn.execute(
                "INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, ?)",
                (user["id"], token, expiry.isoformat()),
            )
            conn.execute(
                "UPDATE users SET login_attempts = 0, locked_until = NULL, "
                "last_login = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), user["id"]),
            )
            conn.commit()
            return {"user_id": user["id"], "token": token, "expires_at": expiry.isoformat()}
        except sqlite3.Error as e:
            raise DatabaseError(f"Authentication failed: {e}")
        finally:
            self.pool.release(conn)

    def search_users(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search users by username or email."""
        conn = self.pool.acquire()
        try:
            like_pattern = f"%{query}%"
            cursor = conn.execute(
                "SELECT id, username, email, role, created_at FROM users "
                "WHERE (username LIKE ? OR email LIKE ?) "
                "AND deleted_at IS NULL LIMIT ?",
                (like_pattern, like_pattern, limit),
            )
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise DatabaseError(f"Search failed: {e}")
        finally:
            self.pool.release(conn)

    def update_user(self, user_id: int, **kwargs) -> Optional[Dict[str, Any]]:
        """Update user fields."""
        allowed = {"username", "email", "role"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            raise ValidationError("No valid fields to update")
        if "email" in updates:
            validate_email(updates["email"])

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [datetime.utcnow().isoformat(), user_id]

        conn = self.pool.acquire()
        try:
            conn.execute(
                f"UPDATE users SET {set_clause}, updated_at = ? WHERE id = ? AND deleted_at IS NULL",
                values,
            )
            conn.commit()
            return self.get_user(user_id)
        except sqlite3.IntegrityError:
            raise ValidationError("Username or email already taken")
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to update user {user_id}: {e}")
        finally:
            self.pool.release(conn)

    def list_users(self, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE,
                   role: Optional[UserRole] = None) -> Dict[str, Any]:
        """List users with pagination and optional role filter."""
        page_size = min(page_size, MAX_PAGE_SIZE)
        offset = (page - 1) * page_size

        conn = self.pool.acquire()
        try:
            where = "WHERE deleted_at IS NULL"
            params: list = []
            if role:
                where += " AND role = ?"
                params.append(role.value)

            count_cursor = conn.execute(f"SELECT COUNT(*) FROM users {where}", params)
            total = count_cursor.fetchone()[0]

            params.extend([page_size, offset])
            cursor = conn.execute(
                f"SELECT id, username, email, role, created_at FROM users {where} "
                f"ORDER BY created_at DESC LIMIT ? OFFSET ?",
                params,
            )
            users = [dict(row) for row in cursor.fetchall()]
            return {
                "users": users,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
            }
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to list users: {e}")
        finally:
            self.pool.release(conn)


# ── Order Service ────────────────────────────────────────────────────────────

class OrderService:
    """Handles order CRUD and lifecycle management."""

    def __init__(self, pool: DatabasePool):
        self.pool = pool

    def create_order(self, user_id: int, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a new order for a user."""
        if not items:
            raise ValidationError("Order must contain at least one item")

        total = sum(item["price"] * item["quantity"] for item in items)
        order_number = generate_order_number()

        conn = self.pool.acquire()
        try:
            cursor = conn.execute(
                "INSERT INTO orders (user_id, order_number, total, status, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, order_number, total, OrderStatus.PENDING.value,
                 datetime.utcnow().isoformat(), datetime.utcnow().isoformat()),
            )
            order_id = cursor.lastrowid
            for item in items:
                conn.execute(
                    "INSERT INTO order_items (order_id, product_id, product_name, price, quantity) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (order_id, item["product_id"], item["product_name"],
                     item["price"], item["quantity"]),
                )
            conn.commit()
            return {
                "id": order_id, "order_number": order_number,
                "total": total, "status": OrderStatus.PENDING.value,
                "items": items,
            }
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to create order: {e}")
        finally:
            self.pool.release(conn)

    def get_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a single order with its items."""
        conn = self.pool.acquire()
        try:
            cursor = conn.execute(
                "SELECT id, user_id, order_number, total, status, created_at, updated_at "
                "FROM orders WHERE id = ?",
                (order_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            order = dict(row)
            items_cursor = conn.execute(
                "SELECT product_id, product_name, price, quantity "
                "FROM order_items WHERE order_id = ?",
                (order_id,),
            )
            order["items"] = [dict(r) for r in items_cursor.fetchall()]
            return order
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to fetch order {order_id}: {e}")
        finally:
            self.pool.release(conn)

    def list_orders(self, user_id: int, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE,
                    status: Optional[OrderStatus] = None) -> Dict[str, Any]:
        """List orders for a user with pagination."""
        page_size = min(page_size, MAX_PAGE_SIZE)
        offset = (page - 1) * page_size

        conn = self.pool.acquire()
        try:
            where = "WHERE user_id = ?"
            params: list = [user_id]
            if status:
                where += " AND status = ?"
                params.append(status.value)

            count_cursor = conn.execute(f"SELECT COUNT(*) FROM orders {where}", params)
            total = count_cursor.fetchone()[0]

            params.extend([page_size, offset])
            cursor = conn.execute(
                f"SELECT id, order_number, total, status, created_at "
                f"FROM orders {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
                params,
            )
            orders = [dict(row) for row in cursor.fetchall()]
            return {
                "orders": orders,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
            }
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to list orders: {e}")
        finally:
            self.pool.release(conn)

    def update_order_status(self, order_id: int, new_status: OrderStatus) -> Optional[Dict[str, Any]]:
        """Update the status of an order with transition validation."""
        order = self.get_order(order_id)
        if order is None:
            return None

        current = OrderStatus(order["status"])
        valid_transitions = {
            OrderStatus.PENDING: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
            OrderStatus.CONFIRMED: {OrderStatus.PROCESSING, OrderStatus.CANCELLED},
            OrderStatus.PROCESSING: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
            OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
            OrderStatus.DELIVERED: {OrderStatus.REFUNDED},
            OrderStatus.CANCELLED: set(),
            OrderStatus.REFUNDED: set(),
        }
        if new_status not in valid_transitions.get(current, set()):
            raise ValidationError(
                f"Cannot transition from {current.value} to {new_status.value}"
            )

        conn = self.pool.acquire()
        try:
            conn.execute(
                "UPDATE orders SET status = ?, updated_at = ? WHERE id = ?",
                (new_status.value, datetime.utcnow().isoformat(), order_id),
            )
            conn.execute(
                "INSERT INTO order_status_history (order_id, old_status, new_status, changed_at) "
                "VALUES (?, ?, ?, ?)",
                (order_id, current.value, new_status.value, datetime.utcnow().isoformat()),
            )
            conn.commit()
            return self.get_order(order_id)
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to update order status: {e}")
        finally:
            self.pool.release(conn)

    def cancel_order(self, order_id: int, reason: str = "") -> Optional[Dict[str, Any]]:
        """Cancel an order with an optional reason."""
        result = self.update_order_status(order_id, OrderStatus.CANCELLED)
        if result and reason:
            conn = self.pool.acquire()
            try:
                conn.execute(
                    "UPDATE orders SET cancellation_reason = ? WHERE id = ?",
                    (reason, order_id),
                )
                conn.commit()
            except sqlite3.Error:
                pass
            finally:
                self.pool.release(conn)
        return result

    def get_order_stats(self, user_id: int) -> Dict[str, Any]:
        """Get order statistics for a user."""
        conn = self.pool.acquire()
        try:
            cursor = conn.execute(
                "SELECT status, COUNT(*) as count, SUM(total) as total_amount "
                "FROM orders WHERE user_id = ? GROUP BY status",
                (user_id,),
            )
            stats = {}
            for row in cursor.fetchall():
                stats[row["status"]] = {
                    "count": row["count"],
                    "total_amount": row["total_amount"] or 0,
                }
            total_cursor = conn.execute(
                "SELECT COUNT(*) as total_orders, SUM(total) as lifetime_total "
                "FROM orders WHERE user_id = ?",
                (user_id,),
            )
            totals = dict(total_cursor.fetchone())
            return {
                "by_status": stats,
                "total_orders": totals["total_orders"],
                "lifetime_total": totals["lifetime_total"] or 0,
            }
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get order stats: {e}")
        finally:
            self.pool.release(conn)


# ── Helper Functions ─────────────────────────────────────────────────────────

def validate_email(email: str) -> None:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValidationError(f"Invalid email format: {email}")


def validate_password(password: str) -> None:
    """Validate password strength."""
    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValidationError(
            f"Password must be at least {PASSWORD_MIN_LENGTH} characters"
        )
    if not re.search(r'[A-Z]', password):
        raise ValidationError("Password must contain at least one uppercase letter")
    if not re.search(r'[a-z]', password):
        raise ValidationError("Password must contain at least one lowercase letter")
    if not re.search(r'[0-9]', password):
        raise ValidationError("Password must contain at least one digit")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValidationError("Password must contain at least one special character")


def hash_password(password: str) -> str:
    """Hash a password with a random salt using PBKDF2."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
    )
    return f"{salt}:{key.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a stored hash."""
    try:
        salt, key_hex = password_hash.split(":")
        expected_key = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
        )
        return hmac.compare_digest(expected_key, bytes.fromhex(key_hex))
    except (ValueError, TypeError):
        return False


def generate_session_token() -> str:
    """Generate a secure random session token."""
    return secrets.token_urlsafe(32)


def generate_order_number() -> str:
    """Generate a unique order number."""
    timestamp = int(time.time() * 1000)
    random_part = secrets.token_hex(4)
    return f"ORD-{timestamp}-{random_part}"


def parse_config(config_path: str) -> Dict[str, Any]:
    """Parse a JSON configuration file."""
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        required_keys = ["database", "server", "logging"]
        for key in required_keys:
            if key not in config:
                raise ValidationError(f"Missing required config key: {key}")
        return config
    except FileNotFoundError:
        raise ServiceError(f"Configuration file not found: {config_path}")
    except json.JSONDecodeError as e:
        raise ServiceError(f"Invalid JSON in config file: {e}")


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input by stripping dangerous characters."""
    text = text.strip()
    text = text[:max_length]
    text = re.sub(r'[<>";]', '', text)
    return text


def format_currency(amount: float, currency: str = "USD") -> str:
    """Format a numeric amount as currency."""
    symbols = {"USD": "$", "EUR": "\u20ac", "GBP": "\u00a3", "JPY": "\u00a5"}
    symbol = symbols.get(currency, currency + " ")
    if currency == "JPY":
        return f"{symbol}{int(amount):,}"
    return f"{symbol}{amount:,.2f}"


def calculate_tax(subtotal: float, tax_rate: float = 0.08) -> Dict[str, float]:
    """Calculate tax and total for a given subtotal."""
    tax = round(subtotal * tax_rate, 2)
    total = round(subtotal + tax, 2)
    return {"subtotal": subtotal, "tax": tax, "total": total, "tax_rate": tax_rate}


def paginate_results(items: list, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> Dict[str, Any]:
    """Generic pagination helper."""
    page_size = min(page_size, MAX_PAGE_SIZE)
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": items[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "has_next": end < total,
        "has_prev": page > 1,
    }


def build_where_clause(filters: Dict[str, Any]) -> Tuple[str, list]:
    """Build a SQL WHERE clause from a dictionary of filters."""
    conditions = []
    params = []
    for key, value in filters.items():
        if value is None:
            continue
        if isinstance(value, list):
            placeholders = ", ".join("?" for _ in value)
            conditions.append(f"{key} IN ({placeholders})")
            params.extend(value)
        elif isinstance(value, str) and "%" in value:
            conditions.append(f"{key} LIKE ?")
            params.append(value)
        else:
            conditions.append(f"{key} = ?")
            params.append(value)
    where = " AND ".join(conditions) if conditions else "1=1"
    return where, params


# ── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class Address:
    """Mailing address model."""
    street: str
    city: str
    state: str
    zip_code: str
    country: str = "US"

    def validate(self) -> None:
        if not self.street:
            raise ValidationError("Street is required")
        if not self.city:
            raise ValidationError("City is required")
        if not re.match(r'^\d{5}(-\d{4})?$', self.zip_code):
            raise ValidationError(f"Invalid ZIP code: {self.zip_code}")

    def to_dict(self) -> Dict[str, str]:
        return {
            "street": self.street, "city": self.city,
            "state": self.state, "zip_code": self.zip_code,
            "country": self.country,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "Address":
        return cls(
            street=data.get("street", ""),
            city=data.get("city", ""),
            state=data.get("state", ""),
            zip_code=data.get("zip_code", ""),
            country=data.get("country", "US"),
        )


@dataclass
class PaymentInfo:
    """Payment information model (tokenized, no raw card data)."""
    token: str
    last_four: str
    card_type: str
    expiry_month: int
    expiry_year: int
    billing_address: Optional[Address] = None

    def validate(self) -> None:
        if not self.token:
            raise ValidationError("Payment token is required")
        if len(self.last_four) != 4 or not self.last_four.isdigit():
            raise ValidationError("Invalid last four digits")
        if self.card_type not in ("visa", "mastercard", "amex", "discover"):
            raise ValidationError(f"Unsupported card type: {self.card_type}")
        if self.expiry_month < 1 or self.expiry_month > 12:
            raise ValidationError("Invalid expiry month")
        current_year = datetime.utcnow().year
        if self.expiry_year < current_year:
            raise ValidationError("Card has expired")
        if self.billing_address:
            self.billing_address.validate()

    def is_expired(self) -> bool:
        now = datetime.utcnow()
        if self.expiry_year < now.year:
            return True
        if self.expiry_year == now.year and self.expiry_month < now.month:
            return True
        return False


@dataclass
class OrderItem:
    """Individual item in an order."""
    product_id: int
    product_name: str
    price: float
    quantity: int

    def validate(self) -> None:
        if self.price < 0:
            raise ValidationError("Price cannot be negative")
        if self.quantity < 1:
            raise ValidationError("Quantity must be at least 1")

    @property
    def subtotal(self) -> float:
        return round(self.price * self.quantity, 2)


@dataclass
class ShippingInfo:
    """Shipping details for an order."""
    method: str
    address: Address
    tracking_number: Optional[str] = None
    estimated_delivery: Optional[str] = None
    cost: float = 0.0

    def validate(self) -> None:
        valid_methods = ("standard", "express", "overnight", "pickup")
        if self.method not in valid_methods:
            raise ValidationError(f"Invalid shipping method: {self.method}")
        self.address.validate()
        if self.cost < 0:
            raise ValidationError("Shipping cost cannot be negative")


# ── API Route Handlers ───────────────────────────────────────────────────────

class RequestHandler:
    """Simple request handler mapping routes to service methods."""

    def __init__(self, user_service: UserService, order_service: OrderService):
        self.user_service = user_service
        self.order_service = order_service
        self.routes = {
            "GET /users": self.handle_list_users,
            "GET /users/{id}": self.handle_get_user,
            "POST /users": self.handle_create_user,
            "PUT /users/{id}": self.handle_update_user,
            "DELETE /users/{id}": self.handle_delete_user,
            "GET /users/search": self.handle_search_users,
            "POST /auth/login": self.handle_login,
            "GET /orders": self.handle_list_orders,
            "GET /orders/{id}": self.handle_get_order,
            "POST /orders": self.handle_create_order,
            "PUT /orders/{id}/status": self.handle_update_order_status,
            "DELETE /orders/{id}": self.handle_cancel_order,
            "GET /orders/stats": self.handle_order_stats,
        }

    def handle_request(self, method: str, path: str, body: Optional[Dict] = None,
                       query: Optional[Dict] = None, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Route a request to the appropriate handler."""
        route_key = f"{method} {path}"
        for pattern, handler in self.routes.items():
            if self._match_route(pattern, route_key):
                try:
                    return {"status": 200, "data": handler(body=body, query=query, user_id=user_id)}
                except ValidationError as e:
                    return {"status": 400, "error": str(e)}
                except AuthenticationError as e:
                    return {"status": 401, "error": str(e)}
                except AuthorizationError as e:
                    return {"status": 403, "error": str(e)}
                except DatabaseError as e:
                    logger.error(f"Database error: {e}")
                    return {"status": 500, "error": "Internal server error"}
        return {"status": 404, "error": f"Route not found: {route_key}"}

    def _match_route(self, pattern: str, route: str) -> bool:
        """Simple route pattern matching."""
        pattern_parts = pattern.split("/")
        route_parts = route.split("/")
        if len(pattern_parts) != len(route_parts):
            return False
        for p, r in zip(pattern_parts, route_parts):
            if p.startswith("{") and p.endswith("}"):
                continue
            if p != r:
                return False
        return True

    def handle_list_users(self, **kwargs) -> Dict:
        query = kwargs.get("query") or {}
        return self.user_service.list_users(
            page=int(query.get("page", 1)),
            page_size=int(query.get("page_size", DEFAULT_PAGE_SIZE)),
        )

    def handle_get_user(self, **kwargs) -> Dict:
        user_id = kwargs.get("user_id")
        result = self.user_service.get_user(user_id)
        if result is None:
            raise ValidationError("User not found")
        return result

    def handle_create_user(self, **kwargs) -> Dict:
        body = kwargs.get("body") or {}
        return self.user_service.create_user(
            username=body["username"], email=body["email"],
            password=body["password"], role=UserRole(body.get("role", "user")),
        )

    def handle_update_user(self, **kwargs) -> Dict:
        user_id = kwargs.get("user_id")
        body = kwargs.get("body") or {}
        result = self.user_service.update_user(user_id, **body)
        if result is None:
            raise ValidationError("User not found")
        return result

    def handle_delete_user(self, **kwargs) -> Dict:
        user_id = kwargs.get("user_id")
        if not self.user_service.delete_user(user_id):
            raise ValidationError("User not found")
        return {"deleted": True}

    def handle_search_users(self, **kwargs) -> Dict:
        query = kwargs.get("query") or {}
        return {"users": self.user_service.search_users(
            query=query.get("q", ""), limit=int(query.get("limit", 20)),
        )}

    def handle_login(self, **kwargs) -> Dict:
        body = kwargs.get("body") or {}
        result = self.user_service.authenticate(body["username"], body["password"])
        if result is None:
            raise AuthenticationError("Invalid credentials")
        return result

    def handle_list_orders(self, **kwargs) -> Dict:
        query = kwargs.get("query") or {}
        user_id = kwargs.get("user_id")
        return self.order_service.list_orders(
            user_id=user_id, page=int(query.get("page", 1)),
            page_size=int(query.get("page_size", DEFAULT_PAGE_SIZE)),
        )

    def handle_get_order(self, **kwargs) -> Dict:
        order_id = kwargs.get("user_id")
        result = self.order_service.get_order(order_id)
        if result is None:
            raise ValidationError("Order not found")
        return result

    def handle_create_order(self, **kwargs) -> Dict:
        body = kwargs.get("body") or {}
        user_id = kwargs.get("user_id")
        return self.order_service.create_order(user_id=user_id, items=body.get("items", []))

    def handle_update_order_status(self, **kwargs) -> Dict:
        order_id = kwargs.get("user_id")
        body = kwargs.get("body") or {}
        result = self.order_service.update_order_status(
            order_id=order_id, new_status=OrderStatus(body["status"]),
        )
        if result is None:
            raise ValidationError("Order not found")
        return result

    def handle_cancel_order(self, **kwargs) -> Dict:
        order_id = kwargs.get("user_id")
        body = kwargs.get("body") or {}
        result = self.order_service.cancel_order(
            order_id=order_id, reason=body.get("reason", ""),
        )
        if result is None:
            raise ValidationError("Order not found")
        return result

    def handle_order_stats(self, **kwargs) -> Dict:
        user_id = kwargs.get("user_id")
        return self.order_service.get_order_stats(user_id=user_id)


# ── Database Initialization ──────────────────────────────────────────────────

def init_database(pool: DatabasePool) -> None:
    """Initialize database tables."""
    conn = pool.acquire()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                login_attempts INTEGER DEFAULT 0,
                locked_until TEXT,
                last_login TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                deleted_at TEXT
            );
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                order_number TEXT UNIQUE NOT NULL,
                total REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                cancellation_reason TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id)
            );
            CREATE TABLE IF NOT EXISTS order_status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                old_status TEXT NOT NULL,
                new_status TEXT NOT NULL,
                changed_at TEXT NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id)
            );
            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
            CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
            CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
        """)
        pool.release(conn)
        logger.info("Database tables initialized")
    except sqlite3.Error as e:
        pool.release(conn)
        raise DatabaseError(f"Failed to initialize database: {e}")


# ── Main Entry Point ─────────────────────────────────────────────────────────

def create_app() -> RequestHandler:
    """Create and configure the application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    pool = DatabasePool()
    init_database(pool)
    user_service = UserService(pool)
    order_service = OrderService(pool)
    handler = RequestHandler(user_service, order_service)
    logger.info("Application initialized")
    return handler


if __name__ == "__main__":
    app = create_app()
    print("Service ready. Use handle_request() to process requests.")
```

</details>

### SkillOS + strict-patch Output

<details>
<summary>Click to expand (224 output tokens)</summary>

```
[FILE] service.py
[DEL:247]                 f"SELECT id, username, email, role, created_at FROM users "
[ADD:247]                 "SELECT id, username, email, role, created_at FROM users "
[DEL:248]                 f"WHERE (username LIKE '%{query}%' OR email LIKE '%{query}%') "
[ADD:248]                 "WHERE (username LIKE '%' || ? || '%' OR email LIKE '%' || ? || '%') "
[DEL:249]                 f"AND deleted_at IS NULL LIMIT {limit}",
[ADD:249]                 "AND deleted_at IS NULL LIMIT ?",
[ADD:250]                 (query, query, limit),
[DEL:393]         offset = page * page_size
[ADD:393]         offset = (page - 1) * page_size
[EOF]
```

</details>
