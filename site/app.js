import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const config = window.APP_CONFIG || {};
const configured = Boolean(config.supabaseUrl && config.supabaseAnonKey);
const supabase = configured ? createClient(config.supabaseUrl, config.supabaseAnonKey) : null;
const authScreen = document.querySelector("#auth-screen");
const appScreen = document.querySelector("#app-screen");
const notice = document.querySelector("#notice");
const loginForm = document.querySelector("#login-form");
const signupForm = document.querySelector("#signup-form");
const testList = document.querySelector("#test-list");
let currentUser = null;
let currentProfile = null;
let tests = [];
let activeTestDate = "";
let showPastTests = false;
let authMode = "login";
let noticeTimeout;

function showNotice(message, isError = false) {
  notice.textContent = message;
  notice.classList.toggle("is-error", isError);
  notice.hidden = false;
  window.clearTimeout(noticeTimeout);
  noticeTimeout = window.setTimeout(() => { notice.hidden = true; }, 6000);
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[character]);
}

function setAuthMode(mode) {
  authMode = mode;
  const isLogin = mode === "login";
  loginForm.hidden = !isLogin;
  signupForm.hidden = isLogin;
  document.querySelectorAll("[data-auth-tab]").forEach((tab) => {
    const selected = tab.dataset.authTab === mode;
    tab.classList.toggle("is-active", selected);
    tab.setAttribute("aria-selected", String(selected));
  });
}

function setPendingMode(isPending) {
  document.querySelector("#pending-panel").hidden = !isPending;
  document.querySelector(".auth-tabs").hidden = isPending;
  if (isPending) {
    loginForm.hidden = true;
    signupForm.hidden = true;
  } else {
    setAuthMode(authMode);
  }
}

function showSignedOut() {
  currentUser = null;
  currentProfile = null;
  authScreen.hidden = false;
  appScreen.hidden = true;
  setPendingMode(false);
  document.querySelector("#config-help").hidden = configured;
}

function showPending() {
  authScreen.hidden = false;
  appScreen.hidden = true;
  setPendingMode(true);
}

function showSignedIn() {
  const isProfessor = currentProfile.role === "professor";
  authScreen.hidden = true;
  appScreen.hidden = false;
  document.querySelector("#account-label").textContent = currentProfile.username;
  document.querySelector("#role-label").textContent = isProfessor ? "Perfil de professor" : "Perfil de aluno";
  document.querySelector("#manage-link").hidden = !isProfessor;
  if (isProfessor) void updatePendingCount();
  document.querySelector("#import-button").hidden = true;
  document.querySelector("#day-filter-controls").hidden = !isProfessor;
  if (!isProfessor) {
    activeTestDate = "";
    document.querySelector("#test-day-filter").value = "";
  }
  document.querySelector("#home-view").hidden = false;
  document.querySelector("#users-view").hidden = true;
}

async function loadProfile() {
  const { data, error } = await supabase.from("profiles").select("id, username, role, approved").eq("id", currentUser.id).single();
  if (error) throw error;
  currentProfile = data;
  if (data.role !== "professor" && !data.approved) return showPending();
  showSignedIn();
  await loadTests();
}

async function loadTests() {
  const { data, error } = await supabase.from("tests").select("id, user_id, name, school_year, subject, test_date, grade").order("test_date", { ascending: true });
  if (error) throw error;
  tests = data || [];
  renderTests();
}

function localDateString(date = new Date()) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function filteredTests() {
  const filter = document.querySelector("#student-filter").value.trim().toLocaleLowerCase("pt-PT");
  const today = localDateString();
  return tests.filter((item) =>
    (!filter || item.name.toLocaleLowerCase("pt-PT").includes(filter)) &&
    (!activeTestDate || item.test_date === activeTestDate) &&
    (showPastTests || item.test_date >= today || item.test_date === activeTestDate)
  );
}

function renderTests() {
  const visibleTests = filteredTests();
  const hasPastTests = tests.some((item) => item.test_date < localDateString());
  document.querySelector("#record-count").textContent = String(visibleTests.length);
  const togglePastTests = document.querySelector("#toggle-past-tests");
  togglePastTests.hidden = !hasPastTests;
  togglePastTests.textContent = showPastTests ? "Ocultar antigos" : "Mostrar antigos";
  togglePastTests.setAttribute("aria-pressed", String(showPastTests));
  const hasFilter = document.querySelector("#student-filter").value.trim().length > 0 || Boolean(activeTestDate) || showPastTests;
  document.querySelector("#clear-filter").hidden = !hasFilter;
  document.querySelector("#export-button").hidden = !hasFilter;
  if (!visibleTests.length) {
    testList.innerHTML = tests.length
      ? `<p class="empty-state">${hasPastTests && !showPastTests && !activeTestDate
        ? "Não há testes futuros para os filtros selecionados. Os testes antigos estão ocultos."
        : "Não há testes para os filtros selecionados."}</p>`
      : '<p class="empty-state">Ainda não existem testes registados.</p>';
    return;
  }

  const isProfessor = currentProfile?.role === "professor";
  testList.innerHTML = visibleTests.map((item) => {
    const formattedDate = new Date(`${item.test_date}T00:00:00`).toLocaleDateString("pt-PT");
    const gradeValue = item.grade === null ? "" : String(item.grade);
    return `<article class="test-item">
      <div><strong class="student-name">${escapeHtml(item.name)}</strong><span class="student-meta">${escapeHtml(item.school_year)} · ${escapeHtml(item.subject)}</span></div>
      <time class="test-date" datetime="${escapeHtml(item.test_date)}">${formattedDate}</time>
      <form class="grade-area" data-grade-form="${escapeHtml(item.id)}">
        <label class="visually-hidden" for="grade-${escapeHtml(item.id)}">Nota de ${escapeHtml(item.name)}</label>
        <input class="grade-input" id="grade-${escapeHtml(item.id)}" name="grade" type="number" min="0" max="20" step="0.1" value="${escapeHtml(gradeValue)}" placeholder="Nota">
        <button class="button grade-button" type="submit">Guardar nota</button>
        ${isProfessor ? `<button class="button grade-button button-danger" type="button" data-delete-test="${escapeHtml(item.id)}">Apagar</button>` : ""}
      </form>
    </article>`;
  }).join("");
}

async function updatePendingCount() {
  const { count, error } = await supabase.from("profiles").select("id", { count: "exact", head: true }).eq("approved", false).neq("role", "professor");
  if (error) return;
  document.querySelector("#manage-link").textContent = count ? `Utilizadores (${count} pendente${count === 1 ? "" : "s"})` : "Utilizadores";
}

async function loadProfiles() {
  const { data, error } = await supabase.from("profiles").select("id, username, role, approved, created_at").order("username");
  if (error) {
    showNotice(error.message, true);
    return;
  }
  const isPending = (profile) => profile.role !== "professor" && !profile.approved;
  const pending = (data || []).filter(isPending).sort((a, b) => a.created_at.localeCompare(b.created_at));
  const approved = (data || []).filter((profile) => !isPending(profile));
  document.querySelector("#pending-count").textContent = String(pending.length);
  document.querySelector("#pending-list").innerHTML = pending.map((profile) => `
    <div class="pending-row">
      <span><strong>${escapeHtml(profile.username)}</strong><span class="pending-date">Pedido em ${new Date(profile.created_at).toLocaleDateString("pt-PT")}</span></span>
      <span class="pending-actions">
        <button class="button button-primary" type="button" data-approve-user="${escapeHtml(profile.id)}">Aprovar</button>
        <button class="button button-danger" type="button" data-reject-user="${escapeHtml(profile.id)}" data-username="${escapeHtml(profile.username)}">Rejeitar</button>
      </span>
    </div>`).join("") || '<p class="empty-state">Não há pedidos à espera de aprovação.</p>';
  void updatePendingCount();
  document.querySelector("#user-list").innerHTML = approved.map((profile) => `
    <div class="user-row">
      <span>${escapeHtml(profile.username)}</span>
      <span class="current-role">${profile.role === "professor" ? "Professor" : "Aluno"}</span>
      <form data-role-form="${escapeHtml(profile.id)}">
        <label class="visually-hidden" for="role-${escapeHtml(profile.id)}">Perfil de ${escapeHtml(profile.username)}</label>
        <select id="role-${escapeHtml(profile.id)}" name="role">
          <option value="aluno" ${profile.role === "aluno" ? "selected" : ""}>Aluno</option>
          <option value="professor" ${profile.role === "professor" ? "selected" : ""}>Professor</option>
        </select>
        <button class="button button-primary" type="submit">Guardar</button>
        ${profile.id === currentUser.id ? "" : `<button class="button button-danger" type="button" data-delete-user="${escapeHtml(profile.id)}" data-username="${escapeHtml(profile.username)}">Apagar</button>`}
      </form>
    </div>`).join("") || '<p class="empty-state">Não existem utilizadores.</p>';
}

function showUsersView() {
  document.querySelector("#home-view").hidden = true;
  document.querySelector("#users-view").hidden = false;
  void loadProfiles();
}

function downloadCsv() {
  const rows = filteredTests();
  const fields = ["Nome", "Ano", "Disciplina", "Data", "Nota"];
  const escapeCell = (value) => `"${String(value ?? "").replaceAll('"', '""')}"`;
  const content = [fields, ...rows.map((item) => [item.name, item.school_year, item.subject, item.test_date, item.grade ?? ""])]
    .map((row) => row.map(escapeCell).join(",")).join("\r\n");
  const blob = new Blob(["\ufeff", content], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  const query = document.querySelector("#student-filter").value.trim();
  link.href = url;
  const filename = [query || "historico", activeTestDate].filter(Boolean).join("_");
  link.download = `${filename.replaceAll(" ", "_").toLocaleLowerCase("pt-PT")}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

async function importJson(file) {
  try {
    const imported = JSON.parse(await file.text());
    if (!Array.isArray(imported)) throw new Error("O ficheiro deve conter uma lista JSON de testes.");
    const { data: users, error: usersError } = await supabase.from("profiles").select("id, username");
    if (usersError) throw usersError;
    const userIds = new Map((users || []).map((profile) => [profile.username.toLocaleLowerCase("pt-PT"), profile.id]));
    const rows = imported.map((item) => {
      const name = item.nome ?? item.name;
      const schoolYear = item.ano ?? item.school_year;
      const subject = item.disciplina ?? item.subject;
      const testDate = item.data ?? item.test_date;
      const rawGrade = item.nota ?? item.grade ?? "";
      const grade = rawGrade === "" ? null : Number(String(rawGrade).replace(",", "."));
      if (!name || !schoolYear || !subject || !/^\d{4}-\d{2}-\d{2}$/.test(testDate || "")) {
        throw new Error("Cada teste precisa de nome, ano, disciplina e data válida.");
      }
      if (grade !== null && (!Number.isFinite(grade) || grade < 0 || grade > 20)) {
        throw new Error(`A nota de ${name} tem de estar entre 0 e 20.`);
      }
      const ownerName = item.usuario || name;
      const owner = userIds.get(String(ownerName).toLocaleLowerCase("pt-PT"));
      return { user_id: owner || currentProfile.id, name, school_year: schoolYear, subject, test_date: testDate, grade };
    });
    if (!rows.length) throw new Error("O ficheiro não contém testes para importar.");
    const { error } = await supabase.from("tests").insert(rows);
    if (error) throw error;
    showNotice(`${rows.length} teste(s) importado(s).`);
    await loadTests();
  } catch (error) {
    showNotice(`Não foi possível importar: ${error.message}`, true);
  } finally {
    document.querySelector("#import-file").value = "";
  }
}

document.querySelectorAll("[data-auth-tab]").forEach((tab) => {
  tab.addEventListener("click", () => setAuthMode(tab.dataset.authTab));
});

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!supabase) return;
  const form = new FormData(loginForm);
  const { error } = await supabase.auth.signInWithPassword({ email: form.get("email"), password: form.get("password") });
  if (error) showNotice(error.message, true);
});

function updateSignupType() {
  const isProfessor = new FormData(signupForm).get("account_type") === "professor";
  const codeInput = document.querySelector("#signup-teacher-code");
  document.querySelector("#teacher-code-field").hidden = !isProfessor;
  codeInput.required = isProfessor;
  if (!isProfessor) codeInput.value = "";
  document.querySelector("#signup-submit").textContent = isProfessor ? "Criar conta de professor" : "Criar conta de aluno";
}

signupForm.addEventListener("change", (event) => {
  if (event.target.name === "account_type") updateSignupType();
});

signupForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!supabase) return;
  const form = new FormData(signupForm);
  const isProfessor = form.get("account_type") === "professor";
  const metadata = { username: String(form.get("username")).trim(), account_type: isProfessor ? "professor" : "aluno" };
  if (isProfessor) metadata.teacher_code = String(form.get("teacher_code")).trim();
  const { data, error } = await supabase.auth.signUp({
    email: form.get("email"),
    password: form.get("password"),
    options: { data: metadata }
  });
  if (error) {
    const invalidCode = isProfessor && /database error saving new user|invalid_teacher_code/i.test(error.message);
    return showNotice(invalidCode ? "Código de professor inválido." : error.message, true);
  }
  if (!data.session) {
    setAuthMode("login");
    signupForm.reset();
    updateSignupType();
    showNotice("Conta criada. Confirme o email antes de iniciar sessão.");
  } else if (!isProfessor) {
    signupForm.reset();
    updateSignupType();
    showNotice("Conta criada. Um professor tem de aprovar a conta antes de a poder usar.");
  }
});

document.querySelector("#test-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const formElement = event.currentTarget;
  const form = new FormData(formElement);
  const rawGrade = String(form.get("grade")).trim().replace(",", ".");
  const grade = rawGrade ? Number(rawGrade) : null;
  if (grade !== null && (!Number.isFinite(grade) || grade < 0 || grade > 20)) return showNotice("A nota deve estar entre 0 e 20.", true);
  const { error } = await supabase.from("tests").insert({
    user_id: currentUser.id,
    name: String(form.get("name")).trim(),
    school_year: form.get("school_year"),
    subject: form.get("subject"),
    test_date: form.get("test_date"),
    grade
  });
  if (error) return showNotice(error.message, true);
  formElement.reset();
  showNotice("Teste guardado.");
  await loadTests();
});

testList.addEventListener("submit", async (event) => {
  const form = event.target.closest("[data-grade-form]");
  if (!form) return;
  event.preventDefault();
  const rawGrade = String(new FormData(form).get("grade")).trim().replace(",", ".");
  const grade = rawGrade ? Number(rawGrade) : null;
  if (grade !== null && (!Number.isFinite(grade) || grade < 0 || grade > 20)) return showNotice("A nota deve estar entre 0 e 20.", true);
  const { error } = await supabase.from("tests").update({ grade }).eq("id", form.dataset.gradeForm);
  if (error) return showNotice(error.message, true);
  showNotice("Nota atualizada.");
  await loadTests();
});

testList.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-delete-test]");
  if (!button) return;
  const item = tests.find((test) => test.id === button.dataset.deleteTest);
  if (!item || !window.confirm(`Apagar o teste de ${item.name} (${item.subject})?`)) return;
  const { data, error } = await supabase.from("tests").delete().eq("id", item.id).select("id");
  if (error) return showNotice(error.message, true);
  if (!data.length) return showNotice("Não tem permissão para apagar este teste.", true);
  showNotice("Teste apagado.");
  await loadTests();
});

document.querySelector("#refresh-button").addEventListener("click", async (event) => {
  const button = event.currentTarget;
  button.disabled = true;
  try {
    await loadTests();
    showNotice("Testes atualizados.");
  } catch (error) {
    showNotice(error.message, true);
  } finally {
    button.disabled = false;
  }
});

document.querySelector("#filter-form").addEventListener("submit", (event) => {
  event.preventDefault();
  renderTests();
});
document.querySelector("#student-filter").addEventListener("input", renderTests);
document.querySelector("#day-filter-button").addEventListener("click", () => {
  const selectedDate = document.querySelector("#test-day-filter").value;
  if (!selectedDate) return showNotice("Seleciona um dia para ver os testes.", true);
  activeTestDate = selectedDate;
  renderTests();
});
document.querySelector("#toggle-past-tests").addEventListener("click", () => {
  showPastTests = !showPastTests;
  renderTests();
});
document.querySelector("#clear-filter").addEventListener("click", () => {
  document.querySelector("#student-filter").value = "";
  document.querySelector("#test-day-filter").value = "";
  activeTestDate = "";
  showPastTests = false;
  renderTests();
});
document.querySelector("#export-button").addEventListener("click", downloadCsv);
document.querySelector("#import-button").addEventListener("click", () => document.querySelector("#import-file").click());
document.querySelector("#import-file").addEventListener("change", (event) => {
  if (event.currentTarget.files[0]) void importJson(event.currentTarget.files[0]);
});
document.querySelector("#manage-link").addEventListener("click", showUsersView);
document.querySelector("#back-home").addEventListener("click", () => {
  document.querySelector("#users-view").hidden = true;
  document.querySelector("#home-view").hidden = false;
});
document.querySelector("#user-list").addEventListener("click", async (event) => {
  const button = event.target.closest("[data-delete-user]");
  if (!button) return;
  if (!window.confirm(`Apagar a conta de ${button.dataset.username}? Os testes desta conta também são apagados. Esta ação não pode ser desfeita.`)) return;
  const { error } = await supabase.rpc("delete_user_account", { target_user: button.dataset.deleteUser });
  if (error) return showNotice(error.message, true);
  showNotice("Utilizador apagado.");
  await loadProfiles();
});
document.querySelector("#user-list").addEventListener("submit", async (event) => {
  const form = event.target.closest("[data-role-form]");
  if (!form) return;
  event.preventDefault();
  const role = new FormData(form).get("role");
  const userId = form.dataset.roleForm;
  const { error } = await supabase.from("profiles").update({ role }).eq("id", userId);
  if (error) return showNotice(error.message, true);
  showNotice("Perfil atualizado.");
  await loadProfiles();
  if (userId === currentUser.id) {
    currentProfile.role = role;
    showSignedIn();
    renderTests();
  }
});
document.querySelector("#pending-list").addEventListener("click", async (event) => {
  const approveButton = event.target.closest("[data-approve-user]");
  const rejectButton = event.target.closest("[data-reject-user]");
  if (approveButton) {
    const { data, error } = await supabase.from("profiles").update({ approved: true }).eq("id", approveButton.dataset.approveUser).select("id");
    if (error) return showNotice(error.message, true);
    if (!data.length) return showNotice("Não foi possível aprovar esta conta.", true);
    showNotice("Conta aprovada.");
  } else if (rejectButton) {
    if (!window.confirm(`Rejeitar e apagar o pedido de ${rejectButton.dataset.username}?`)) return;
    const { error } = await supabase.rpc("delete_user_account", { target_user: rejectButton.dataset.rejectUser });
    if (error) return showNotice(error.message, true);
    showNotice("Pedido rejeitado.");
  } else {
    return;
  }
  await loadProfiles();
});
document.querySelector("#pending-check").addEventListener("click", async () => {
  if (!currentUser) return;
  try {
    await loadProfile();
    if (!currentProfile.approved && currentProfile.role !== "professor") showNotice("A conta ainda não foi aprovada.");
  } catch (error) {
    showNotice(error.message, true);
  }
});
document.querySelector("#pending-logout").addEventListener("click", async () => {
  const { error } = await supabase.auth.signOut();
  if (error) showNotice(error.message, true);
  showSignedOut();
});
document.querySelector("#logout-button").addEventListener("click", async () => {
  const { error } = await supabase.auth.signOut();
  if (error) showNotice(error.message, true);
  showSignedOut();
});

function scheduleDailyRender() {
  const now = new Date();
  const nextMidnight = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
  window.setTimeout(() => {
    renderTests();
    scheduleDailyRender();
  }, nextMidnight.getTime() - now.getTime() + 50);
}

document.addEventListener("visibilitychange", () => {
  if (!document.hidden) renderTests();
});
scheduleDailyRender();

if (!configured) {
  document.querySelectorAll("#login-form button, #signup-form button").forEach((button) => { button.disabled = true; });
  showSignedOut();
} else {
  supabase.auth.onAuthStateChange((_event, session) => {
    window.setTimeout(async () => {
      if (!session) return showSignedOut();
      currentUser = session.user;
      try { await loadProfile(); } catch (error) { showNotice(error.message, true); }
    }, 0);
  });
  supabase.auth.getSession().then(async ({ data, error }) => {
    if (error) return showNotice(error.message, true);
    if (!data.session) return showSignedOut();
    currentUser = data.session.user;
    try { await loadProfile(); } catch (profileError) { showNotice(profileError.message, true); }
  });
}