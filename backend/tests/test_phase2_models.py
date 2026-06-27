"""Phase 2 model coverage for future exam, collaboration, and learning features."""

from backend import models


def test_role_model_exists_and_links_users():
    assert hasattr(models, "Role")
    assert hasattr(models.User, "role_id")
    assert hasattr(models.Role, "users")


def test_exam_models_have_required_fields():
    assert hasattr(models, "Exam")
    assert hasattr(models, "ExamQuestion")
    assert hasattr(models, "ExamSubmission")

    assert hasattr(models.Exam, "title")
    assert hasattr(models.Exam, "course_id")
    assert hasattr(models.Exam, "creator_id")
    assert hasattr(models.Exam, "time_limit")
    assert hasattr(models.Exam, "status")
    assert models.Exam.__table__.c.status.default.arg == "draft"

    assert hasattr(models.ExamQuestion, "score")
    assert hasattr(models.ExamQuestion, "order_index")
    assert hasattr(models.ExamSubmission, "answers")


def test_collaboration_and_learning_models_exist():
    assert hasattr(models, "Collaboration")
    assert hasattr(models.Collaboration, "course_id")
    assert hasattr(models.Collaboration, "role")

    assert hasattr(models, "Tag")
    assert hasattr(models.Tag, "parent_id")
    assert hasattr(models, "QuestionTag")

    assert hasattr(models, "Bookmark")
    assert hasattr(models.Bookmark, "folder_name")

    assert hasattr(models, "StudyGoal")
    assert hasattr(models.StudyGoal, "target_count")
    assert hasattr(models.StudyGoal, "progress")
