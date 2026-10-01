import pandas as pd
import requests
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from service.extraction_service import ExtractionService

router = APIRouter()
extraction_service = ExtractionService()


@router.get("/ilo/{indicator_id}")
def get_indicator(
    indicator_id: str,
    from_date: int = Query(default=2014, ge=1900, le=2100),
    to_date: int = Query(default=2026, ge=1900, le=2100),
):
    try:
        data = extraction_service.get_indicator_data(
            indicator_id=indicator_id,
            from_date=from_date,
            to_date=to_date,
        )
        return data.astype(object).where(pd.notna(data), None).to_dict(
            orient="records"
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=502,
            detail=f"ILOSTAT data retrieval failed: {exc}",
        ) from exc


@router.get("/ilo/{indicator_id}/csv")
def download_indicator_csv(
    indicator_id: str,
    from_date: int = Query(default=2014, ge=1900, le=2100),
    to_date: int = Query(default=2026, ge=1900, le=2100),
):
    try:
        data = extraction_service.get_indicator_data(
            indicator_id=indicator_id,
            from_date=from_date,
            to_date=to_date,
        )
        return Response(
            content=data.to_csv(index=False),
            media_type="text/csv",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="{indicator_id}.csv"'
                )
            },
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
