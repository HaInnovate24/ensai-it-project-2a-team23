from fastapi import APIRouter

from  service.extraction_service import ExtractionService
router = APIRouter()


@router.get("/ilo/{indicator_id}")
def get_indicator(
    indicator_id: str,
    from_date: int = 2014,
    to_date: int = 2026,
):
    return ExtractionService.get_indicator_data(
        indicator_id,
        from_date,
        to_date,
    )