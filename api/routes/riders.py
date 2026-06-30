from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from api.state import app_state

router = APIRouter()


class RiderResponse(BaseModel):
    rider_id: int
    name: str
    team: str
    nationality: str
    sprint: float
    climbing: float
    tt: float
    gc: float
    form: float
    dns: bool
    dnf: bool
    young_rider_eligible: bool


class RiderUpdate(BaseModel):
    sprint: Optional[float] = Field(None, ge=0, le=100)
    climbing: Optional[float] = Field(None, ge=0, le=100)
    tt: Optional[float] = Field(None, ge=0, le=100)
    gc: Optional[float] = Field(None, ge=0, le=100)
    form: Optional[float] = Field(None, ge=0.5, le=1.5)
    dns: Optional[bool] = None
    dnf: Optional[bool] = None


@router.get("/riders", response_model=list[RiderResponse])
def get_riders():
    return [
        RiderResponse(
            rider_id=rs.rider.rider_id, name=rs.rider.name, team=rs.rider.team,
            nationality=rs.rider.nationality, sprint=rs.sprint, climbing=rs.climbing,
            tt=rs.tt, gc=rs.gc, form=rs.form, dns=rs.dns, dnf=rs.dnf,
            young_rider_eligible=rs.rider.young_rider_eligible,
        )
        for rs in app_state.riders.values()
    ]


@router.put("/riders/{rider_id}", response_model=RiderResponse)
def update_rider(rider_id: int, update: RiderUpdate):
    rs = app_state.riders.get(rider_id)
    if rs is None:
        raise HTTPException(404, detail=f"Rider {rider_id} not found")
    for field, value in update.model_dump(exclude_none=True).items():
        setattr(rs, field, value)
    return RiderResponse(
        rider_id=rs.rider.rider_id, name=rs.rider.name, team=rs.rider.team,
        nationality=rs.rider.nationality, sprint=rs.sprint, climbing=rs.climbing,
        tt=rs.tt, gc=rs.gc, form=rs.form, dns=rs.dns, dnf=rs.dnf,
        young_rider_eligible=rs.rider.young_rider_eligible,
    )
