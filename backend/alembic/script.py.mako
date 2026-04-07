"""${message}

Revision ID: ${up_revision}
Reverts:     ${down_revision | comma,n}
Branch labels: ${branch_labels | comma,n}
Depends on:  ${depends_on | comma,n}
Created:     ${create_date}
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2
${imports if imports else ""}

# Identificadores da revision
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    """Aplica as alterações desta migration."""
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """Reverte as alterações desta migration."""
    ${downgrades if downgrades else "pass"}
