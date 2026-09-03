"""001_initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-02 22:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('mobile', sa.String(50), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_login', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_role', 'users', ['role'])
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_mobile', 'users', ['mobile'])

    # 2. locations
    op.create_table(
        'locations',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('state', sa.String(100), nullable=False),
        sa.Column('district', sa.String(100), nullable=False),
        sa.Column('pincode', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_locations_id', 'locations', ['id'])
    op.create_index('ix_locations_state', 'locations', ['state'])
    op.create_index('ix_locations_district', 'locations', ['district'])

    # 3. healthcare_centres
    op.create_table(
        'healthcare_centres',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('location_id', sa.Integer(), sa.ForeignKey('locations.id'), nullable=False),
        sa.Column('centre_type', sa.String(50), nullable=False, server_default='PHC'),
        sa.Column('code', sa.String(50), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_healthcare_centres_id', 'healthcare_centres', ['id'])
    op.create_index('ix_healthcare_centres_name', 'healthcare_centres', ['name'])

    # 4. hospitals
    op.create_table(
        'hospitals',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('location_id', sa.Integer(), sa.ForeignKey('locations.id'), nullable=False),
        sa.Column('address', sa.Text(), nullable=False),
        sa.Column('contact', sa.String(100), nullable=False),
        sa.Column('speciality', sa.String(255), nullable=False),
        sa.Column('availability', sa.String(100), nullable=False),
        sa.Column('verification_status', sa.String(50), nullable=False, server_default='VERIFIED'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_hospitals_id', 'hospitals', ['id'])
    op.create_index('ix_hospitals_name', 'hospitals', ['name'])
    op.create_index('ix_hospitals_verification_status', 'hospitals', ['verification_status'])

    # 5. healthcare_workers
    op.create_table(
        'healthcare_workers',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('professional_id', sa.String(100), nullable=False, unique=True),
        sa.Column('healthcare_centre_id', sa.Integer(), sa.ForeignKey('healthcare_centres.id'), nullable=True),
        sa.Column('location_id', sa.Integer(), sa.ForeignKey('locations.id'), nullable=True),
        sa.Column('verification_status', sa.String(50), nullable=False, server_default='PENDING'),
        sa.Column('verification_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_healthcare_workers_id', 'healthcare_workers', ['id'])
    op.create_index('ix_healthcare_workers_professional_id', 'healthcare_workers', ['professional_id'])
    op.create_index('ix_healthcare_workers_verification_status', 'healthcare_workers', ['verification_status'])

    # 6. doctors
    op.create_table(
        'doctors',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('medical_reg_number', sa.String(100), nullable=False, unique=True),
        sa.Column('hospital_id', sa.Integer(), sa.ForeignKey('hospitals.id'), nullable=True),
        sa.Column('location_id', sa.Integer(), sa.ForeignKey('locations.id'), nullable=True),
        sa.Column('verification_status', sa.String(50), nullable=False, server_default='PENDING'),
        sa.Column('speciality', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_doctors_id', 'doctors', ['id'])
    op.create_index('ix_doctors_medical_reg_number', 'doctors', ['medical_reg_number'])
    op.create_index('ix_doctors_verification_status', 'doctors', ['verification_status'])

    # 7. patients
    op.create_table(
        'patients',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('patient_id', sa.String(50), nullable=False, unique=True),
        sa.Column('age', sa.Integer(), nullable=False),
        sa.Column('gender', sa.String(20), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by_worker_id', sa.Integer(), sa.ForeignKey('healthcare_workers.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_patients_id', 'patients', ['id'])
    op.create_index('ix_patients_patient_id', 'patients', ['patient_id'])

    # 8. screening_cases
    op.create_table(
        'screening_cases',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('case_id', sa.String(50), nullable=False, unique=True),
        sa.Column('patient_id', sa.Integer(), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('healthcare_worker_id', sa.Integer(), sa.ForeignKey('healthcare_workers.id'), nullable=False),
        sa.Column('healthcare_centre_id', sa.Integer(), sa.ForeignKey('healthcare_centres.id'), nullable=True),
        sa.Column('location_id', sa.Integer(), sa.ForeignKey('locations.id'), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='DRAFT'),
        sa.Column('referral_required', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_screening_cases_id', 'screening_cases', ['id'])
    op.create_index('ix_screening_cases_case_id', 'screening_cases', ['case_id'])
    op.create_index('ix_screening_cases_status', 'screening_cases', ['status'])

    # 9. screening_images
    op.create_table(
        'screening_images',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('case_id', sa.String(50), sa.ForeignKey('screening_cases.case_id'), nullable=False),
        sa.Column('object_key', sa.String(500), nullable=False),
        sa.Column('storage_type', sa.String(50), nullable=False, server_default='s3'),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False, server_default='image/jpeg'),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_screening_images_id', 'screening_images', ['id'])
    op.create_index('ix_screening_images_case_id', 'screening_images', ['case_id'])

    # 10. image_validations
    op.create_table(
        'image_validations',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('case_id', sa.String(50), sa.ForeignKey('screening_cases.case_id'), nullable=False, unique=True),
        sa.Column('is_fundus', sa.Boolean(), nullable=False),
        sa.Column('modality_status', sa.String(50), nullable=False),
        sa.Column('fundus_confidence', sa.Float(), nullable=False),
        sa.Column('color_score', sa.Float(), nullable=False),
        sa.Column('geometry_score', sa.Float(), nullable=False),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('validated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_image_validations_id', 'image_validations', ['id'])
    op.create_index('ix_image_validations_case_id', 'image_validations', ['case_id'])

    # 11. image_quality_assessments
    op.create_table(
        'image_quality_assessments',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('case_id', sa.String(50), sa.ForeignKey('screening_cases.case_id'), nullable=False, unique=True),
        sa.Column('quality_status', sa.String(50), nullable=False),
        sa.Column('quality_score', sa.Float(), nullable=False),
        sa.Column('is_gradeable', sa.Boolean(), nullable=False),
        sa.Column('blur_metric', sa.Float(), nullable=True),
        sa.Column('contrast_metric', sa.Float(), nullable=True),
        sa.Column('illumination_metric', sa.Float(), nullable=True),
        sa.Column('details_json', sa.Text(), nullable=True),
        sa.Column('assessed_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_image_quality_assessments_id', 'image_quality_assessments', ['id'])
    op.create_index('ix_image_quality_assessments_case_id', 'image_quality_assessments', ['case_id'])

    # 12. ai_predictions
    op.create_table(
        'ai_predictions',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('case_id', sa.String(50), sa.ForeignKey('screening_cases.case_id'), nullable=False, unique=True),
        sa.Column('model_version', sa.String(100), nullable=False),
        sa.Column('dr_stage', sa.Integer(), nullable=True),
        sa.Column('class_name', sa.String(255), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('probabilities_json', sa.Text(), nullable=True),
        sa.Column('gradcam_storage_key', sa.Text(), nullable=True),
        sa.Column('triage_decision', sa.Text(), nullable=False),
        sa.Column('priority', sa.String(50), nullable=False, server_default='ROUTINE'),
        sa.Column('is_uncertain', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_ai_predictions_id', 'ai_predictions', ['id'])
    op.create_index('ix_ai_predictions_case_id', 'ai_predictions', ['case_id'])

    # 13. lesion_findings
    op.create_table(
        'lesion_findings',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('case_id', sa.String(50), sa.ForeignKey('screening_cases.case_id'), nullable=False),
        sa.Column('lesion_type', sa.String(100), nullable=False),
        sa.Column('detected', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('area_pct', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.90'),
        sa.Column('mask_storage_key', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_lesion_findings_id', 'lesion_findings', ['id'])
    op.create_index('ix_lesion_findings_case_id', 'lesion_findings', ['case_id'])

    # 14. referrals
    op.create_table(
        'referrals',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('case_id', sa.String(50), sa.ForeignKey('screening_cases.case_id'), nullable=False, unique=True),
        sa.Column('hospital_id', sa.Integer(), sa.ForeignKey('hospitals.id'), nullable=False),
        sa.Column('doctor_id', sa.Integer(), sa.ForeignKey('doctors.id'), nullable=True),
        sa.Column('priority', sa.String(50), nullable=False, server_default='MEDIUM'),
        sa.Column('status', sa.String(50), nullable=False, server_default='PENDING'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_referrals_id', 'referrals', ['id'])
    op.create_index('ix_referrals_case_id', 'referrals', ['case_id'])
    op.create_index('ix_referrals_priority', 'referrals', ['priority'])
    op.create_index('ix_referrals_status', 'referrals', ['status'])

    # 15. doctor_reviews
    op.create_table(
        'doctor_reviews',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('case_id', sa.String(50), sa.ForeignKey('screening_cases.case_id'), nullable=False, unique=True),
        sa.Column('doctor_id', sa.Integer(), sa.ForeignKey('doctors.id'), nullable=False),
        sa.Column('referral_id', sa.Integer(), sa.ForeignKey('referrals.id'), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_doctor_reviews_id', 'doctor_reviews', ['id'])
    op.create_index('ix_doctor_reviews_case_id', 'doctor_reviews', ['case_id'])

    # 16. clinical_decisions
    op.create_table(
        'clinical_decisions',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('review_id', sa.Integer(), sa.ForeignKey('doctor_reviews.id'), nullable=True),
        sa.Column('case_id', sa.String(50), sa.ForeignKey('screening_cases.case_id'), nullable=False, unique=True),
        sa.Column('doctor_id', sa.Integer(), sa.ForeignKey('doctors.id'), nullable=False),
        sa.Column('decision_type', sa.String(50), nullable=False),
        sa.Column('original_dr_stage', sa.Integer(), nullable=False),
        sa.Column('final_dr_stage', sa.Integer(), nullable=False),
        sa.Column('final_severity', sa.String(255), nullable=False),
        sa.Column('clinical_notes', sa.Text(), nullable=False),
        sa.Column('treatment_plan', sa.Text(), nullable=True),
        sa.Column('follow_up_timeline', sa.String(255), nullable=True),
        sa.Column('decided_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_clinical_decisions_id', 'clinical_decisions', ['id'])
    op.create_index('ix_clinical_decisions_case_id', 'clinical_decisions', ['case_id'])

    # 17. reports
    op.create_table(
        'reports',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('case_id', sa.String(50), sa.ForeignKey('screening_cases.case_id'), nullable=False, unique=True),
        sa.Column('report_json', sa.Text(), nullable=False),
        sa.Column('pdf_storage_key', sa.String(500), nullable=True),
        sa.Column('generated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_reports_id', 'reports', ['id'])
    op.create_index('ix_reports_case_id', 'reports', ['case_id'])

    # 18. audit_logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('case_id', sa.String(50), nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_audit_logs_id', 'audit_logs', ['id'])
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_case_id', 'audit_logs', ['case_id'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('reports')
    op.drop_table('clinical_decisions')
    op.drop_table('doctor_reviews')
    op.drop_table('referrals')
    op.drop_table('lesion_findings')
    op.drop_table('ai_predictions')
    op.drop_table('image_quality_assessments')
    op.drop_table('image_validations')
    op.drop_table('screening_images')
    op.drop_table('screening_cases')
    op.drop_table('patients')
    op.drop_table('doctors')
    op.drop_table('healthcare_workers')
    op.drop_table('hospitals')
    op.drop_table('healthcare_centres')
    op.drop_table('locations')
    op.drop_table('users')
