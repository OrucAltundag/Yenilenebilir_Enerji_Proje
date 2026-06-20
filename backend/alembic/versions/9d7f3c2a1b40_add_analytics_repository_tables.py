"""add analytics repository tables

Revision ID: 9d7f3c2a1b40
Revises: f5b7b20feab5
Create Date: 2026-06-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9d7f3c2a1b40"
down_revision: Union[str, None] = "f5b7b20feab5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("district_master", sa.Column("search_key", sa.String(), nullable=True))
    op.create_index(
        op.f("ix_district_master_search_key"),
        "district_master",
        ["search_key"],
        unique=False,
    )

    op.create_table(
        "district_score_summary",
        sa.Column("district_id", sa.String(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("ges_score_mean", sa.Float(), nullable=False),
        sa.Column("ges_score_median", sa.Float(), nullable=False),
        sa.Column("ges_score_min", sa.Float(), nullable=False),
        sa.Column("ges_score_max", sa.Float(), nullable=False),
        sa.Column("ges_score_p10", sa.Float(), nullable=False),
        sa.Column("ges_score_p90", sa.Float(), nullable=False),
        sa.Column("ges_score_stddev", sa.Float(), nullable=False),
        sa.Column("res_score_mean", sa.Float(), nullable=False),
        sa.Column("res_score_median", sa.Float(), nullable=False),
        sa.Column("res_score_min", sa.Float(), nullable=False),
        sa.Column("res_score_max", sa.Float(), nullable=False),
        sa.Column("res_score_p10", sa.Float(), nullable=False),
        sa.Column("res_score_p90", sa.Float(), nullable=False),
        sa.Column("res_score_stddev", sa.Float(), nullable=False),
        sa.Column("sample_count", sa.Integer(), nullable=False),
        sa.Column("t2m", sa.Float(), nullable=False),
        sa.Column("rh2m", sa.Float(), nullable=False),
        sa.Column("ws10m", sa.Float(), nullable=False),
        sa.Column("allsky_sfc_sw_dwn", sa.Float(), nullable=False),
        sa.Column("arazi_egimi_yuzde", sa.Float(), nullable=False),
        sa.Column("yuzey_alani_km2", sa.Float(), nullable=False),
        sa.Column("land_forest_nature", sa.Float(), nullable=False),
        sa.Column("land_water", sa.Float(), nullable=False),
        sa.Column("land_wetland", sa.Float(), nullable=False),
        sa.Column("land_agriculture", sa.Float(), nullable=False),
        sa.Column("land_urban", sa.Float(), nullable=False),
        sa.Column("tesvik_bolgesi", sa.Float(), nullable=False),
        sa.Column("ges_national_rank", sa.Integer(), nullable=False),
        sa.Column("ges_percentile", sa.Float(), nullable=False),
        sa.Column("res_national_rank", sa.Integer(), nullable=False),
        sa.Column("res_percentile", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["district_id"], ["district_master.district_id"]),
        sa.PrimaryKeyConstraint("district_id", "year"),
    )
    op.create_index(
        op.f("ix_district_score_summary_ges_national_rank"),
        "district_score_summary",
        ["ges_national_rank"],
        unique=False,
    )
    op.create_index(
        op.f("ix_district_score_summary_res_national_rank"),
        "district_score_summary",
        ["res_national_rank"],
        unique=False,
    )

    op.create_table(
        "district_monthly_profile",
        sa.Column("district_id", sa.String(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("ges_mean", sa.Float(), nullable=False),
        sa.Column("res_mean", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["district_id"], ["district_master.district_id"]),
        sa.PrimaryKeyConstraint("district_id", "year", "month"),
    )


def downgrade() -> None:
    op.drop_table("district_monthly_profile")
    op.drop_index(
        op.f("ix_district_score_summary_res_national_rank"),
        table_name="district_score_summary",
    )
    op.drop_index(
        op.f("ix_district_score_summary_ges_national_rank"),
        table_name="district_score_summary",
    )
    op.drop_table("district_score_summary")
    op.drop_index(op.f("ix_district_master_search_key"), table_name="district_master")
    op.drop_column("district_master", "search_key")
