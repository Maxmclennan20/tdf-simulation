from fastapi import APIRouter
from pydantic import BaseModel
from api.state import app_state

router = APIRouter()


class StageResponse(BaseModel):
    stage: int
    start: str
    finish: str
    distance: float
    type: str
    key_climbs: list[str]


@router.get("/stages", response_model=list[StageResponse])
def get_stages():
    return [
        StageResponse(
            stage=s.stage, start=s.start, finish=s.finish,
            distance=s.distance, type=s.type.value, key_climbs=s.key_climbs,
        )
        for s in sorted(app_state.stages.values(), key=lambda x: x.stage)
    ]
