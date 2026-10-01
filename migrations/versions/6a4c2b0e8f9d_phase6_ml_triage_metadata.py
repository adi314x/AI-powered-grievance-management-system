"""phase6 ml triage metadata

Revision ID: 6a4c2b0e8f9d
Revises: 13ea9c2201a0
Create Date: 2026-04-15 04:05:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6a4c2b0e8f9d'
down_revision = '13ea9c2201a0'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('grievances', schema=None) as batch_op:
        batch_op.add_column(sa.Column('prediction_confidence', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('prediction_source', sa.String(length=30), nullable=True))
        batch_op.add_column(sa.Column('requires_manual_triage', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('triage_reason', sa.Text(), nullable=True))

    op.create_table(
        'department_correction_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('grievance_id', sa.Integer(), nullable=False),
        sa.Column('predicted_department', sa.String(length=100), nullable=False),
        sa.Column('corrected_department', sa.String(length=100), nullable=False),
        sa.Column('prediction_confidence', sa.Float(), nullable=True),
        sa.Column('corrected_by_user_id', sa.Integer(), nullable=False),
        sa.Column('assigned_officer_id', sa.Integer(), nullable=True),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['assigned_officer_id'], ['users.id']),
        sa.ForeignKeyConstraint(['corrected_by_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['grievance_id'], ['grievances.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('department_correction_logs')

    with op.batch_alter_table('grievances', schema=None) as batch_op:
        batch_op.drop_column('triage_reason')
        batch_op.drop_column('requires_manual_triage')
        batch_op.drop_column('prediction_source')
        batch_op.drop_column('prediction_confidence')
