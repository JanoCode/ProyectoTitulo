import sqlalchemy as sa
from alembic import op

revision = "20261110_02"
down_revision = "20261015_01"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("settings", sa.Column(
        "gesture_control_side", sa.String(5), nullable=False, server_default="right"
    ))
    op.create_check_constraint("valid_gesture_control_side", "settings",
                               "gesture_control_side IN ('left', 'right')")


def downgrade():
    op.drop_constraint("valid_gesture_control_side", "settings", type_="check")
    op.drop_column("settings", "gesture_control_side")
