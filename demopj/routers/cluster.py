# routers/cluster.py
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from demopj.database import get_session
from demopj.models import DataPoint, ClusterJob, Cluster, ClusterMember
from demopj.schemas import ClusterRequest, ClusterJobOut, ClusterResult
from sklearn.cluster import KMeans            # pip install scikit-learn
import numpy as np
from uuid import UUID
import datetime
import select

router = APIRouter(prefix="/analyze", tags=["analyze"])

@router.get("/job/{job_id}", response_model=ClusterJobOut)
async def get_job(job_id: UUID, db: AsyncSession = Depends(get_session)):
    job = await db.get(ClusterJob, job_id)
    if not job: raise HTTPException(404)
    return job

@router.get("/result/{job_id}", response_model=list[ClusterResult])
async def get_result(job_id: UUID, db: AsyncSession = Depends(get_session)):
    job = await db.get(ClusterJob, job_id)
    if not job or job.status != "done":
        raise HTTPException(404, "Job not finished or missing")
    res = await db.execute(
        select(Cluster).where(Cluster.job_id == job_id).order_by(Cluster.label)
    )
    clusters = res.scalars().all()
    output = []
    for c in clusters:
        mem_ids = [m.datapoint_id for m in c.members]
        output.append(
            ClusterResult(label=c.label,
                          centroid=c.centroid,
                          members=mem_ids)
        )
    return output


@router.post("/cluster", response_model=ClusterJobOut, status_code=202)
async def create_cluster_job(
    payload: ClusterRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session),
):
    job = ClusterJob(n_clusters=payload.n_clusters, status="pending")
    db.add(job)
    await db.commit(); await db.refresh(job)

    background_tasks.add_task(
        run_clustering, job.id, payload.datapoint_ids, db.bind.sync_engine.url
    )
    return job

async def run_clustering(job_id: UUID, ids: list[UUID], db_url: str):
    """
    실질 작업: (1) 데이터 로딩 → (2) KMeans → (3) 결과 INSERT
    같은 프로세스라 간단히 sync engine 사용
    """
    from sqlalchemy import select, create_engine
    from sqlalchemy.orm import Session
    engine = create_engine(db_url, future=True)

    with Session(engine) as s:
        job = s.get(ClusterJob, job_id)
        job.status, job.started_at = "running", datetime.utcnow()
        s.commit()

        # 1) 데이터 가져오기
        rows = s.execute(
            select(DataPoint).where(DataPoint.id.in_(ids))
        ).scalars().all()
        if not rows:
            job.status = "failed"; s.commit(); return

        X = np.array([flatten(dp.raw_json) for dp in rows])  # → [[f1, f2, …]]

        # 2) K-Means
        km = KMeans(n_clusters=job.n_clusters, n_init="auto", random_state=0)  # sklearn ≥1.7
        km.fit(X)   # :contentReference[oaicite:2]{index=2}

        # 3) 결과 저장
        for lbl in range(job.n_clusters):
            cl = Cluster(job_id=job.id, label=lbl,
                         centroid=km.cluster_centers_[lbl].tolist())
            s.add(cl); s.flush()  # id 확보
            for dp, dist in zip(rows, km.transform(X)[:, lbl]):
                if km.labels_[rows.index(dp)] == lbl:
                    s.add(ClusterMember(cluster_id=cl.id,
                                        datapoint_id=dp.id,
                                        distance=float(dist)))
        job.status = "done"; job.finished_at = datetime.utcnow()
        s.commit()

def flatten(raw: dict) -> list[float]:
    """👶🏻 예시 변환기: 숫자만 뽑아 정렬. 필요 시 여기 맞춤 수정."""
    return [v for _, v in sorted(raw.items()) if isinstance(v, (int, float))]
