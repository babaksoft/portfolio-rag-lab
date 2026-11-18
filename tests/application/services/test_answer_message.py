from portfolio_rag.application.services import AnswerMessageService


def test_answer_message_returns_labeled_placeholder() -> None:
    result = AnswerMessageService().execute("What did you build?")

    assert result.is_placeholder is True
    assert "Placeholder response" in result.answer
    assert "not a factual answer" in result.answer
