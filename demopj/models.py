# models.py
from sqlalchemy import Integer, String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from demopj.database import Base

class Feedback(Base):
    __tablename__ = "feedbacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(Text)
    tag: Mapped[str] = mapped_column(String(30), default="general")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

# models.py (추가 부분)
from sqlalchemy import Integer, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
import uuid

class DataPoint(Base):
    __tablename__ = "data_points"

    id: Mapped[uuid.UUID] = mapped_column(
        default=uuid.uuid4, primary_key=True
    )
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    raw_json: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

class ClusterJob(Base):
    __tablename__ = "cluster_jobs"

    id: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, primary_key=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    n_clusters: Mapped[int] = mapped_column(Integer, default=5)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    clusters: Mapped[list["Cluster"]] = relationship(back_populates="job")

class Cluster(Base):
    __tablename__ = "clusters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cluster_jobs.id", ondelete="CASCADE")
    )
    label: Mapped[int] = mapped_column(Integer)
    centroid: Mapped[list[float]] = mapped_column(JSON)

    job: Mapped["ClusterJob"] = relationship(back_populates="clusters")
    members: Mapped[list["ClusterMember"]] = relationship(back_populates="cluster")

class ClusterMember(Base):
    __tablename__ = "cluster_members"

    cluster_id: Mapped[int] = mapped_column(
        ForeignKey("clusters.id", ondelete="CASCADE"), primary_key=True
    )
    datapoint_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("data_points.id", ondelete="CASCADE"), primary_key=True
    )
    distance: Mapped[float] = mapped_column(Float)

    cluster: Mapped["Cluster"] = relationship(back_populates="members")
