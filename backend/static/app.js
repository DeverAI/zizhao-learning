/* 自招学习平台 SPA：主页组件格 + 各组件页 + 登录 */
const $ = (s, r = document) => r.querySelector(s);
const view = $("#view");
const dock = $("#dock");
const userLabel = $("#userLabel");
const btnLogout = $("#btnLogout");

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
    `<button data-id="${c.id}" class="${state.route === c.id ? "active" : ""}">${c.icon}<div>${c.name}</div></button>`
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
  view.innerHTML = `
    <h1 class="page">主页</h1>
    <p class="muted">点组件进入。可在资料库上传文件让 AI 整理；时间表可对话整理。</p>
    <div class="card-grid">
      ${cards.map(c => `
        <div class="card" data-go="${c.id}">
          <div class="icon">${c.icon}</div>
          <h3>${c.name}</h3>
          <p>${c.description}</p>
        </div>`).join("")}
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
      <div><b>${c.name}</b> <span class="muted">${c.id}</span><div class="muted">${c.description}</div></div>
      <button class="ghost" data-toggle="${c.id}">${enabled.has(c.id) ? "已启用" : "启用"}</button>
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
  $("#btnReq").onclick = async () => {
    const r = await api("/api/components/request", {
      method: "POST",
      body: JSON.stringify({ title: $("#reqTitle").value, description: "用户申请" }),
    });
    $("#reqOut").textContent = JSON.stringify(r, null, 2);
  };
  // 自注册 API + 离线包
  try {
    const view = await api("/api/settings/apis");
    $("#txtBase").value = view.text?.base_url || "";
    $("#txtModel").value = view.text?.model || "";
    $("#ttsBase").value = view.tts?.base_url || "";
    $("#ttsModel").value = view.tts?.model || "";
    $("#ttsVoice").value = view.tts?.voice || "alloy";
    $("#apiOut").textContent = `text=${view.text?.configured} tts=${view.tts?.configured}\nkeys: ${view.text?.api_key_masked} / ${view.tts?.api_key_masked}`;
  } catch (_) {}
  $("#btnSaveText").onclick = async () => {
    const r = await api("/api/settings/apis/text", {
      method: "POST",
      body: JSON.stringify({ base_url: $("#txtBase").value, api_key: $("#txtKey").value, model: $("#txtModel").value }),
    });
    $("#apiOut").textContent = JSON.stringify(r.view || r, null, 2);
  };
  $("#btnSaveTts").onclick = async () => {
    const r = await api("/api/settings/apis/tts", {
      method: "POST",
      body: JSON.stringify({
        base_url: $("#ttsBase").value,
        api_key: $("#ttsKey").value,
        model: $("#ttsModel").value,
        voice: $("#ttsVoice").value || "alloy",
      }),
    });
    $("#apiOut").textContent = JSON.stringify(r.view || r, null, 2);
  };
  $("#btnProbeApi").onclick = async () => {
    $("#apiOut").textContent = "探测中…";
    const r = await api("/api/settings/apis/probe", { method: "POST" });
    $("#apiOut").textContent = JSON.stringify(r, null, 2);
  };
  $("#btnManifest").onclick = async () => {
    const r = await api("/api/offline/manifest");
    $("#offOut").textContent = JSON.stringify(r, null, 2);
  };
  $("#btnBundle").onclick = async () => {
    const r = await api("/api/offline/bundle");
    const m = r.material || {};
    $("#offOut").textContent = `day=${r.day_key} etag=${r.etag}\n素材：${m.title || "无"}\n分段=${(r.segments||[]).length} audio_ready=${r.audio_ready}\n常驻=${(r.resident_sample||[]).length} 时间表=${(r.timetable||[]).length}\n${(m.body||"").slice(0,400)}`;
  };
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
  $("#btnToday").onclick = async () => {
    const m = await api("/api/material/today");
    mid = m.id;
    $("#todayOut").textContent = `《${m.title}》 ${m.domain}\n来源：${m.source}\ndegraded=${!!m.degraded}\n\n${(m.body||"").slice(0,1200)}`;
  };
  $("#btnRefresh").onclick = async () => {
    const m = await api("/api/material/refresh", { method: "POST", body: JSON.stringify({ domain: "any" }) });
    mid = m.id;
    $("#todayOut").textContent = `已切换《${m.title}》\n${(m.body||"").slice(0,800)}`;
  };
  $("#btnChallenge").onclick = async () => {
    const r = await api("/api/material/challenge", { method: "POST", body: JSON.stringify({ material_id: mid, rounds: 3 }) });
    $("#todayOut").textContent = (r.questions||[]).map(q => `${q.round}.[${q.type}] ${q.ask}`).join("\n");
  };
  $("#btnQuiz").onclick = async () => {
    const r = await api("/api/quiz/build?material_id=" + (mid || ""));
    quizQs = r.questions || [];
    $("#quizBox").innerHTML = quizQs.map(q => `
      <div class="list-item"><div style="flex:1"><b>${q.type}</b>
      <div>${q.ask}</div>
      <textarea data-q="${q.id}" placeholder="作答"></textarea></div></div>`).join("") || "<div class='muted'>无题</div>";
  };
  $("#btnGradeQuiz").onclick = async () => {
    const answers = quizQs.map(q => ({
      id: q.id,
      text: (document.querySelector(`[data-q="${q.id}"]`) || {}).value || "",
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
    <h1 class="page">英语背诵</h1>
    <div class="panel">
      <div class="row"><button class="primary" id="btnNext">抽一段</button><span id="recTitle" class="tag"></span></div>
      <pre class="out" id="passage">点抽题</pre>
      <textarea id="recIn" placeholder="默写/口述后粘贴"></textarea>
      <div class="row">
        <button class="primary" id="btnGrade">找茬批改</button>
        <button class="ghost" id="btnGradeLlm">+模型点评</button>
      </div>
      <pre class="out" id="gradeOut">批改结果</pre>
    </div>`;
  let id = null;
  $("#btnNext").onclick = async () => {
    const it = await api("/api/recitation/next");
    id = it.id;
    $("#recTitle").textContent = it.title;
    $("#passage").textContent = it.passage;
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
      <div class="list-item"><div><b>${x.title}</b><div class="muted">${(x.body||"").slice(0,80)}</div></div>
      <button class="ghost" data-play="${x.id}">用正文生成</button></div>`).join("") || "<div class='muted'>暂无</div>";
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
    $("#tt").innerHTML = days.map((d,i) => `
      <div class="list-item"><div><b>${d}</b></div>
      <div style="flex:1">${(by[i]||[]).map(x => `<div>${x.start}-${x.end} ${x.title}</div>`).join("") || "<span class='muted'>—</span>"}</div></div>`).join("");
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
      <div class="list-item"><div><b>${x.title}</b> <span class="tag">${x.kind}</span>
      <div class="muted">${(x.body||"").slice(0,100)}</div></div>
      <button class="danger" data-del="${x.id}">删</button></div>`).join("") || "<div class='muted'>空</div>";
    $("#res").querySelectorAll("[data-del]").forEach(b => {
      b.onclick = async () => { await api("/api/resident/"+b.dataset.del, { method: "DELETE" }); refreshRes(); };
    });
  }
  async function refreshMedia() {
    const r = await api("/api/media");
    $("#media").innerHTML = (r.items||[]).map(x => `
      <div class="list-item"><div><b>${x.filename}</b>
      <span class="tag ${x.degraded?"warn":"ok"}">${x.degraded?"degraded":"ok"}</span>
      <div class="muted">${x.kind} · ${x.text_preview||""}</div></div></div>`).join("") || "<div class='muted'>空</div>";
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
  await bootstrap();
  if (!state.user) setRoute("login");
  else render();
})();
