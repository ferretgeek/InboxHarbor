import { demoResults, parseAccounts, sanitizedExport } from "/core.js";

const elements = {
  theme: document.querySelector("#theme-select"),
  accessKey: document.querySelector("#access-key"),
  status: document.querySelector("#server-status"),
  form: document.querySelector("#fetch-form"),
  accounts: document.querySelector("#accounts"),
  accountFile: document.querySelector("#account-file"),
  limit: document.querySelector("#limit"),
  previewChars: document.querySelector("#preview-chars"),
  timeout: document.querySelector("#timeout"),
  concurrency: document.querySelector("#concurrency"),
  fetchButton: document.querySelector("#fetch-button"),
  demoButton: document.querySelector("#demo-button"),
  error: document.querySelector("#form-error"),
  empty: document.querySelector("#empty-state"),
  list: document.querySelector("#result-list"),
  summary: document.querySelector("#result-summary"),
  privacy: document.querySelector("#privacy-toggle"),
  export: document.querySelector("#export-button"),
  toast: document.querySelector("#toast"),
};

let currentResults = [];
let privacyOn = true;
let toastTimer;

function showToast(message) {
  elements.toast.textContent = message;
  elements.toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => elements.toast.classList.remove("show"), 2300);
}

function setTheme(theme) {
  const allowed = new Set(["sky", "jade", "sunset", "graphite"]);
  const selected = allowed.has(theme) ? theme : "sky";
  document.documentElement.dataset.theme = selected;
  elements.theme.value = selected;
  localStorage.setItem("inboxharbor-theme", selected);
}

elements.theme.addEventListener("change", () => setTheme(elements.theme.value));
setTheme(localStorage.getItem("inboxharbor-theme") || "sky");

function makeElement(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function renderResults(results, isDemo = false) {
  currentResults = results;
  elements.list.replaceChildren();
  elements.empty.hidden = true;
  elements.list.hidden = false;
  privacyOn = true;
  elements.list.classList.add("privacy-on");
  elements.privacy.textContent = "显示详情";
  let messageCount = 0;
  let successCount = 0;

  results.forEach((account) => {
    const card = makeElement("article", "account-result");
    const head = makeElement("header", "account-head");
    head.append(makeElement("strong", "", account.account));
    const status = makeElement("span", account.status === "ok" ? "" : "failed", account.status === "ok" ? "读取成功" : "读取失败");
    head.append(status);
    card.append(head);
    if (account.status !== "ok") {
      card.append(makeElement("p", "account-error", account.error || "读取失败"));
    }
    (account.messages || []).forEach((message) => {
      messageCount += 1;
      const row = makeElement("article", "message-card");
      const mark = makeElement("div", "sender-mark", String(message.sender || "信").trim().slice(0, 1).toUpperCase());
      const content = makeElement("div", "");
      const top = makeElement("div", "message-top");
      top.append(makeElement("span", "message-sender private-detail", message.sender || "未知发件人"));
      top.append(makeElement("time", "message-date", message.date || ""));
      content.append(top);
      content.append(makeElement("h4", "message-subject private-detail", message.subject || "（无主题）"));
      content.append(makeElement("p", "message-preview private-detail", message.preview || "（无文本预览）"));
      if ((message.codes || []).length) {
        const codes = makeElement("div", "codes private-detail");
        message.codes.forEach((code) => codes.append(makeElement("span", "code-chip", code)));
        content.append(codes);
      }
      row.append(mark, content);
      card.append(row);
    });
    if (account.status === "ok") successCount += 1;
    elements.list.append(card);
  });
  elements.summary.textContent = `${successCount}/${results.length} 个邮箱 · ${messageCount} 封来信${isDemo ? " · 合成演示" : ""}`;
  elements.privacy.disabled = false;
  elements.export.disabled = false;
}

elements.demoButton.addEventListener("click", () => {
  renderResults(structuredClone(demoResults), true);
  document.querySelector("#workbench").scrollIntoView({ behavior: "smooth" });
  showToast("已打开完全合成的安全演示");
});

elements.privacy.addEventListener("click", () => {
  privacyOn = !privacyOn;
  elements.list.classList.toggle("privacy-on", privacyOn);
  elements.privacy.textContent = privacyOn ? "显示详情" : "隐藏详情";
});

elements.export.addEventListener("click", () => {
  const payload = JSON.stringify(sanitizedExport(currentResults), null, 2);
  const blob = new Blob([payload], { type: "application/json;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `inboxharbor-redacted-${new Date().toISOString().slice(0, 10)}.json`;
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 0);
  showToast("已导出不含发件人、主题、正文和验证码值的摘要");
});

elements.accountFile.addEventListener("change", async () => {
  const file = elements.accountFile.files?.[0];
  elements.accountFile.value = "";
  if (!file) return;
  if (file.size > 256_000) {
    elements.error.textContent = "TXT 不能超过 256 KB";
    return;
  }
  elements.accounts.value = await file.text();
  elements.error.textContent = "";
  showToast("TXT 已在浏览器内读取，不会自动上传");
});

elements.form.addEventListener("submit", async (event) => {
  event.preventDefault();
  elements.error.textContent = "";
  let accounts;
  try {
    accounts = parseAccounts(elements.accounts.value);
  } catch (error) {
    elements.error.textContent = error instanceof Error ? error.message : "账号格式无法解析";
    return;
  }
  const payload = {
    accounts,
    settings: {
      limit: Number(elements.limit.value),
      preview_chars: Number(elements.previewChars.value),
      timeout: Number(elements.timeout.value),
      concurrency: Number(elements.concurrency.value),
    },
  };
  elements.accounts.value = "";
  accounts = null;
  elements.fetchButton.disabled = true;
  elements.fetchButton.querySelector("span").textContent = "正在穿过潮汐…";
  try {
    const headers = { "Content-Type": "application/json" };
    if (elements.accessKey.value) headers["X-InboxHarbor-Key"] = elements.accessKey.value;
    const response = await fetch("/api/fetch", {
      method: "POST",
      headers,
      body: JSON.stringify(payload),
      credentials: "same-origin",
      cache: "no-store",
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "取件请求被拒绝");
    renderResults(data.results || []);
    showToast("取件完成，账号输入已经清空");
  } catch (error) {
    elements.error.textContent = error instanceof Error ? error.message : "取件失败";
  } finally {
    elements.fetchButton.disabled = false;
    elements.fetchButton.querySelector("span").textContent = "开始安全取件";
  }
});

async function checkHealth() {
  try {
    const response = await fetch("/api/health", { cache: "no-store" });
    if (!response.ok) throw new Error();
    const data = await response.json();
    elements.status.classList.add("ready");
    elements.status.querySelector("span").textContent = data.auth_required ? "服务就绪 · 远程密钥保护" : "本地服务就绪 · 零持久化";
  } catch {
    elements.status.classList.add("error");
    elements.status.querySelector("span").textContent = "无法连接后端服务";
  }
}

checkHealth();
