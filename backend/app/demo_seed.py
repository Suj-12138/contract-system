# -*- coding: utf-8 -*-
"""
演示数据预制脚本 — P5 Task 30.

创建 4 个演示账号 + 1 个完整审批链的合同，供周五演示使用。

用法：
    cd backend
    python -m app.demo_seed
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_settings
from app.domain.enums import ContractStatus, UserRole
from app.domain.models import (
    make_approval_record,
    make_audit_log,
    make_contract,
    make_message,
    make_template,
    make_user,
)
from app.repositories.json_repository import JsonRepository
from app.security.passwords import hash_password
from app.storage.json_store import JsonFileStore


def seed_demo_data():
    settings = get_settings()
    store = JsonFileStore(settings.DATA_FILE)
    repo = JsonRepository(store)

    # ── 1. 创建 4 个演示账号 ──
    admin = make_user(store, "admin", "admin@company.com",
                      hash_password("demo123456"), UserRole.ADMIN)
    repo.create_user(admin)

    handler = make_user(store, "张三", "zhangsan@company.com",
                        hash_password("demo123456"), UserRole.HANDLER)
    repo.create_user(handler)

    approver1 = make_user(store, "李主管", "lizhuguan@company.com",
                          hash_password("demo123456"), UserRole.APPROVER)
    repo.create_user(approver1)

    approver2 = make_user(store, "王法务", "wangfawu@company.com",
                          hash_password("demo123456"), UserRole.APPROVER)
    repo.create_user(approver2)

    print("[OK] 4 个演示账号已创建：")
    print(f"   管理员: admin / demo123456")
    print(f"   经办人: 张三 / demo123456")
    print(f"   主管审批: 李主管 / demo123456")
    print(f"   法务审批: 王法务 / demo123456")

    # ── 2. 创建模板 ──
    template = make_template(store, "标准采购合同", "适用于常规物资采购",
                             [
                                 {"label": "甲方", "type": "text", "required": True},
                                 {"label": "乙方", "type": "text", "required": True},
                                 {"label": "合同金额", "type": "number", "required": True},
                                 {"label": "交付日期", "type": "date", "required": True},
                                 {"label": "主要条款", "type": "textarea", "required": True},
                             ],
                             admin["id"])
    repo.create_template(template)
    print(f"[OK] 模板「{template['name']}」已创建")

    # ── 3. 创建已走完审批链的合同 ──
    contract = make_contract(
        store,
        title="2026年度服务器采购合同",
        counterparty="华为技术有限公司",
        handler_id=handler["id"],
        approver_1_id=approver1["id"],
        approver_2_id=approver2["id"],
        template_id=template["id"],
        content_json={
            "甲方": "本公司",
            "乙方": "华为技术有限公司",
            "合同金额": "¥500,000.00",
            "到期日期": "2027-08-15T00:00:00Z",
            "合同正文": "第一条 合同标的\n甲方向乙方采购服务器设备，具体配置及数量详见附件一。\n\n第二条 交付与验收\n乙方应于2026年8月15日前完成设备交付，甲方在收到设备后10个工作日内完成验收。\n\n第三条 付款方式\n合同签订后支付30%，验收合格后支付60%，质保期满支付10%。\n\n第四条 售后服务\n乙方提供3年免费维保服务，响应时间不超过4小时。",
        },
        amount=500000.0,
        expires_at="2027-08-15T00:00:00Z",
    )
    repo.create_contract(contract)

    # 模拟审批流程：创建审批记录 → 一级通过 → 二级通过 → 签订
    ar1 = make_approval_record(store, contract["id"], 1, approver1["id"])
    ar2 = make_approval_record(store, contract["id"], 2, approver2["id"])
    repo.create_approval_record(ar1)
    repo.create_approval_record(ar2)

    # 更新审批记录为已通过
    now = store.utcnow()
    repo.update_approval_record(ar1["id"], {
        "decision": "approved", "comment": "同意采购，金额合理。", "decided_at": now,
    })
    repo.update_approval_record(ar2["id"], {
        "decision": "approved", "comment": "合同条款无法律风险。", "decided_at": now,
    })

    # 合同状态 → reviewed → approved → signed → active
    repo.update_contract(contract["id"], {
        "status": ContractStatus.ACTIVE.value, "signed_at": now, "updated_at": now,
    })

    # 审计日志
    repo.create_audit_log(make_audit_log(store, handler["id"], "create_contract",
                                          "contract", contract["id"], "创建合同"))
    repo.create_audit_log(make_audit_log(store, handler["id"], "submit_review",
                                          "contract", contract["id"], "提交审批"))
    repo.create_audit_log(make_audit_log(store, approver1["id"], "approve",
                                          "contract", contract["id"], "第1级审批通过"))
    repo.create_audit_log(make_audit_log(store, approver2["id"], "approve",
                                          "contract", contract["id"], "第2级审批通过"))
    repo.create_audit_log(make_audit_log(store, handler["id"], "sign_contract",
                                          "contract", contract["id"], "确认签订"))

    # 通知消息
    repo.create_message(make_message(store, handler["id"],
                                     "审批通过", f"合同「{contract['title']}」已通过审批",
                                     contract["id"]))

    print(f"[OK] 演示合同「{contract['title']}」已创建（状态: 履行中）")
    print(f"   合同ID: {contract['id']}")

    # ── 4. 额外创建 2 个不同状态的合同 ──
    draft_contract = make_contract(
        store, "2027年度办公用品采购", "得力集团",
        handler["id"], approver1["id"], approver2["id"],
        amount=20000.0, expires_at="2027-12-31T00:00:00Z",
    )
    repo.create_contract(draft_contract)
    repo.create_audit_log(make_audit_log(store, handler["id"], "create_contract",
                                          "contract", draft_contract["id"], "创建合同"))
    print(f"[OK] 草稿合同「{draft_contract['title']}」已创建（状态: 草稿）")

    # 5. 创建一份审批中的合同（李主管待审批）
    review_contract = make_contract(
        store, "2026年度软件许可采购", "微软中国",
        handler["id"], approver1["id"], approver2["id"],
        amount=300000.0,
        content_json={
            "甲方": "本公司",
            "乙方": "微软中国",
            "合同金额": "¥300,000.00",
            "到期日期": "2027-06-30T00:00:00Z",
            "合同正文": "第一条 许可范围\n微软向甲方授予200个用户的企业级软件使用许可，涵盖Windows、Office 365及Azure基础服务。\n\n第二条 许可期限\n许可有效期自合同签订之日起至2027年6月30日止。\n\n第三条 费用与支付\n年度许可费为人民币30万元，按年支付。",
        },
        expires_at="2027-06-30T00:00:00Z",
    )
    repo.create_contract(review_contract)
    # 提交审批
    repo.update_contract(review_contract["id"], {"status": ContractStatus.REVIEW.value})
    ar1_pending = make_approval_record(store, review_contract["id"], 1, approver1["id"])
    ar2_pending = make_approval_record(store, review_contract["id"], 2, approver2["id"])
    repo.create_approval_record(ar1_pending)
    repo.create_approval_record(ar2_pending)
    repo.create_audit_log(make_audit_log(store, handler["id"], "create_contract",
                                          "contract", review_contract["id"], "创建合同"))
    repo.create_audit_log(make_audit_log(store, handler["id"], "submit_review",
                                          "contract", review_contract["id"], "提交审批"))
    print(f"[OK] 审批中合同「{review_contract['title']}」已创建（状态: 审批中，等待李主管审批）")

    print("\n[DONE] 演示数据预制完成！")
    print(f"   数据文件: {settings.DATA_FILE}")
    print("\n   演示流程：")
    print("   1. admin 登录 → 查看数据看板")
    print("   2. 张三 登录 → 查看合同列表（含履行中 + 草稿）")
    print("   3. 张三 → 提交草稿合同审批")
    print("   4. 李主管 登录 → 待审批列表 → 审批通过")
    print("   5. 王法务 登录 → 待审批列表 → 审批通过")
    print("   6. 张三 登录 → 确认签订")


if __name__ == "__main__":
    seed_demo_data()
