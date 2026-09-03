"""002_location_hierarchy

Revision ID: 002_location_hierarchy
Revises: 001_initial_schema
Create Date: 2026-09-03 06:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_location_hierarchy'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. states
    op.create_table(
        'states',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('code', sa.String(10), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_states_id', 'states', ['id'])
    op.create_index('ix_states_name', 'states', ['name'], unique=True)
    op.create_index('ix_states_code', 'states', ['code'], unique=True)

    # 2. districts
    op.create_table(
        'districts',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('state_id', sa.Integer(), sa.ForeignKey('states.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('code', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_districts_id', 'districts', ['id'])
    op.create_index('ix_districts_state_id', 'districts', ['state_id'])
    op.create_index('ix_districts_name', 'districts', ['name'])

    # 3. Add columns to healthcare_centres
    op.add_column('healthcare_centres', sa.Column('district_id', sa.Integer(), sa.ForeignKey('districts.id'), nullable=True))
    op.add_column('healthcare_centres', sa.Column('facility_type', sa.String(50), nullable=False, server_default='PHC'))
    op.add_column('healthcare_centres', sa.Column('address', sa.Text(), nullable=True))
    op.add_column('healthcare_centres', sa.Column('pincode', sa.String(20), nullable=True))
    op.add_column('healthcare_centres', sa.Column('status', sa.String(50), nullable=False, server_default='ACTIVE'))
    op.create_index('ix_healthcare_centres_district_id', 'healthcare_centres', ['district_id'])
    op.alter_column('healthcare_centres', 'location_id', existing_type=sa.Integer(), nullable=True)

    # 4. Add columns to hospitals
    op.add_column('hospitals', sa.Column('district_id', sa.Integer(), sa.ForeignKey('districts.id'), nullable=True))
    op.add_column('hospitals', sa.Column('facility_type', sa.String(50), nullable=False, server_default='SPECIALTY_EYE_HOSPITAL'))
    op.add_column('hospitals', sa.Column('pincode', sa.String(20), nullable=True))
    op.add_column('hospitals', sa.Column('registration_reference', sa.String(100), nullable=True))
    op.add_column('hospitals', sa.Column('status', sa.String(50), nullable=False, server_default='VERIFIED'))
    op.create_index('ix_hospitals_district_id', 'hospitals', ['district_id'])
    op.create_index('ix_hospitals_status', 'hospitals', ['status'])
    op.alter_column('hospitals', 'location_id', existing_type=sa.Integer(), nullable=True)
    op.alter_column('hospitals', 'address', existing_type=sa.Text(), nullable=True)
    op.alter_column('hospitals', 'contact', existing_type=sa.String(100), nullable=True)

    # 5. Add columns to healthcare_workers
    op.add_column('healthcare_workers', sa.Column('state_id', sa.Integer(), sa.ForeignKey('states.id'), nullable=True))
    op.add_column('healthcare_workers', sa.Column('district_id', sa.Integer(), sa.ForeignKey('districts.id'), nullable=True))
    op.create_index('ix_healthcare_workers_state_id', 'healthcare_workers', ['state_id'])
    op.create_index('ix_healthcare_workers_district_id', 'healthcare_workers', ['district_id'])

    # 6. Add columns to doctors
    op.add_column('doctors', sa.Column('state_id', sa.Integer(), sa.ForeignKey('states.id'), nullable=True))
    op.add_column('doctors', sa.Column('district_id', sa.Integer(), sa.ForeignKey('districts.id'), nullable=True))
    op.create_index('ix_doctors_state_id', 'doctors', ['state_id'])
    op.create_index('ix_doctors_district_id', 'doctors', ['district_id'])

    # 7. Add columns to users
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('users', 'email_verified')
    op.drop_column('doctors', 'district_id')
    op.drop_column('doctors', 'state_id')
    op.drop_column('healthcare_workers', 'district_id')
    op.drop_column('healthcare_workers', 'state_id')
    op.drop_column('hospitals', 'status')
    op.drop_column('hospitals', 'registration_reference')
    op.drop_column('hospitals', 'pincode')
    op.drop_column('hospitals', 'facility_type')
    op.drop_column('hospitals', 'district_id')
    op.drop_column('healthcare_centres', 'status')
    op.drop_column('healthcare_centres', 'pincode')
    op.drop_column('healthcare_centres', 'address')
    op.drop_column('healthcare_centres', 'facility_type')
    op.drop_column('healthcare_centres', 'district_id')
    op.drop_table('districts')
    op.drop_table('states')
