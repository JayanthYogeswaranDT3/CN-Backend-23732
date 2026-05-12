from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.db.session import get_db_session

DbSessionDep = Annotated[object, Depends(get_db_session)]
"
