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
  const isLogin = mode === "login";
  loginForm.hidden = !isLogin;
  signupForm.hidden = isLogin;
  document.querySelectorAll("[data-auth-tab]").forEach((tab) => {
    const selected = tab.dataset.authTab === mode;
    tab.classList.toggle("is-active", selected);
    tab.setAttribute("aria-selected", String(selected));
  });
}

function showSignedOut() {
  currentUser = null;
  currentProfile = null;
  authScreen.hidden = false;
  appScreen.hidden = true;
  document.querySelector("#config-help").hidden = configured;
}

function showSignedIn() {
  authScreen.hidden = true;
  appScreen.hidden = false;
  document.querySelector("#account-label").textContent = currentProfile.username;
  document.querySelector("#role-label").textContent = currentProfile.role === "professor" ? "Perfil de professor" : "Perfil de aluno";
  document.querySelector("#manage-link").hidden = currentProfile.role !== "professor";
  document.querySelector("#import-button").hidden = currentProfile.role !== "professor";
  document.querySelector("#home-view").hidden = false;
  document.querySelector("#users-view").hidden = true;
}

async function loadProfile() {
  const { data, error } = await supabase.from("profiles").select("id, username, role").eq("id", currentUser.id).single();
  if (error) throw error;
  currentProfile = data;
  showSignedIn();
  await loadTests();
}

async function loadTests() {
  const { data, error } = await supabase.from("tests").select("id, user_id, name, school_year, subject, test_date, grade").order("test_date", { ascending: true });
  if (error) throw error;
  tests = data || [];
  renderTests();
}

function filteredTests() {
  const filter = document.querySelector("#student-filter").value.trim().toLocaleLowerCase("pt-PT");
  return tests.filter((item) => !filter || item.name.toLocaleLowerCase("pt-PT").includes(filter));
}

function renderTests() {
  const visibleTests = filteredTests();
  document.querySelector("#record-count").textContent = String(visibleTests.length);
  const hasFilter = document.querySelector("#student-filter").value.trim().length > 0;
  document.querySelector("#clear-filter").hidden = !hasFilter;
  document.querySelector("#export-button").hidden = !hasFilter;
  if (!visibleTests.length) {
    testList.innerHTML = '<p class="empty-state">Ainda não existem testes registados.</p>';
    return;
  }

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
      </form>
    </article>`;
  }).join("");
}

async function loadProfiles() {
  const { data, error } = await supabase.from("profiles").select("id, username, role").order("username");
  if (error) {
    showNotice(error.message, true);
    return;
  }
  document.querySelector("#user-list").innerHTML = (data || []).map((profile) => `
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
  link.download = `${(query || "historico").replaceAll(" ", "_").toLocaleLowerCase("pt-PT")}.csv`;
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
  }
});

document.querySelector("#test-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
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
  event.currentTarget.reset();
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

document.querySelector("#filter-form").addEventListener("submit", (event) => {
  event.preventDefault();
  renderTests();
});
document.querySelector("#student-filter").addEventListener("input", renderTests);
document.querySelector("#clear-filter").addEventListener("click", () => {
  document.querySelector("#student-filter").value = "";
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
  }
});
document.querySelector("#logout-button").addEventListener("click", async () => {
  const { error } = await supabase.auth.signOut();
  if (error) showNotice(error.message, true);
  showSignedOut();
});

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