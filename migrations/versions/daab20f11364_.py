"""empty message

Revision ID: daab20f11364
Revises: 2f7d61ee22d7
Create Date: 2023-03-28 09:34:24.157145

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'daab20f11364'
down_revision = '2f7d61ee22d7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('timezone_offset', sa.Integer(), nullable=True))
        batch_op.drop_column('registration_date')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('registration_date', mysql.VARCHAR(length=100), nullable=True))
        batch_op.drop_column('timezone_offset')

    # ### end Alembic commands ###