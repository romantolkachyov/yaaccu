"""initial

Revision ID: d1d0e8ca1b9e
Revises: 
Create Date: 2020-12-20 20:22:23.924294

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd1d0e8ca1b9e'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('accounts',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('address', sa.Unicode(), nullable=True),
        sa.Column('pub_key', sa.Unicode(), nullable=True),
        sa.Column('type', sa.Enum('active', 'passive', 'normal', name='account_type'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_accounts_address'), 'accounts', ['address'], unique=True)
    op.create_index(op.f('ix_accounts_pub_key'), 'accounts', ['pub_key'], unique=True)
    op.create_table('currencies',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('name', sa.Unicode(), nullable=True),
        sa.Column('symbol', sa.Unicode(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_currencies_symbol'), 'currencies', ['symbol'], unique=True)
    op.create_table('documents',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('committed', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('operations',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('document', sa.BigInteger(), nullable=True),
        sa.Column('account', sa.BigInteger(), nullable=True),
        sa.Column('currency', sa.BigInteger(), nullable=True),
        sa.Column('amount', sa.Numeric(precision=16, scale=4), nullable=True),
        sa.ForeignKeyConstraint(['account'], ['accounts.id'], ),
        sa.ForeignKeyConstraint(['currency'], ['currencies.id'], ),
        sa.ForeignKeyConstraint(['document'], ['documents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_index(op.f('ix_currencies_symbol'), table_name='currencies')
    op.drop_index(op.f('ix_accounts_pub_key'), table_name='accounts')
    op.drop_index(op.f('ix_accounts_address'), table_name='accounts')
    op.drop_table('operations')
    op.drop_table('documents')
    op.drop_table('currencies')
    op.drop_table('accounts')
    op.execute('DROP TYPE account_type')
