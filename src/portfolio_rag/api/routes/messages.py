"""User-message routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from portfolio_rag.api.correlation import get_correlation_id
from portfolio_rag.api.dependencies import get_answer_message_service
from portfolio_rag.api.models import ErrorResponse, MessageRequest, MessageResponse
from portfolio_rag.application.services import AnswerMessageService

router = APIRouter(prefix="/v1/messages", tags=["messages"])


@router.post(
    "",
    response_model=MessageResponse,
    responses={422: {"model": ErrorResponse}},
)
async def answer_message(
    request: MessageRequest,
    service: Annotated[AnswerMessageService, Depends(get_answer_message_service)],
) -> MessageResponse:
    """Validate and answer one message through the application service."""
    result = service.execute(request.message)
    return MessageResponse(
        answer=result.answer,
        is_placeholder=result.is_placeholder,
        correlation_id=get_correlation_id(),
    )
