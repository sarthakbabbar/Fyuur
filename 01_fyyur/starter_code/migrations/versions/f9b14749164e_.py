"""empty message

Revision ID: f9b14749164e
Revises: 6261a9010df4
Create Date: 2020-10-28 23:38:37.116818

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f9b14749164e'
down_revision = '6261a9010df4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Artist', sa.Column('website', sa.String(length=120), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Artist', 'website')
    # ### end Alembic commands ###