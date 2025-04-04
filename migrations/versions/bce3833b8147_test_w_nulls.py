"""Test w nulls

Revision ID: bce3833b8147
Revises: 
Create Date: 2025-01-12 04:21:50.275390

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bce3833b8147'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('cell')
    op.drop_table('returns_table')
    op.drop_table('column')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('column',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.VARCHAR(), nullable=False),
    sa.Column('returns_table_id', sa.INTEGER(), nullable=False),
    sa.Column('acds', sa.VARCHAR(), nullable=True),
    sa.ForeignKeyConstraint(['returns_table_id'], ['returns_table.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('returns_table',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.VARCHAR(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('cell',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('value', sa.VARCHAR(), nullable=False),
    sa.Column('color', sa.VARCHAR(), nullable=True),
    sa.Column('format', sa.VARCHAR(), nullable=True),
    sa.Column('column_id', sa.INTEGER(), nullable=False),
    sa.ForeignKeyConstraint(['column_id'], ['column.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###
