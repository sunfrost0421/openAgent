"""ORM 模型测试"""
from sqlalchemy import inspect
from src.core.session.db_models import SessionModel, TurnModel


def test_session_model_columns():
    """测试 SessionModel 字段"""
    columns = [c.name for c in inspect(SessionModel).columns]
    expected = [
        "id", "session_id", "user_id", "channel_id",
        "created_at", "updated_at", "expires_at", "summary"
    ]
    for col in expected:
        assert col in columns, f"Missing column: {col}"


def test_turn_model_columns():
    """测试 TurnModel 字段"""
    columns = [c.name for c in inspect(TurnModel).columns]
    expected = [
        "id", "turn_id", "session_id", "agent_name",
        "messages", "final_reply", "created_at", "is_compressed"
    ]
    for col in expected:
        assert col in columns, f"Missing column: {col}"


def test_turn_foreign_key():
    """测试 TurnModel 外键约束"""
    fk = TurnModel.__table__.foreign_keys
    assert len(fk) == 1
    fk_col = list(fk)[0]
    assert fk_col.column.name == "session_id"
    assert "ondelete" in str(fk_col.constraint)


def test_session_turn_relationship():
    """测试 Session 和 Turn 的关系"""
    # 检查 relationship 是否正确配置
    assert hasattr(SessionModel, 'turns')
    assert hasattr(TurnModel, 'session')
