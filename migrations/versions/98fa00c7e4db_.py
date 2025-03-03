"""empty message

Revision ID: 98fa00c7e4db
Revises: 35d9a2cf9d34
Create Date: 2025-03-04 07:41:47.207730

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '98fa00c7e4db'
down_revision = '35d9a2cf9d34'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Reminders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('pronote_id', sa.Integer(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Reminders', schema=None) as batch_op:
        batch_op.drop_column('pronote_id')

    # ### end Alembic commands ###
