"use strict";

const api = (p, opt) => fetch("/api" + p, opt).then(async (r) => {
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || r.statusText);
  return r.json();
});

const $ = (s) => document.querySelector(s);
const hoje = () => new Date().toISOString().slice(0, 10);
const HORIZONTE_DIAS = 90;

const estado = { filtro: null, status: "Prateleira", q: "", offset: 0, fim: false };

// --------------------------------------------------------------------------
// Navegação por abas
// --------------------------------------------------------------------------
document.querySelectorAll(".tabbar button").forEach((b) => {
  b.addEventListener("click", () => mostrarAba(b.dataset.tab));
});
function mostrarAba(nome) {
  document.querySelectorAll(".tabbar button").forEach((b) =>
    b.classList.toggle("active", b.dataset.tab === nome));
  $("#tab-cadastrar").classList.toggle("hidden", nome !== "cadastrar");
  $("#tab-lista").classList.toggle("hidden", nome !== "lista");
  if (nome === "lista") recarregarLista();
}

// --------------------------------------------------------------------------
// Estatísticas
// --------------------------------------------------------------------------
async function carregarStats() {
  try {
    const s = await api("/stats");
    $("#stats").innerHTML = `
      <div class="stat"><span class="num">${s.prateleira}</span><span class="lbl">Na prateleira</span></div>
      <div class="stat aviso"><span class="num">${s.vencendo}</span><span class="lbl">Vencem em 90d</span></div>
      <div class="stat alerta"><span class="num">${s.vencidos}</span><span class="lbl">Vencidos</span></div>
      <div class="stat"><span class="num">${s.total}</span><span class="lbl">Total</span></div>`;
  } catch (e) { /* silencioso */ }
}

// --------------------------------------------------------------------------
// Formulário de cadastro
// --------------------------------------------------------------------------
async function prepararFormulario() {
  $("#data-hoje").textContent = hoje().split("-").reverse().join("/");
  try {
    const { proxima_etiqueta } = await api("/proxima-etiqueta");
    $("#proxima-etiqueta").textContent = proxima_etiqueta;
  } catch (e) {}
  try {
    const sug = await api("/sugestoes");
    preencherDatalist("lista-marcas", sug.marcas);
    preencherDatalist("lista-series", sug.series);
    preencherDatalist("lista-cores", sug.cores);
    window._sugestoes = sug;
  } catch (e) {}
}
function preencherDatalist(id, valores) {
  $("#" + id).innerHTML = (valores || []).map((v) => `<option value="${escAttr(v)}">`).join("");
}

$("#fotos").addEventListener("change", (e) => {
  const prev = $("#preview-fotos");
  prev.innerHTML = "";
  [...e.target.files].forEach((f) => {
    const img = document.createElement("img");
    img.src = URL.createObjectURL(f);
    prev.appendChild(img);
  });
});

$("#form-cadastro").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = $("#form-cadastro button[type=submit]");
  const msg = $("#msg-cadastro");
  btn.disabled = true; msg.textContent = "Salvando..."; msg.className = "msg";

  const fd = new FormData();
  fd.append("marca", $("#marca").value);
  fd.append("serie", $("#serie").value);
  fd.append("cor", $("#cor").value);
  fd.append("validade", $("#validade").value);
  [...$("#fotos").files].forEach((f) => fd.append("fotos", f));

  try {
    const novo = await api("/esmaltes", { method: "POST", body: fd });
    msg.textContent = `✓ Esmalte nº ${novo.etiqueta} cadastrado!`;
    msg.className = "msg ok";
    e.target.reset();
    $("#preview-fotos").innerHTML = "";
    prepararFormulario();
    carregarStats();
  } catch (err) {
    msg.textContent = "Erro: " + err.message;
    msg.className = "msg erro";
  } finally {
    btn.disabled = false;
  }
});

// --------------------------------------------------------------------------
// Lista + filtros
// --------------------------------------------------------------------------
const FILTROS = [
  { id: "prateleira", lbl: "Na prateleira", status: "Prateleira", filtro: null },
  { id: "vencendo", lbl: "Vencendo", status: null, filtro: "vencendo" },
  { id: "vencidos", lbl: "Vencidos", status: null, filtro: "vencidos" },
  { id: "removidos", lbl: "Removidos", status: "Removido", filtro: null },
  { id: "todos", lbl: "Todos", status: null, filtro: null },
];
let filtroAtivo = "prateleira";

function montarChips() {
  $("#chips").innerHTML = FILTROS.map((f) =>
    `<button class="chip ${f.id === filtroAtivo ? "active" : ""}" data-id="${f.id}">${f.lbl}</button>`
  ).join("");
  $("#chips").querySelectorAll(".chip").forEach((c) =>
    c.addEventListener("click", () => { filtroAtivo = c.dataset.id; recarregarLista(); }));
}

let buscaTimer;
$("#busca").addEventListener("input", (e) => {
  clearTimeout(buscaTimer);
  buscaTimer = setTimeout(() => { estado.q = e.target.value.trim(); recarregarLista(); }, 300);
});

function recarregarLista() {
  estado.offset = 0; estado.fim = false;
  $("#lista").innerHTML = "";
  montarChips();
  carregarLista();
}

async function carregarLista() {
  const f = FILTROS.find((x) => x.id === filtroAtivo);
  const params = new URLSearchParams({ limite: 50, offset: estado.offset });
  if (f.status) params.set("status", f.status);
  if (f.filtro) params.set("filtro", f.filtro);
  if (estado.q) params.set("q", estado.q);
  params.set("ordem", f.filtro ? "validade" : "etiqueta");

  try {
    const itens = await api("/esmaltes?" + params);
    if (estado.offset === 0 && itens.length === 0)
      $("#lista").innerHTML = `<p style="text-align:center;color:#888;padding:30px">Nenhum esmalte encontrado.</p>`;
    itens.forEach((it) => $("#lista").appendChild(montarItem(it)));
    estado.offset += itens.length;
    estado.fim = itens.length < 50;
    $("#carregar-mais").classList.toggle("hidden", estado.fim);
  } catch (e) {}
}
$("#carregar-mais").addEventListener("click", carregarLista);

function statusValidade(it) {
  if (!it.validade) return null;
  const dias = Math.round((new Date(it.validade) - new Date(hoje())) / 86400000);
  if (dias < 0) return { cls: "vencido", txt: "Vencido" };
  if (dias <= HORIZONTE_DIAS) return { cls: "vencendo", txt: `Vence em ${dias}d` };
  return { cls: "ok", txt: "No prazo" };
}

function montarItem(it) {
  const div = document.createElement("div");
  div.className = "item";
  const thumb = it.fotos && it.fotos.length
    ? `<img class="thumb" src="/uploads/${it.fotos[0]}" />`
    : `<div class="thumb">💅</div>`;
  let badge = "";
  if (it.status === "Prateleira") {
    const sv = statusValidade(it);
    if (sv) badge = `<span class="badge ${sv.cls}">${sv.txt}</span>`;
  } else {
    badge = `<span class="badge removido">${it.status}${it.motivo ? " · " + it.motivo : ""}</span>`;
  }
  div.innerHTML = `
    ${thumb}
    <div class="info">
      <div class="titulo">${esc(it.marca || "—")} ${it.serie ? "· " + esc(it.serie) : ""}</div>
      <div class="sub">${esc(it.cor || "—")} ${it.validade ? "· val. " + fmtMes(it.validade) : ""}</div>
      ${badge}
    </div>
    <span class="etq">#${it.etiqueta}</span>`;
  div.addEventListener("click", () => abrirModal(it.id));
  return div;
}

// --------------------------------------------------------------------------
// Modal de detalhes / edição
// --------------------------------------------------------------------------
$("#fechar-modal").addEventListener("click", fecharModal);
$("#modal").addEventListener("click", (e) => { if (e.target.id === "modal") fecharModal(); });
function fecharModal() { $("#modal").classList.add("hidden"); }

async function abrirModal(id) {
  const it = await api("/esmaltes/" + id);
  const sv = statusValidade(it);
  const fotos = (it.fotos || []).map((f) => `<img src="/uploads/${f}" />`).join("")
    || `<div style="padding:20px;color:#aaa">Sem fotos</div>`;
  const naPrateleira = it.status === "Prateleira";

  $("#modal-corpo").innerHTML = `
    <h2>${esc(it.marca || "—")} <span class="etq">#${it.etiqueta}</span></h2>
    <div class="modal-fotos">${fotos}</div>
    <label style="font-weight:600;font-size:.8rem">Adicionar fotos
      <input type="file" id="add-fotos" accept="image/*" capture="environment" multiple />
    </label>
    <div class="linha-detalhe"><span>Série</span><span>${esc(it.serie || "—")}</span></div>
    <div class="linha-detalhe"><span>Cor</span><span>${esc(it.cor || "—")}</span></div>
    <div class="linha-detalhe"><span>Validade</span><span>${it.validade ? fmtMes(it.validade) : "—"} ${sv ? `<span class="badge ${sv.cls}">${sv.txt}</span>` : ""}</span></div>
    <div class="linha-detalhe"><span>Cadastro</span><span>${fmtData(it.data_cadastro)}</span></div>
    <div class="linha-detalhe"><span>Status</span><span>${esc(it.status)}</span></div>
    ${it.motivo ? `<div class="linha-detalhe"><span>Motivo</span><span>${esc(it.motivo)}</span></div>` : ""}
    ${it.data_removido ? `<div class="linha-detalhe"><span>Removido em</span><span>${fmtData(it.data_removido)}</span></div>` : ""}

    ${naPrateleira ? `
      <label>Motivo da remoção
        <select id="motivo-remocao">
          ${(window._sugestoes?.motivos || ["Acabou","Vencido","Ficou duro","Perdido"]).map((m) => `<option>${m}</option>`).join("")}
        </select>
      </label>` : ""}

    <div class="acoes">
      ${naPrateleira
        ? `<button class="btn-remover" id="btn-remover">Retirar da prateleira</button>`
        : `<button class="btn-voltar" id="btn-voltar">Voltar p/ prateleira</button>`}
      <button class="btn-excluir" id="btn-excluir">Excluir</button>
    </div>`;

  $("#add-fotos").addEventListener("change", async (e) => {
    if (!e.target.files.length) return;
    const fd = new FormData();
    [...e.target.files].forEach((f) => fd.append("fotos", f));
    await api(`/esmaltes/${id}/fotos`, { method: "POST", body: fd });
    abrirModal(id);
    recarregarLista();
  });

  const btnRem = $("#btn-remover");
  if (btnRem) btnRem.addEventListener("click", async () => {
    await api("/esmaltes/" + id, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: "Removido", motivo: $("#motivo-remocao").value }),
    });
    fecharModal(); recarregarLista(); carregarStats();
  });

  const btnVolta = $("#btn-voltar");
  if (btnVolta) btnVolta.addEventListener("click", async () => {
    await api("/esmaltes/" + id, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: "Prateleira" }),
    });
    fecharModal(); recarregarLista(); carregarStats();
  });

  $("#btn-excluir").addEventListener("click", async () => {
    if (!confirm("Excluir este esmalte e suas fotos? Esta ação não pode ser desfeita.")) return;
    await api("/esmaltes/" + id, { method: "DELETE" });
    fecharModal(); recarregarLista(); carregarStats();
  });

  $("#modal").classList.remove("hidden");
}

// --------------------------------------------------------------------------
// Utilitários
// --------------------------------------------------------------------------
function esc(s) { return String(s).replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }
function escAttr(s) { return esc(s); }
function fmtData(iso) { return iso ? iso.slice(0, 10).split("-").reverse().join("/") : "—"; }
function fmtMes(iso) { const [a, m] = iso.split("-"); return `${m}/${a}`; }

// --------------------------------------------------------------------------
// Boot
// --------------------------------------------------------------------------
carregarStats();
prepararFormulario();
montarChips();

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/service-worker.js").catch(() => {});
}
