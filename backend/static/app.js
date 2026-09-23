/* 自招学习平台 SPA：主页组件格 + 各组件页 + 登录 */
const $ = (s, r = document) => r.querySelector(s);
/* 所有来自服务端的文本（上传标题/文件名/素材/常驻条目）进 innerHTML 前必须过这一层，
   否则一个带 <img onerror> 的文件名就是存储型 XSS。 */
function esc(v) {
  return String(v == null ? "" : v).replace(/[&<>"']/g, c => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}
const view = $("#view");
const dock = $("#dock");
const userLabel = $("#userLabel");
const btnLogout = $("#btnLogout");
const clockHm = $("#clockHm");
const clockDate = $("#clockDate");

const state = {
  user: null,
  home: null,
  route: "login",
};

async function api(path, opts = {}) {
  const res = await fetch(path, {
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
    ...opts,
  });
  let data = {};
  try { data = await res.json(); } catch (_) { data = {}; }
  if (!res.ok) {
    const err = new Error(data.detail || res.statusText || "error");
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

/* ---------------- 顶栏时钟 ----------------
 * 走时靠浏览器本地时间（每秒自增，不请求）；整点/首次跟服务端对一次，
 * 防止本机时钟被改错导致「今天」看错天（day_key 是服务端按北京时间算的）。
 */
let clockSkewMs = 0;

function renderClock() {
  if (!clockHm) return;
  const d = new Date(Date.now() + clockSkewMs);
  const p = n => String(n).padStart(2, "0");
  clockHm.textContent = `${p(d.getHours())}:${p(d.getMinutes())}`;
  const wd = "周" + "日一二三四五六"[d.getDay()];
  clockDate.textContent = `${d.getFullYear()}年${p(d.getMonth() + 1)}月${p(d.getDate())}日 ${wd}`;
}

async function syncClock() {
  try {
    const t = await api("/api/system/time");
    if (t && t.unix) clockSkewMs = t.unix * 1000 - Date.now();
  } catch (_) { /* 离线就用本地时间，别让时钟把页面搞挂 */ }
  renderClock();
}

function startClock() {
  renderClock();
  setInterval(renderClock, 1000);
  syncClock();
  // 每 10 分钟重新校一次（设备休眠唤醒/长时间挂后台会漂）
  setInterval(syncClock, 10 * 60 * 1000);
}

function setRoute(name) {
  state.route = name;
  location.hash = "#/" + name;
  render();
}

function parseHash() {
  const h = (location.hash || "#/home").replace(/^#\/?/, "") || "home";
  return h.split("?")[0];
}

/* ---------------- Login ---------------- */
function renderLogin() {
  view.innerHTML = `
    <div class="login-wrap panel">
      <h1 class="page">登录 / 注册</h1>
      <div class="tabs">
        <button class="primary" id="tabEmail">邮箱验证码</button>
        <button class="ghost" id="tabPass">PassKey</button>
      </div>
      <div id="emailPane">
        <div class="row"><label>邮箱</label><input id="email" type="email" placeholder="you@example.com" /></div>
        <div class="row">
          <button class="ghost" id="btnSendCode">发送验证码</button>
          <input id="code" placeholder="6 位验证码" style="flex:1" />
        </div>
        <button class="primary" id="btnEmailLogin" style="width:100%">登录 / 自动注册</button>
        <p class="hint">开发环境验证码写入本地 outbox（storage 已 gitignore）。ESP 请用设备 PassKey。</p>
        <pre class="out" id="authOut"></pre>
      </div>
      <div id="passPane" class="hidden">
        <div class="row"><label>凭据</label><input id="credId" placeholder="credential_id" /></div>
        <div class="row"><label>挑战</label><input id="pkChal" placeholder="challenge" /></div>
        <div class="row"><label>签名</label><input id="pkSig" placeholder="signature" /></div>
        <button class="primary" id="btnPassLogin" style="width:100%">PassKey 登录</button>
        <p class="hint">浏览器完整 WebAuthn 可后续接；此处支持已注册凭据 + 挑战登录。设备盒子走 /api/auth/device/login。</p>
        <pre class="out" id="passOut"></pre>
      </div>
    </div>`;
  dock.classList.add("hidden");
  btnLogout.classList.add("hidden");
  userLabel.textContent = "";

  $("#tabEmail").onclick = () => {
    $("#emailPane").classList.remove("hidden");
    $("#passPane").classList.add("hidden");
    $("#tabEmail").className = "primary"; $("#tabPass").className = "ghost";
  };
  $("#tabPass").onclick = () => {
    $("#passPane").classList.remove("hidden");
    $("#emailPane").classList.add("hidden");
    $("#tabPass").className = "primary"; $("#tabEmail").className = "ghost";
  };
  $("#btnSendCode").onclick = async () => {
    try {
      const r = await api("/api/auth/email/send-code", { method: "POST", body: JSON.stringify({ email: $("#email").value }) });
      $("#authOut").textContent = JSON.stringify(r, null, 2);
    } catch (e) { $("#authOut").textContent = String(e.message || e); }
  };
  $("#btnEmailLogin").onclick = async () => {
    try {
      const r = await api("/api/auth/email/login", {
        method: "POST",
        body: JSON.stringify({ email: $("#email").value, code: $("#code").value }),
      });
      state.user = r.user;
      await bootstrap();
      setRoute("home");
    } catch (e) { $("#authOut").textContent = String(e.message || e); }
  };
  $("#btnPassLogin").onclick = async () => {
    try {
      const r = await api("/api/auth/passkey/login", {
        method: "POST",
        body: JSON.stringify({
          credential_id: $("#credId").value,
          challenge: $("#pkChal").value,
          signature: $("#pkSig").value || "local",
        }),
      });
      state.user = r.user;
      await bootstrap();
      setRoute("home");
    } catch (e) { $("#passOut").textContent = String(e.message || e); }
  };
}

/* ---------------- Shell ---------------- */
function renderDock() {
  const comps = (state.home && state.home.components) || [];
  if (!comps.length) { dock.classList.add("hidden"); return; }
  dock.classList.remove("hidden");
  dock.innerHTML = comps.map(c =>
    `<button data-id="${esc(c.id)}" class="${state.route === c.id ? "active" : ""}">${esc(c.icon)}<div>${esc(c.name)}</div></button>`
  ).join("");
  dock.querySelectorAll("button").forEach(b => {
    b.onclick = () => setRoute(b.dataset.id);
  });
}

async function bootstrap() {
  try {
    state.user = await api("/api/auth/me");
    state.home = await api("/api/home");
    userLabel.textContent = state.user.display_name || state.user.email;
    btnLogout.classList.remove("hidden");
  } catch (e) {
    state.user = null;
    state.home = null;
  }
}

btnLogout.onclick = async () => {
  try { await api("/api/auth/logout", { method: "POST" }); } catch (_) {}
  state.user = null; state.home = null;
  setRoute("login");
};
$("#brandHome").onclick = () => { if (state.user) setRoute("home"); };

/* ---------------- Views ---------------- */
function renderHome() {
  const cards = (state.home && state.home.components) || [];
  const d = new Date(Date.now() + clockSkewMs);
  const p = n => String(n).padStart(2, "0");
  const wd = "周" + "日一二三四五六"[d.getDay()];
  const dateLine = `${d.getFullYear()}年${p(d.getMonth() + 1)}月${p(d.getDate())}日 ${wd}`;
  view.innerHTML = `
    <h1 class="page">主页</h1>
    <p class="muted">今天是 <b class="today-flag">${dateLine}</b>。点组件进入。可在资料库上传文件让 AI 整理；时间表可对话整理。</p>
    <div class="card-grid">
      ${cards.length ? cards.map(c => `
        <div class="card" data-go="${esc(c.id)}">
          <div class="icon">${esc(c.icon)}</div>
          <h3>${esc(c.name)}</h3>
          <p>${esc(c.description)}</p>
        </div>`).join("") : `<p class="muted">所有组件都关了。在下面「组件管理」里点「启用」恢复。</p>`}
    </div>
    <div class="panel" style="margin-top:16px">
      <h2>自注册 API（OpenAI 兼容）</h2>
      <p class="hint">文本模型 + TTS 各配一个；Key 只存本机 storage，不进 git。</p>
      <div class="row"><label>文本 Base</label><input id="txtBase" placeholder="https://api.openai.com/v1" /></div>
      <div class="row"><label>文本 Key</label><input id="txtKey" type="password" placeholder="sk-..." /></div>
      <div class="row"><label>文本模型</label><input id="txtModel" placeholder="gpt-4o-mini" /></div>
      <div class="row"><button class="primary" id="btnSaveText">保存文本 API</button></div>
      <div class="row"><label>TTS Base</label><input id="ttsBase" placeholder="https://api.openai.com/v1" /></div>
      <div class="row"><label>TTS Key</label><input id="ttsKey" type="password" placeholder="sk-..." /></div>
      <div class="row"><label>TTS 模型</label><input id="ttsModel" placeholder="tts-1" /></div>
      <div class="row"><label>Voice</label><input id="ttsVoice" placeholder="alloy" /></div>
      <div class="row"><button class="primary" id="btnSaveTts">保存 TTS</button><button class="ghost" id="btnProbeApi">连通测试</button></div>
      <pre class="out" id="apiOut">未配置/未测</pre>
    </div>
    <div class="panel">
      <h2>离线包（板子/浏览器）</h2>
      <div class="row">
        <button class="ghost" id="btnManifest">清单</button>
        <button class="primary" id="btnBundle">今日离线内容</button>
      </div>
      <pre class="out" id="offOut">登录后拉取；断网播本地缓存。板子 10 分钟无操作音量自动最小。</pre>
    </div>
    <div class="panel" style="margin-top:16px">
      <h2>组件管理</h2>
      <div id="compList"></div>
      <div class="row" style="margin-top:10px">
        <input id="reqTitle" placeholder="申请新组件名称" />
        <button class="ghost" id="btnReq">提交申请</button>
      </div>
      <pre class="out" id="reqOut"></pre>
    </div>`;
  view.querySelectorAll("[data-go]").forEach(el => {
    el.onclick = () => setRoute(el.dataset.go);
  });
  const list = $("#compList");
  const catalog = (state.home && state.home.catalog) || [];
  const enabled = new Set(((state.home && state.home.components) || []).map(c => c.id));
  list.innerHTML = catalog.map(c => `
    <div class="list-item">
      <div><b>${esc(c.name)}</b> <span class="muted">${esc(c.id)}</span><div class="muted">${esc(c.description)}</div></div>
      <button class="ghost" data-toggle="${esc(c.id)}">${enabled.has(c.id) ? "已启用" : "启用"}</button>
    </div>`).join("");
  list.querySelectorAll("[data-toggle]").forEach(btn => {
    btn.onclick = async () => {
      const id = btn.dataset.toggle;
      const on = !enabled.has(id);
      await api("/api/components/toggle", { method: "POST", body: JSON.stringify({ component_id: id, enabled: on }) });
      state.home = await api("/api/home");
      renderHome(); renderDock();
    };
  });
  // 自注册 API + 离线包
  // 注意：renderHome 保持同步（render() 直接调用），异步取配置必须包在 IIFE 里；
  // 之前这里直接在同步函数体里 await，是解析期语法错误，整个 app.js 加载失败、页面全白。
  // 另外变量名不能叫 view——全局 view 是 #view 容器，会被遮蔽。
  async function loadApiSettings() {
    try {
      const cfg = await api("/api/settings/apis");
      $("#txtBase").value = cfg.text?.base_url || "";
      $("#txtModel").value = cfg.text?.model || "";
      $("#ttsBase").value = cfg.tts?.base_url || "";
      $("#ttsModel").value = cfg.tts?.model || "";
      $("#ttsVoice").value = cfg.tts?.voice || "alloy";
      $("#apiOut").textContent = `text=${cfg.text?.configured} tts=${cfg.tts?.configured}\nkeys: ${cfg.text?.api_key_masked} / ${cfg.tts?.api_key_masked}`;
    } catch (_) {}
  }
  loadApiSettings();
  // 这几个按钮原先一个 try/catch 都没有：Key 填错、后端 500 都是「点了没反应」。
  async function guard(out, fn) {
    const el = $(out);
    try { await fn(el); } catch (e) { el.textContent = String(e.message || e); }
  }
  $("#btnSaveText").onclick = () => guard("#apiOut", async (el) => {
    el.textContent = "保存中…";
    const r = await api("/api/settings/apis/text", {
      method: "POST",
      body: JSON.stringify({ base_url: $("#txtBase").value, api_key: $("#txtKey").value, model: $("#txtModel").value }),
    });
    $("#txtKey").value = "";
    el.textContent = "已保存（Key 不回显）\n" + JSON.stringify(r.view || r, null, 2);
    loadApiSettings();
  });
  $("#btnSaveTts").onclick = () => guard("#apiOut", async (el) => {
    el.textContent = "保存中…";
    const r = await api("/api/settings/apis/tts", {
      method: "POST",
      body: JSON.stringify({
        base_url: $("#ttsBase").value,
        api_key: $("#ttsKey").value,
        model: $("#ttsModel").value,
        voice: $("#ttsVoice").value || "alloy",
      }),
    });
    $("#ttsKey").value = "";
    el.textContent = "已保存（Key 不回显）\n" + JSON.stringify(r.view || r, null, 2);
    loadApiSettings();
  });
  $("#btnProbeApi").onclick = () => guard("#apiOut", async (el) => {
    el.textContent = "探测中…（要出网，最多等 20 秒）";
    const r = await api("/api/settings/apis/probe", { method: "POST" });
    el.textContent = JSON.stringify(r, null, 2);
  });
  $("#btnManifest").onclick = () => guard("#offOut", async (el) => {
    el.textContent = "加载中…";
    const r = await api("/api/offline/manifest");
    el.textContent = JSON.stringify(r, null, 2);
  });
  $("#btnBundle").onclick = () => guard("#offOut", async (el) => {
    el.textContent = "加载中…";
    const r = await api("/api/offline/bundle");
    const m = r.material || {};
    el.textContent = `day=${r.day_key} etag=${r.etag}\n素材：${m.title || "无"}\n分段=${(r.segments||[]).length} audio_ready=${r.audio_ready}\n常驻=${(r.resident_sample||[]).length} 时间表=${(r.timetable||[]).length}\n${(m.body||"").slice(0,400)}`;
  });
  $("#btnReq").onclick = () => guard("#reqOut", async (el) => {
    const t = $("#reqTitle").value.trim();
    if (!t) { el.textContent = "先写组件名称"; return; }
    const r = await api("/api/components/request", {
      method: "POST",
      body: JSON.stringify({ title: t, description: "用户申请" }),
    });
    el.textContent = JSON.stringify(r, null, 2);
  });
}

function renderZizhao() {
  view.innerHTML = `
    <h1 class="page">自招素材</h1>
    <div class="panel">
      <div class="row">
        <button class="primary" id="btnToday">取今日素材</button>
        <button class="ghost" id="btnRefresh">换素材</button>
        <button class="ghost" id="btnChallenge">找茬清单</button>
      </div>
      <pre class="out" id="todayOut">未加载</pre>
    </div>
    <div class="panel">
      <h2>今日小测（错题→补漏）</h2>
      <div class="row"><button class="primary" id="btnQuiz">出题</button></div>
      <div id="quizBox"></div>
      <div class="row"><button class="ghost" id="btnGradeQuiz">交卷</button></div>
      <pre class="out" id="quizOut">听完素材立刻测；错题自动进补漏计划</pre>
    </div>
    <div class="panel">
      <h2>挂载对话（Agent）</h2>
      <textarea id="chatIn" placeholder="提问；可让它整理时间表/查常驻资料/搜邻仓"></textarea>
      <div class="row"><button class="primary" id="btnChat">发送</button></div>
      <pre class="out" id="chatOut">对话输出（纯文本，无 Markdown）</pre>
    </div>`;
  let mid = null;
  let quizQs = [];
  async function loadToday() {
    $("#todayOut").textContent = "加载中…";
    try {
      const m = await api("/api/material/today");
      mid = m.id;
      $("#todayOut").textContent = `《${m.title}》 ${m.domain}\n来源：${m.source} · ${m.day_key || ""}\ndegraded=${!!m.degraded}\n\n${(m.body||"").slice(0,1200)}`;
    } catch (e) {
      // 404 = 今天还没生成；不要留个静默空面板
      $("#todayOut").textContent = e.status === 404
        ? "今天还没有素材。点「换素材」立即生成一条（需要配好文本模型 Key）。"
        : String(e.message || e);
    }
  }
  $("#btnToday").onclick = loadToday;
  $("#btnRefresh").onclick = async () => {
    $("#todayOut").textContent = "生成中…（首次可能要 10-30 秒）";
    try {
      const m = await api("/api/material/refresh", { method: "POST", body: JSON.stringify({ domain: "any" }) });
      mid = m.id;
      $("#todayOut").textContent = `已切换《${m.title}》 degraded=${!!m.degraded}\n${(m.body||"").slice(0,800)}`;
    } catch (e) { $("#todayOut").textContent = String(e.message || e); }
  };
  $("#btnChallenge").onclick = async () => {
    if (!mid) { $("#todayOut").textContent = "先「取今日素材」"; return; }
    try {
      const r = await api("/api/material/challenge", { method: "POST", body: JSON.stringify({ material_id: mid, rounds: 3 }) });
      $("#todayOut").textContent = (r.questions||[]).map(q => `${q.round}.[${q.type}] ${q.ask}`).join("\n");
    } catch (e) { $("#todayOut").textContent = String(e.message || e); }
  };
  loadToday();  // 进页面就自动拉，别让用户猜按钮在哪
  $("#btnQuiz").onclick = async () => {
    if (!mid) { $("#quizOut").textContent = "先「取今日素材」再出题"; return; }
    try {
      const r = await api("/api/quiz/build?material_id=" + mid);
      quizQs = r.questions || [];
      $("#quizBox").innerHTML = quizQs.map(q => `
        <div class="list-item"><div style="flex:1"><b>${esc(q.type)}</b>
        <div>${esc(q.ask)}</div>
        <textarea data-q="${esc(q.id)}" placeholder="作答"></textarea></div></div>`).join("") || "<div class='muted'>无题</div>";
    } catch (e) { $("#quizOut").textContent = String(e.message || e); }
  };
  $("#btnGradeQuiz").onclick = async () => {
    if (!quizQs.length) { $("#quizOut").textContent = "先出题"; return; }
    const answers = quizQs.map(q => ({
      id: q.id,
      text: (document.querySelector(`[data-q="${CSS.escape(String(q.id))}"]`) || {}).value || "",
    }));
    const g = await api("/api/quiz/grade", {
      method: "POST",
      body: JSON.stringify({ material_id: mid || "", answers }),
    });
    $("#quizOut").textContent = `得分 ${g.score}/${g.total}  补漏+${g.gap_plan_added}\n${g.next_action}\n` +
      (g.results||[]).map(r => `${r.id}: ${r.passed ? "OK" : "MISS"} ${r.feedback}`).join("\n");
  };
  $("#btnChat").onclick = async () => {
    $("#chatOut").textContent = "思考中…";
    try {
      const sid = (state.user && state.user.id) ? state.user.id + ":web" : "web";
      const r = await api("/api/material/chat", {
        method: "POST",
        body: JSON.stringify({ session_id: sid, message: $("#chatIn").value, material_id: mid }),
      });
      const tools = (r.tool_trail||[]).map(t => `- ${t.name} ok=${t.ok}`).join("\n");
      $("#chatOut").textContent = `${r.reply}\n\n[degraded=${r.degraded} provider=${r.provider}]\n${tools}`;
    } catch (e) { $("#chatOut").textContent = String(e.message||e); }
  };
}

function renderEnglish() {
  view.innerHTML = `
    <h1 class="page">英语</h1>
    <div class="tabs">
      <button class="primary" id="tabCard">单词卡</button>
      <button class="ghost" id="tabRecite">段落背诵</button>
    </div>

    <div id="cardPane">
      <div class="panel">
        <div class="row">
          <select id="bank"><option value="gaokao">高考高频</option><option value="prep_collocations">介词搭配</option><option value="familiar_new_sense">熟词生义</option></select>
          <select id="mode"><option value="en2cn">英→中</option><option value="cn2en">中→英</option></select>
          <select id="src"><option value="new">新词（去已会）</option><option value="wrong">错词库</option><option value="mixed">全部</option></select>
          <select id="sort"><option value="freq">按频</option><option value="alpha">按字母</option></select>
          <button class="primary" id="btnCard">抽卡</button>
        </div>
        <div class="row"><span class="tag" id="cardPos"></span><span class="muted" id="bankStat"></span></div>
        <div class="panel" style="background:var(--panel-2)">
          <div id="cardFace" style="font-size:24px;min-height:44px">点「抽卡」开始</div>
          <div class="muted" id="cardHint"></div>
        </div>
        <div class="row">
          <button class="ghost" id="btnReveal">显示答案</button>
          <button class="ghost" id="btnVague">模糊·给名句</button>
        </div>
        <div class="row">
          <button class="primary" id="gKnown">会</button>
          <button class="ghost" id="gVague">模糊</button>
          <button class="danger" id="gWrong">不会</button>
        </div>
        <pre class="out" id="cardOut">按「会 / 模糊 / 不会」记进度；模糊和不会进错词库。</pre>
      </div>
    </div>

    <div id="recitePane" class="hidden">
      <div class="panel">
        <div class="row"><button class="primary" id="btnNext">抽一段</button><span id="recTitle" class="tag"></span></div>
        <pre class="out" id="passage">点抽题</pre>
        <textarea id="recIn" placeholder="默写/口述后粘贴"></textarea>
        <div class="row">
          <button class="primary" id="btnGrade">找茬批改</button>
          <button class="ghost" id="btnGradeLlm">+模型点评</button>
        </div>
        <pre class="out" id="gradeOut">批改结果</pre>
      </div>
    </div>`;

  $("#tabCard").onclick = () => {
    $("#cardPane").classList.remove("hidden");
    $("#recitePane").classList.add("hidden");
    $("#tabCard").className = "primary"; $("#tabRecite").className = "ghost";
  };
  $("#tabRecite").onclick = () => {
    $("#recitePane").classList.remove("hidden");
    $("#cardPane").classList.add("hidden");
    $("#tabRecite").className = "primary"; $("#tabCard").className = "ghost";
  };

  /* ---- 单词卡 ---- */
  let card = null;
  async function loadBanks() {
    try {
      const r = await api("/api/english/banks");
      $("#bankStat").textContent = `会 ${r.known} · 模糊 ${r.vague} · 错词 ${r.wrong_bank}`;
    } catch (_) {}
  }
  $("#btnCard").onclick = async () => {
    try {
      const q = `bank_id=${encodeURIComponent($("#bank").value)}&mode=${$("#mode").value}&source=${$("#src").value}&sort=${$("#sort").value}`;
      const r = await api("/api/english/card?" + q);
      if (r.empty) { card = null; $("#cardFace").textContent = r.note || "无卡片"; $("#cardOut").textContent = ""; return; }
      card = r.card || null;
      const face = card.mode === "cn2en" ? (card.cn || "（无释义）") : (card.word || "");
      $("#cardFace").textContent = face;
      $("#cardPos").textContent = card.pos || "";
      $("#cardHint").textContent = card.mode === "cn2en" ? "看释义拼写单词" : "想中文释义";
      if (r.progress) $("#bankStat").textContent = `会 ${r.progress.known} · 模糊 ${r.progress.vague} · 错词 ${r.progress.wrong}`;
    } catch (e) { $("#cardOut").textContent = String(e.message || e); }
  };
  $("#btnReveal").onclick = async () => {
    if (!card || !card.word) { $("#cardOut").textContent = "先抽卡"; return; }
    try {
      const r = await api(`/api/english/reveal?bank_id=${encodeURIComponent(card.bank_id)}&word=${encodeURIComponent(card.word)}`);
      const a = r.answer || {};
      $("#cardOut").textContent = [a.word, a.pos, a.cn].filter(Boolean).join(" · ") + (a.sentence ? `\n例句：${a.sentence}` : "");
    } catch (e) { $("#cardOut").textContent = String(e.message || e); }
  };
  $("#btnVague").onclick = async () => {
    if (!card || !card.word) { $("#cardOut").textContent = "先抽卡"; return; }
    try {
      const r = await api("/api/english/vague?word=" + encodeURIComponent(card.word));
      $("#cardOut").textContent = `名句：${r.sentence}\n选项：1) ${r.options[0]}   2) ${r.options[1]}\n（想好点「显示答案」核对）`;
    } catch (e) { $("#cardOut").textContent = String(e.message || e); }
  };
  const GRADE_CN = { known: "会", vague: "模糊", wrong: "不会" };
  async function gradeCard(g) {
    if (!card || !card.word) { $("#cardOut").textContent = "先抽卡"; return; }
    try {
      const r = await api("/api/english/grade", {
        method: "POST",
        body: JSON.stringify({ bank_id: card.bank_id, word: card.word, grade: g }),
      });
      // 别把 "wrong 已记录" 这种英文枚举直接甩给初三学生看
      $("#cardOut").textContent = `已记「${GRADE_CN[g] || g}」· 已会 ${r.known} · 错词库 ${r.wrong_count} 条${r.in_wrong_bank ? "（本词已在错词库）" : ""}`;
      await loadBanks();
      $("#btnCard").click();
    } catch (e) { $("#cardOut").textContent = String(e.message || e); }
  }
  $("#gKnown").onclick = () => gradeCard("known");
  $("#gVague").onclick = () => gradeCard("vague");
  $("#gWrong").onclick = () => gradeCard("wrong");
  loadBanks();

  /* ---- 段落背诵 ---- */
  let id = null;
  $("#btnNext").onclick = async () => {
    try {
      const it = await api("/api/recitation/next");
      id = it.id;
      $("#recTitle").textContent = it.title;
      $("#passage").textContent = it.passage;
    } catch (e) {
      // 后端 404 = 题库还没有条目（新用户必然遇到）。原样抛会把页面丢在
      // "点抽题" 状态、用户以为坏了。给出可执行动作。
      $("#gradeOut").textContent = e.status === 404
        ? "背诵题库还没有条目。去「资料库」粘贴一段英文，或在常驻资料里加一条 kind=english 的段落，再回来抽题。"
        : String(e.message || e);
    }
  };
  async function grade(llm) {
    if (!id) { $("#gradeOut").textContent = "先抽题"; return; }
    const g = await api("/api/recitation/grade", {
      method: "POST",
      body: JSON.stringify({ item_id: id, text: $("#recIn").value, use_llm: llm }),
    });
    let t = `coverage=${g.coverage} order=${g.order_ratio} passed=${g.passed}\n` + (g.issues||[]).join("\n") + `\n${g.next_action||""}`;
    if (g.coach) t += `\n\n${g.coach.comment||""}${g.coach.degraded?"\n(coach degraded)":""}`;
    $("#gradeOut").textContent = t;
  }
  $("#btnGrade").onclick = () => grade(false);
  $("#btnGradeLlm").onclick = () => grade(true);
}

function renderTools() {
  view.innerHTML = `
    <h1 class="page">小工具</h1>
    <div class="panel">
      <h2>语音 / 文本计算器</h2>
      <p class="hint">口述「三除以八再乘一百」→ 生成算式 → 本地安全求值（不出网算结果）。</p>
      <textarea id="calcIn" placeholder="3/8 百分之多少再乘12"></textarea>
      <div class="row">
        <button class="primary" id="btnCalc">计算</button>
        <span class="muted" id="calcProv"></span>
      </div>
      <pre class="out" id="calcOut">结果</pre>
    </div>
    <div class="panel">
      <h2>讲题（邻仓题目）</h2>
      <div class="row">
        <input id="qid" placeholder="邻仓 question_id" style="flex:1" />
        <input id="qask" placeholder="讲解这道题" style="flex:1" />
        <button class="primary" id="btnExplain">讲解</button>
      </div>
      <pre class="out" id="expOut">黑板稿（≤8 行，纯文本）</pre>
      <div class="row">
        <button class="primary" id="sayOk">对</button>
        <button class="ghost" id="sayNo">问题</button>
      </div>
    </div>`;
  let lastQid = "";
  $("#btnCalc").onclick = async () => {
    if (!$("#calcIn").value.trim()) { $("#calcOut").textContent = "先写要算的东西，如：三除以八再乘一百"; return; }
    $("#calcOut").textContent = "计算中…";
    try {
      const r = await api("/api/tools/calc", { method: "POST", body: JSON.stringify({ text: $("#calcIn").value }) });
      $("#calcOut").textContent = `口述：${r.spoken}\n算式：${r.expression}\n结果：${r.value}`;
      $("#calcProv").textContent = `provider=${r.provider}${r.degraded ? "（降级：正则抽算式）" : ""}`;
    } catch (e) { $("#calcOut").textContent = String(e.message || e); $("#calcProv").textContent = ""; }
  };
  $("#btnExplain").onclick = async () => {
    lastQid = $("#qid").value.trim();
    if (!lastQid) { $("#expOut").textContent = "先填 question_id"; return; }
    $("#expOut").textContent = "讲题中…";
    try {
      const r = await api("/api/tools/explain_question", {
        method: "POST",
        body: JSON.stringify({ question_id: lastQid, ask: $("#qask").value || "讲解这道题" }),
      });
      $("#expOut").textContent = r.blackboard + `\n\n[provider=${r.provider}]`;
    } catch (e) { $("#expOut").textContent = String(e.message || e); }
  };
  async function confirm(said) {
    if (!lastQid) { $("#expOut").textContent = "先讲解一题"; return; }
    try {
      const r = await api("/api/tools/explain_confirm", {
        method: "POST",
        body: JSON.stringify({ question_id: lastQid, said }),
      });
      $("#expOut").textContent = r.understood ? "已确认：换下一题" : (r.blackboard || "再讲一遍");
    } catch (e) { $("#expOut").textContent = String(e.message || e); }
  }
  $("#sayOk").onclick = () => confirm("对");
  $("#sayNo").onclick = () => confirm("问题");
}

function renderClassics() {
  view.innerHTML = `
    <h1 class="page">古诗文播放</h1>
    <div class="panel">
      <div class="row"><button class="primary" id="btnLoad">载入常驻·classics</button></div>
      <div id="list"></div>
    </div>
    <div class="panel">
      <h2>新增/朗读</h2>
      <div class="row"><input id="t" placeholder="篇名" /></div>
      <textarea id="b" placeholder="正文"></textarea>
      <div class="row">
        <button class="primary" id="btnSave">存常驻</button>
        <button class="ghost" id="btnTts">生成 MP3</button>
      </div>
      <pre class="out" id="out"></pre>
      <audio id="player" controls class="hidden" style="width:100%"></audio>
    </div>`;
  $("#btnLoad").onclick = async () => {
    const r = await api("/api/resident?kind=classics");
    $("#list").innerHTML = (r.items||[]).map(x => `
      <div class="list-item"><div><b>${esc(x.title)}</b><div class="muted">${esc((x.body||"").slice(0,80))}</div></div>
      <button class="ghost" data-play="${esc(x.id)}">用正文生成</button></div>`).join("") || "<div class='muted'>暂无</div>";
    $("#list").querySelectorAll("[data-play]").forEach(btn => {
      btn.onclick = async () => {
        const item = (r.items||[]).find(i => i.id === btn.dataset.play);
        if (!item) return;
        $("#t").value = item.title; $("#b").value = item.body || "";
        $("#out").textContent = "已载入正文，可点生成 MP3";
      };
    });
  };
  $("#btnSave").onclick = async () => {
    const r = await api("/api/resident", {
      method: "POST",
      body: JSON.stringify({ title: $("#t").value, body: $("#b").value, kind: "classics" }),
    });
    $("#out").textContent = JSON.stringify(r, null, 2);
  };
  $("#btnTts").onclick = async () => {
    const blob = new Blob([$("#b").value], { type: "text/plain" });
    const fd = new FormData();
    fd.append("file", blob, ($("#t").value || "classics") + ".txt");
    fd.append("make_mp3", "true");
    fd.append("component", "classics");
    const res = await fetch("/api/media/upload", { method: "POST", body: fd, credentials: "same-origin" });
    const data = await res.json();
    $("#out").textContent = JSON.stringify(data, null, 2);
    const p = data.item && data.item.mp3_path;
    if (data.item && !data.item.mp3_degraded && data.item.id) {
      // 通过 media detail 拿不到 path；用统一下载接口（见后端若未暴露则提示）
      $("#out").textContent += "\n\n若服务端已生成 MP3，可在 /api/media 列表查看状态。";
    }
  };
}

function renderTimetable() {
  view.innerHTML = `
    <h1 class="page">时间表</h1>
    <div class="panel">
      <div class="row">
        <select id="wd">
          <option value="0">周一</option><option value="1">周二</option><option value="2">周三</option>
          <option value="3">周四</option><option value="4">周五</option><option value="5">周六</option><option value="6">周日</option>
        </select>
        <input id="st" type="time" value="08:00" />
        <input id="en" type="time" value="09:00" />
      </div>
      <div class="row"><input id="ti" placeholder="事项" /><button class="primary" id="btnAdd">添加</button><button class="ghost" id="btnReload">刷新</button></div>
      <div id="tt"></div>
    </div>
    <div class="panel">
      <h2>Agent 批量整理</h2>
      <textarea id="bulk" placeholder="周一 08:00-09:00 数学补漏&#10;周二 19:00-19:30 英语背诵"></textarea>
      <div class="row"><button class="primary" id="btnBulk">解析写入</button></div>
      <pre class="out" id="bulkOut"></pre>
    </div>`;
  async function load() {
    const r = await api("/api/timetable");
    const days = r.weekdays || [];
    const by = {};
    (r.items||[]).forEach(it => { (by[it.weekday] = by[it.weekday] || []).push(it); });
    // 今天是周几：JS getDay() 周日=0，服务端 weekday 周一=0，需要换算，否则高亮会错一天
    const todayIdx = (new Date(Date.now() + clockSkewMs).getDay() + 6) % 7;
    $("#tt").innerHTML = days.map((d,i) => `
      <div class="list-item${i === todayIdx ? " is-today" : ""}">
      <div><b>${d}</b>${i === todayIdx ? '<div class="tag ok">今天</div>' : ""}</div>
      <div style="flex:1">${(by[i]||[]).map(x => `<div>${esc(x.start)}-${esc(x.end)} ${esc(x.title)}</div>`).join("") || "<span class='muted'>—</span>"}</div></div>`).join("");
    const sel = $("#wd");
    if (sel) sel.value = String(todayIdx);  // 默认就选今天，少点一次
  }
  $("#btnReload").onclick = load;
  $("#btnAdd").onclick = async () => {
    await api("/api/timetable", {
      method: "POST",
      body: JSON.stringify({ title: $("#ti").value, weekday: +$("#wd").value, start: $("#st").value, end: $("#en").value }),
    });
    $("#ti").value = "";
    load();
  };
  $("#btnBulk").onclick = async () => {
    const r = await api("/api/timetable/bulk", { method: "POST", body: JSON.stringify({ text: $("#bulk").value }) });
    $("#bulkOut").textContent = JSON.stringify(r, null, 2);
    load();
  };
  load();
}

function renderLibrary() {
  view.innerHTML = `
    <h1 class="page">资料库</h1>
    <div class="panel">
      <h2>上传（图片 OCR / 文档抽取 / 可选 MP3）</h2>
      <div class="row">
        <input type="file" id="file" accept=".png,.jpg,.jpeg,.webp,.txt,.md,.pdf,.docx" />
      </div>
      <div class="row">
        <label><input type="checkbox" id="mp3" checked /> 生成 MP3</label>
        <button class="primary" id="btnUp">上传整理</button>
      </div>
      <pre class="out" id="upOut"></pre>
    </div>
    <div class="panel">
      <h2>常驻资料</h2>
      <div class="row"><input id="rt" placeholder="标题" /><button class="ghost" id="btnResAdd">添加笔记</button><button class="ghost" id="btnResLoad">刷新</button></div>
      <div id="res"></div>
    </div>
    <div class="panel">
      <h2>媒体文件</h2>
      <div id="media"></div>
    </div>`;
  $("#btnUp").onclick = async () => {
    const f = $("#file").files[0];
    if (!f) { $("#upOut").textContent = "先选文件"; return; }
    const fd = new FormData();
    fd.append("file", f);
    fd.append("make_mp3", $("#mp3").checked ? "true" : "false");
    fd.append("component", "library");
    const res = await fetch("/api/media/upload", { method: "POST", body: fd, credentials: "same-origin" });
    const data = await res.json();
    $("#upOut").textContent = JSON.stringify(data, null, 2);
    refreshMedia();
  };
  $("#btnResAdd").onclick = async () => {
    await api("/api/resident", { method: "POST", body: JSON.stringify({ title: $("#rt").value, body: "", kind: "note" }) });
    $("#rt").value = ""; refreshRes();
  };
  $("#btnResLoad").onclick = refreshRes;
  async function refreshRes() {
    const r = await api("/api/resident");
    $("#res").innerHTML = (r.items||[]).slice(0,20).map(x => `
      <div class="list-item"><div><b>${esc(x.title)}</b> <span class="tag">${esc(x.kind)}</span>
      <div class="muted">${esc((x.body||"").slice(0,100))}</div></div>
      <button class="danger" data-del="${x.id}">删</button></div>`).join("") || "<div class='muted'>空</div>";
    $("#res").querySelectorAll("[data-del]").forEach(b => {
      b.onclick = async () => { await api("/api/resident/"+b.dataset.del, { method: "DELETE" }); refreshRes(); };
    });
  }
  async function refreshMedia() {
    const r = await api("/api/media");
    $("#media").innerHTML = (r.items||[]).map(x => `
      <div class="list-item"><div><b>${esc(x.filename)}</b>
      <span class="tag ${x.degraded?"warn":"ok"}">${x.degraded?"degraded":"ok"}</span>
      <div class="muted">${esc(x.kind)} · ${esc(x.text_preview||"")}</div></div></div>`).join("") || "<div class='muted'>空</div>";
  }
  refreshRes(); refreshMedia();
}

function renderDevices() {
  view.innerHTML = `
    <h1 class="page">设备（ESP-S3）</h1>
    <div class="panel">
      <p class="muted">为小盒子签发 PassKey，烧录后调用 POST /api/auth/device/login 换 sid。</p>
      <div class="row"><input id="dname" value="esp-s3-paper" /><button class="primary" id="btnProv">签发 PassKey</button></div>
      <pre class="out" id="provOut">PassKey 仅显示一次</pre>
    </div>
    <div class="panel"><h2>已绑定设备</h2><div id="devs"></div></div>`;
  $("#btnProv").onclick = async () => {
    const r = await api("/api/auth/device/provision", { method: "POST", body: JSON.stringify({ name: $("#dname").value }) });
    $("#provOut").textContent = `device_id: ${r.device_id}\npasskey: ${r.passkey}\n（请立刻烧录/保存，刷新后不可再看）`;
    loadDevs();
  };
  async function loadDevs() {
    const r = await api("/api/auth/devices");
    $("#devs").innerHTML = (r.items||[]).map(d => `
      <div class="list-item"><div><b>${d.name}</b><div class="muted">${d.device_id}</div></div>
      <button class="danger" data-rev="${d.device_id}">吊销</button></div>`).join("") || "<div class='muted'>无</div>";
    $("#devs").querySelectorAll("[data-rev]").forEach(b => {
      b.onclick = async () => {
        await api("/api/auth/device/revoke", { method: "POST", body: JSON.stringify({ device_id: b.dataset.rev }) });
        loadDevs();
      };
    });
  }
  loadDevs();
}

const VIEWS = {
  home: renderHome,
  zizhao: renderZizhao,
  english: renderEnglish,
  tools: renderTools,
  classics: renderClassics,
  timetable: renderTimetable,
  library: renderLibrary,
  devices: renderDevices,
};

function render() {
  const route = parseHash();
  if (!state.user) { renderLogin(); return; }
  renderDock();
  const fn = VIEWS[route] || renderHome;
  fn();
}

window.addEventListener("hashchange", render);

(async function init() {
  startClock();  // 先起时钟：登录页也要能看到时间/日期
  await bootstrap();
  if (!state.user) setRoute("login");
  else render();
})();
