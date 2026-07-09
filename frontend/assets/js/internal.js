/** 审批/消息页面共享工具函数. */

export { checkSession, renderNav, redirectByRole } from '/assets/js/session-ui.js';

const STATUS_LABELS = {
  draft: '草稿',
  review: '审批中',
  approved: '已通过',
  rejected: '已驳回',
  signed: '已签订',
  active: '履行中',
  expired: '已到期',
  renewed: '已续签',
  archived: '已归档',
};

export function formatStatus(status) {
  return STATUS_LABELS[status] || status;
}
