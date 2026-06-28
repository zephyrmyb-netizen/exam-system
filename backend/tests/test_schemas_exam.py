from backend.schemas import ExamCreate, ExamOut, ExamResultOut, ExamSubmissionCreate


def test_exam_create_defaults():
    data = ExamCreate(title="Final", course_id=1)

    assert data.title == "Final"
    assert data.course_id == 1
    assert data.time_limit == 60
    assert data.total_score == 100
    assert data.is_shuffle is False
    assert data.is_blind is True
    assert data.question_ids == []


def test_exam_submission_accepts_answer_map():
    data = ExamSubmissionCreate(answers={"1": "A", "2": "True"})

    assert data.answers == {"1": "A", "2": "True"}


def test_exam_output_schemas_expose_frontend_contract():
    assert "status" in ExamOut.model_fields
    assert "question_count" in ExamOut.model_fields
    assert "score" in ExamResultOut.model_fields
    assert "accuracy_rate" in ExamResultOut.model_fields
