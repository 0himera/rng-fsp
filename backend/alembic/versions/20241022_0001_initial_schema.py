from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20241022_0001"
down_revision = None
branch_labels = None
depends_on = None


SCHEMA_DEFAULT_TIMESTAMP = sa.text("timezone('utc', now())")


def upgrade() -> None:
    op.create_table(
        "entropy_simulations",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=SCHEMA_DEFAULT_TIMESTAMP, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=SCHEMA_DEFAULT_TIMESTAMP, nullable=False),
        sa.Column("noise_seed", sa.BigInteger(), nullable=True),
        sa.Column("noise_config", sa.JSON(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("seed_hex", sa.String(length=128), nullable=False),
        sa.Column("pool_hash", sa.LargeBinary(), nullable=False),
        sa.Column("chaos_checksum", sa.String(length=128), nullable=False),
        sa.Column("noise_raw_path", sa.String(length=512), nullable=False),
        sa.Column("chaos_raw_path", sa.String(length=512), nullable=False),
    )

    op.create_table(
        "chaos_runs",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=SCHEMA_DEFAULT_TIMESTAMP, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=SCHEMA_DEFAULT_TIMESTAMP, nullable=False),
        sa.Column("simulation_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("lyapunov_exponent", sa.Float(), nullable=False),
        sa.Column("trajectory_checksum", sa.String(length=128), nullable=False),
        sa.ForeignKeyConstraint(["simulation_id"], ["entropy_simulations.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "rng_runs",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=SCHEMA_DEFAULT_TIMESTAMP, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=SCHEMA_DEFAULT_TIMESTAMP, nullable=False),
        sa.Column("entropy_simulation_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("run_format", sa.String(length=16), nullable=False),
        sa.Column("length", sa.Integer(), nullable=False),
        sa.Column("entropy_metrics", sa.JSON(), nullable=False),
        sa.Column("seed_hash", sa.String(length=128), nullable=False),
        sa.Column("export_path", sa.String(length=512), nullable=True),
        sa.Column("run_checksum", sa.LargeBinary(), nullable=True),
        sa.ForeignKeyConstraint(["entropy_simulation_id"], ["entropy_simulations.id"], ondelete="SET NULL"),
    )

    op.create_table(
        "audit_uploads",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=SCHEMA_DEFAULT_TIMESTAMP, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=SCHEMA_DEFAULT_TIMESTAMP, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1024), nullable=True),
        sa.Column("data_hash", sa.String(length=128), nullable=False),
        sa.Column("result_path", sa.String(length=512), nullable=True),
        sa.Column("raw_payload", sa.LargeBinary(), nullable=False),
    )

    op.create_table(
        "test_reports",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=SCHEMA_DEFAULT_TIMESTAMP, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=SCHEMA_DEFAULT_TIMESTAMP, nullable=False),
        sa.Column("run_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("test_name", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("report_path", sa.String(length=512), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["rng_runs.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("test_reports")
    op.drop_table("audit_uploads")
    op.drop_table("rng_runs")
    op.drop_table("chaos_runs")
    op.drop_table("entropy_simulations")
