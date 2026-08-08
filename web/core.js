const EMAIL_PATTERN = /^[^\s@]{1,64}@[^\s@]{1,190}$/;
const CLIENT_ID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const TENANT_PATTERN = /^(?:common|consumers|organizations|[0-9a-f-]{36}|[a-z0-9.-]{1,190})$/i;

export function maskEmail(address) {
  const [local = "", domain = ""] = String(address).split("@", 2);
  if (!domain) return "***";
  return `${local.slice(0, 1)}${"*".repeat(Math.max(3, Math.min(8, local.length - 1)))}@${domain}`;
}

export function redactText(value) {
  return String(value || "").replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, maskEmail);
}

export function parseAccounts(value) {
  const lines = String(value || "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  if (!lines.length) throw new Error("请先粘贴至少一条账号记录");
  if (lines.length > 50) throw new Error("单次最多处理 50 个邮箱");

  const seen = new Set();
  return lines.map((line, index) => {
    const parts = line.split("----").map((part) => part.trim());
    if (parts.length < 3 || parts.length > 4) {
      throw new Error(`第 ${index + 1} 行必须包含邮箱、client_id、refresh_token，可选 tenant`);
    }
    const [emailRaw, clientId, refreshToken, tenantRaw = "consumers"] = parts;
    const email = emailRaw.toLowerCase();
    const tenant = tenantRaw.toLowerCase();
    if (!EMAIL_PATTERN.test(email)) throw new Error(`第 ${index + 1} 行邮箱格式不正确`);
    if (!CLIENT_ID_PATTERN.test(clientId)) throw new Error(`第 ${index + 1} 行 client_id 不是有效 UUID`);
    if (!refreshToken || refreshToken.length > 8192 || /[\u0000-\u001f]/.test(refreshToken)) {
      throw new Error(`第 ${index + 1} 行 refresh_token 格式不正确`);
    }
    if (!TENANT_PATTERN.test(tenant) || tenant.includes("..")) {
      throw new Error(`第 ${index + 1} 行 tenant 格式不正确`);
    }
    if (seen.has(email)) throw new Error(`第 ${index + 1} 行邮箱重复`);
    seen.add(email);
    return { email, client_id: clientId.toLowerCase(), refresh_token: refreshToken, tenant };
  });
}

export function sanitizedExport(results) {
  return results.map((account) => ({
    account: account.account,
    status: account.status,
    error: account.error || undefined,
    skipped_oversize: account.skipped_oversize || 0,
    message_count: (account.messages || []).length,
    messages: (account.messages || []).map((message) => ({
      date: message.date,
      code_count: (message.codes || []).length,
    })),
  }));
}

export const demoResults = [
  {
    account: "l****@example.com",
    status: "ok",
    skipped_oversize: 0,
    messages: [
      {
        sender: "Northwind Studio <hello@northwind.example>",
        subject: "你的登录验证码",
        date: "Sun, 9 Aug 2026 09:42:00 +0800",
        preview: "你正在登录 Northwind Studio。验证码为 482731，十分钟内有效。若非本人操作，请忽略这封邮件。",
        codes: ["482731"],
      },
      {
        sender: "The Paper Garden <letters@papergarden.example>",
        subject: "八月来信：把缓慢留给周末",
        date: "Sun, 9 Aug 2026 08:15:00 +0800",
        preview: "本周的新刊已经抵达。愿你在嘈杂之外，仍有一张桌子、一束晨光，以及一点属于自己的时间。",
        codes: [],
      },
    ],
  },
  {
    account: "m***@example.net",
    status: "ok",
    skipped_oversize: 1,
    messages: [
      {
        sender: "Cloudline <notice@cloudline.example>",
        subject: "备份任务已完成",
        date: "Sun, 9 Aug 2026 07:30:00 +0800",
        preview: "夜间备份已安全完成，共处理 28 个文件。此消息使用完全合成的展示数据。",
        codes: [],
      },
    ],
  },
];
