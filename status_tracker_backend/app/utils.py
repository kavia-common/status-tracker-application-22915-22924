from math import ceil
from flask import request
from flask_jwt_extended import get_jwt
from werkzeug.exceptions import Forbidden


def paginate_query(query, default_size=10, max_size=50):
    """Paginate a SQLAlchemy query based on request args page and size."""
    try:
        page = int(request.args.get("page", "1"))
    except ValueError:
        page = 1
    try:
        size = int(request.args.get("size", str(default_size)))
    except ValueError:
        size = default_size
    size = min(max(1, size), max_size)

    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    total_pages = ceil(total / size) if size else 1
    meta = {
        "total": total,
        "total_pages": total_pages,
        "first_page": 1,
        "last_page": total_pages,
        "page": page,
        "previous_page": page - 1 if page > 1 else None,
        "next_page": page + 1 if page < total_pages else None,
    }
    return items, meta


def require_admin():
    """Raise Forbidden if current JWT is not admin."""
    claims = get_jwt()
    if not claims.get("is_admin"):
        raise Forbidden("Admin privileges required.")
