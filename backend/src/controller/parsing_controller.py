import requests
from fastapi import APIRouter, HTTPException, Query

from service.extraction_service import ExtractionService
from service.parsing_service import ParsingService

router = APIRouter()
extraction_service = ExtractionService()
parsing_service = ParsingService()


@router.get("/{indicator_id}")
def parse_indicator(
    indicator_id: str,
    from_date: int = Query(default=2014, ge=1900, le=2100),
    to_date: int = Query(default=2026, ge=1900, le=2100),
):
    """Fetch an ILOSTAT indicator and return normalized JSON records."""
    try:
        data = extraction_service.get_indicator_data(
            indicator_id=indicator_id, from_date=from_date, to_date=to_date
        )
        return parsing_service.parse_indicator_data(data, indicator_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"ILOSTAT data retrieval failed: {exc}") from exc
