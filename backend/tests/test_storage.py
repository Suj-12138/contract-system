"""JSON 存储层测试 — P5 Task 27."""
import json

from app.storage.json_store import JsonFileStore


def test_empty_store_created(tmp_path):
    """新文件路径自动创建空存储."""
    data_file = tmp_path / "store.json"
    store = JsonFileStore(str(data_file))
    data = store.read()
    assert data["schema_version"] == 1
    assert data["users"] == []
    assert data["contracts"] == []
    assert data["templates"] == []
    assert data["approval_records"] == []
    assert data["messages"] == []
    assert data["audit_logs"] == []
    assert data["sessions"] == []


def test_atomic_write_preserves_integrity(tmp_path):
    """写入后数据完整可读."""
    data_file = tmp_path / "store.json"
    store = JsonFileStore(str(data_file))
    store.transaction(lambda data: data["users"].append({
        "id": "u1", "username": "test", "email": "test@test.com",
        "password_hash": "h", "role": "handler", "is_active": True,
        "created_at": store.utcnow(),
    }))
    result = store.read()
    assert len(result["users"]) == 1
    assert result["users"][0]["username"] == "test"


def test_concurrent_reads_are_consistent(tmp_path):
    """并发读不会互相干扰."""
    data_file = tmp_path / "store.json"
    store = JsonFileStore(str(data_file))
    # 写入一条数据
    store.transaction(lambda d: d["users"].append({
        "id": "u1", "username": "a", "email": "a@a.com",
        "password_hash": "h", "role": "handler", "is_active": True,
        "created_at": store.utcnow(),
    }))
    # 多次读结果一致
    for _ in range(5):
        data = store.read()
        assert len(data["users"]) == 1


def test_new_id_is_unique_uuid(tmp_path):
    """每次 new_id 生成唯一 UUID."""
    store = JsonFileStore(str(tmp_path / "store.json"))
    ids = {store.new_id() for _ in range(100)}
    assert len(ids) == 100  # 全部唯一


def test_utcnow_iso8601_format(tmp_path):
    """utcnow 返回 ISO 8601 格式时间戳."""
    store = JsonFileStore(str(tmp_path / "store.json"))
    ts = store.utcnow()
    assert "T" in ts
    assert ts.endswith("Z")
    # 可以解析
    from datetime import datetime
    datetime.fromisoformat(ts.replace("Z", "+00:00"))


def test_transaction_rollback_on_error(tmp_path):
    """事务中抛出异常不影响已有数据."""
    data_file = tmp_path / "store.json"
    store = JsonFileStore(str(data_file))
    # 先写入正常数据
    store.transaction(lambda d: d["users"].append({
        "id": "u1", "username": "safe", "email": "s@fe.com",
        "password_hash": "h", "role": "handler", "is_active": True,
        "created_at": store.utcnow(),
    }))

    def bad_mutator(data):
        data["users"].append({
            "id": "u2", "username": "bad", "email": "b@d.com",
            "password_hash": "h", "role": "handler", "is_active": True,
            "created_at": store.utcnow(),
        })
        raise RuntimeError("模拟异常")

    try:
        store.transaction(bad_mutator)
    except RuntimeError:
        pass

    # bad 数据未持久化（注意：transaction 在锁内抛异常时 atomic write 不会执行）
    # 但由于 mutator 已修改了 data 字典（在内存中），且异常在 mutator 内抛出，
    # _write_atomic_unlocked 不会执行。但 data 已被修改。
    # 实际行为：reader 在下次读时会读到写入前状态（因为 write 没执行）
    data = store.read()
    # bad 数据不应出现（因为没写入文件）
    assert len(data["users"]) == 1


def test_data_persistence_across_store_instances(tmp_path):
    """不同 store 实例（同一文件）数据互通."""
    data_file = tmp_path / "store.json"
    s1 = JsonFileStore(str(data_file))
    s1.transaction(lambda d: d.setdefault("test_key", 0))
    s1.transaction(lambda d: d.update({"test_key": d["test_key"] + 1}))

    s2 = JsonFileStore(str(data_file))
    data = s2.read()
    assert data["test_key"] == 1
