"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-03-17
"""
from alembic import op
import sqlalchemy as sa

revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'trades',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('ticker', sa.String(length=16), nullable=False),
        sa.Column('side', sa.String(length=8), nullable=False),
        sa.Column('qty', sa.Float(), nullable=False),
        sa.Column('order_type', sa.String(length=16), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('stop_loss', sa.Float(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_trades_ticker', 'trades', ['ticker'])

    op.create_table(
        'signals',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('ticker', sa.String(length=16), nullable=False),
        sa.Column('recommendation', sa.String(length=16), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_signals_ticker', 'signals', ['ticker'])

    op.create_table(
        'portfolio_snapshots',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('equity', sa.Float(), nullable=False),
        sa.Column('cash', sa.Float(), nullable=False),
        sa.Column('positions', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('portfolio_snapshots')
    op.drop_index('ix_signals_ticker', table_name='signals')
    op.drop_table('signals')
    op.drop_index('ix_trades_ticker', table_name='trades')
    op.drop_table('trades')
