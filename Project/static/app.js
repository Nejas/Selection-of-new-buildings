const els = {
  form: document.querySelector("#searchForm"),
  input: document.querySelector("#searchInput"),
  results: document.querySelector("#results"),
  resultCount: document.querySelector("#resultCount"),
  emptyState: document.querySelector("#emptyState"),
  scoreView: document.querySelector("#scoreView"),
  loadingPanel: document.querySelector("#loadingPanel"),
  developerName: document.querySelector("#developerName"),
  selectedInn: document.querySelector("#selectedInn"),
  scoreValue: document.querySelector("#scoreValue"),
  scoreLabel: document.querySelector("#scoreLabel"),
  statusBand: document.querySelector("#statusBand"),
  statusText: document.querySelector("#statusText"),
  projectsCount: document.querySelector("#projectsCount"),
  problemCount: document.querySelector("#problemCount"),
  delayCount: document.querySelector("#delayCount"),
  legalCount: document.querySelector("#legalCount"),
  criteriaList: document.querySelector("#criteriaList"),
  factorList: document.querySelector("#factorList"),
  warnings: document.querySelector("#warnings"),
  projectsTable: document.querySelector("#projectsTable"),
  projectsTableCount: document.querySelector("#projectsTableCount"),
  legalEvents: document.querySelector("#legalEvents"),
  legalEventsCount: document.querySelector("#legalEventsCount"),
  newsSentimentChart: document.querySelector("#newsSentimentChart"),
  newsList: document.querySelector("#newsList"),
  newsCount: document.querySelector("#newsCount"),
};

const criteriaLabels = {
  deadline_discipline: "Дисциплина сроков",
  problem_objects: "Проблемные объекты",
  legal_risk: "Правовые риски",
  reputation_risk: "Репутация",
};
const CACHE_VERSION = "rating-cache-v3";
const DOSSIER_CACHE_TTL_MS = 12 * 60 * 60 * 1000;
const STALE_DOSSIER_CACHE_TTL_MS = 7 * 24 * 60 * 60 * 1000;

els.form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const query = els.input.value.trim();
  if (query.length < 2) return;
  await searchDevelopers(query);
});

async function searchDevelopers(query) {
  setResultsLoading();
  try {
    const response = await fetch(`/api/developers/search?query=${encodeURIComponent(query)}&limit=20`);
    if (!response.ok) throw new Error("search failed");
    const developers = await response.json();
    renderResults(developers);
  } catch {
    renderMessage("Поиск недоступен");
  }
}

function setResultsLoading() {
  els.resultCount.textContent = "...";
  els.results.innerHTML = `<div class="result-item"><strong>Загрузка</strong><span></span></div>`;
}

function renderResults(developers) {
  els.resultCount.textContent = developers.length;
  if (!developers.length) {
    renderMessage("Ничего не найдено");
    return;
  }

  els.results.innerHTML = developers.map((developer) => `
    <button class="result-item" data-inn="${developer.inn}">
      <strong>${escapeHtml(developer.name)}</strong>
      <span>${developer.inn} · ${escapeHtml(developer.region || "Регион не указан")}</span>
    </button>
  `).join("");

  els.results.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", async () => {
      els.results.querySelectorAll("button").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      await loadScore(button.dataset.inn);
    });
  });
}

function renderMessage(text) {
  els.resultCount.textContent = "0";
  els.results.innerHTML = `<div class="result-item"><strong>${escapeHtml(text)}</strong><span></span></div>`;
}

async function loadScore(inn) {
  showScoreShell();

  const cacheKey = makeCacheKey("dossier", inn);
  const cached = readCache(cacheKey, DOSSIER_CACHE_TTL_MS);
  if (cached) {
    renderScore(cached);
    return;
  }

  setScoreLoading(inn);
  try {
    const response = await fetch(`/api/developers/${inn}/dossier`);
    if (!response.ok) throw new Error("score failed");
    const data = await response.json();
    writeCache(cacheKey, data);
    renderScore(data);
  } catch {
    const stale = readCache(cacheKey, STALE_DOSSIER_CACHE_TTL_MS);
    if (stale) {
      renderScore(stale);
    } else {
      els.developerName.textContent = "Оценка недоступна";
      els.scoreValue.textContent = "–";
      els.scoreLabel.textContent = "ошибка";
    }
  }
}

function showScoreShell() {
  els.emptyState.classList.add("hidden");
  els.scoreView.classList.remove("hidden");
}

function setScoreLoading(inn) {
  els.loadingPanel.classList.remove("hidden");
  els.selectedInn.textContent = inn;
  els.developerName.textContent = "Расчёт рейтинга";
  els.scoreValue.innerHTML = '<span class="skeleton"></span>';
  els.scoreLabel.textContent = "";
  els.statusText.textContent = "";
  els.projectsCount.innerHTML = '<span class="skeleton"></span>';
  els.problemCount.innerHTML = '<span class="skeleton"></span>';
  els.delayCount.innerHTML = '<span class="skeleton"></span>';
  els.legalCount.innerHTML = '<span class="skeleton"></span>';
  els.criteriaList.innerHTML = loadingCriteria();
  els.factorList.innerHTML = loadingFactors();
  els.warnings.innerHTML = "";
  els.projectsTable.innerHTML = "";
  els.legalEvents.innerHTML = "";
  els.newsSentimentChart.innerHTML = "";
  els.newsList.innerHTML = "";
}

function renderScore(data) {
  els.loadingPanel.classList.add("hidden");
  const factors = data.factors || {};
  const details = data.details || {};

  els.developerName.textContent = data.developer || "Застройщик";
  els.selectedInn.textContent = factors.inn || "";
  els.scoreValue.textContent = data.score ?? "–";
  els.scoreLabel.textContent = data.score === null ? "нет оценки" : "баллов";
  els.statusText.textContent = data.status || "";
  setStatusClass(data.status);

  els.projectsCount.textContent = factors.projects_count ?? 0;
  els.problemCount.textContent = factors.problem_projects_count ?? 0;
  els.delayCount.textContent = factors.delayed_projects_count ?? 0;
  els.legalCount.textContent = factors.legal_events_count ?? 0;

  renderCriteria(details.criteria || {}, factors);
  renderFactors(factors);
  renderWarnings([...(details.unknown_reasons || []), ...(details.data_warnings || [])]);
  renderProjects(data.projects || []);
  renderLegalEvents(data.legal_events || []);
  renderNews(data.news || []);
}

function loadingCriteria() {
  return Object.values(criteriaLabels).map((label) => `
    <div class="criterion">
      <strong>${label}</strong>
      <div class="bar"><span style="width: 45%"></span></div>
      <span><span class="skeleton"></span></span>
    </div>
  `).join("");
}

function loadingFactors() {
  return ["Дата регистрации", "Средняя задержка", "Новостей", "Нейтральных новостей", "Негатив новостей", "Текстов в оценке", "Негативных юр. событий"].map((label) => `
    <dt>${label}</dt>
    <dd><span class="skeleton"></span></dd>
  `).join("");
}

function setStatusClass(status) {
  els.statusBand.className = "status-band";
  if (status === "Высокая надёжность") els.statusBand.classList.add("status-high");
  else if (status === "Средняя надёжность") els.statusBand.classList.add("status-medium");
  else if (status === "Рискованный") els.statusBand.classList.add("status-risk");
  else if (status === "Высокий риск") els.statusBand.classList.add("status-danger");
  else els.statusBand.classList.add("status-unknown");
}

function renderCriteria(criteria, factors = {}) {
  els.criteriaList.innerHTML = Object.entries(criteriaLabels).map(([key, label]) => {
    if (key === "problem_objects") {
      const problemCount = factors.problem_projects_count ?? 0;
      const total = factors.projects_count ?? 0;
      const percent = total ? Math.round((problemCount / total) * 100) : 0;
      return `
        <div class="criterion">
          <strong>${label}</strong>
          <div class="bar"><span class="${problemCount ? "danger-bar" : "ok-bar"}" style="width: ${Math.max(percent, problemCount ? 8 : 0)}%"></span></div>
          <span>${problemCount} из ${total}</span>
        </div>
      `;
    }

    const value = criteria[key];
    const percent = value === null || value === undefined ? 50 : Math.round(value * 100);
    const display = value === null || value === undefined ? "н/д" : `${percent}%`;
    return `
      <div class="criterion">
        <strong>${label}</strong>
        <div class="bar"><span style="width: ${percent}%"></span></div>
        <span>${display}</span>
      </div>
    `;
  }).join("");
}

function renderFactors(factors) {
  const rows = [
    ["Дата регистрации", factors.registration_date || "н/д"],
    ["Средняя задержка", formatDays(factors.avg_delay_days)],
    ["Новостей", factors.news_mentions ?? 0],
    ["Нейтральных новостей", factors.neutral_news_count ?? 0],
    ["Негатив новостей", formatPercent(factors.negative_news_share)],
    ["Оценённых новостей", factors.scored_news_count ?? 0],
    ["Негативных юр. событий", factors.legal_events_count ?? 0],
  ];

  els.factorList.innerHTML = rows.map(([key, value]) => `
    <dt>${key}</dt>
    <dd>${value}</dd>
  `).join("");
}

function renderWarnings(warnings) {
  if (!warnings.length) {
    els.warnings.innerHTML = "<li>Нет предупреждений</li>";
    return;
  }
  els.warnings.innerHTML = warnings.map((warning) => `<li>${escapeHtml(warning)}</li>`).join("");
}

function renderProjects(projects) {
  els.projectsTableCount.textContent = projects.length;
  if (!projects.length) {
    els.projectsTable.innerHTML = `<tr><td colspan="5">Нет объектов</td></tr>`;
    return;
  }

  els.projectsTable.innerHTML = projects.slice(0, 20).map((project) => `
    <tr>
      <td>${escapeHtml(project.name)}</td>
      <td>${project.planned_date || "н/д"}</td>
      <td>${formatDays(project.delay_days_avg)}</td>
      <td>${formatArea(project.area)}</td>
      <td>${project.is_problem ? '<span class="tag tag-danger">Проблемный</span>' : statusByDelay(project.delay_days_avg)}</td>
    </tr>
  `).join("");
}

function renderLegalEvents(events) {
  els.legalEventsCount.textContent = events.length;
  if (!events.length) {
    els.legalEvents.innerHTML = `<div class="event-card"><strong>Негативные судебные дела не найдены</strong><p>В подключённом правовом источнике нет дел, где этот застройщик указан ответчиком.</p></div>`;
    return;
  }

  els.legalEvents.innerHTML = events.slice(0, 8).map((event) => `
    <article class="event-card">
      <strong>${legalType(event.event_type)}</strong>
      <p>${escapeHtml(event.description || "Описание отсутствует")}</p>
      <div class="event-meta">
        <span>${event.date || "дата не указана"}</span>
        ${event.source ? `<a href="${escapeHtml(event.source)}" target="_blank" rel="noreferrer">источник</a>` : ""}
      </div>
    </article>
  `).join("");
}

function renderNews(news) {
  els.newsCount.textContent = news.length;
  renderNewsSentimentChart(news);
  if (!news.length) {
    els.newsList.innerHTML = `<div class="event-card"><strong>Значимых новостей не найдено</strong><p>В подключённых новостных лентах нет публикаций, где явно упоминается название или ИНН этого застройщика.</p></div>`;
    return;
  }

  const negative = news.filter((item) => item.sentiment === "negative")[0];
  const positive = news.filter((item) => item.sentiment === "positive")[0];
  const examples = [negative, positive, ...news].filter(Boolean);
  const unique = [];
  const seen = new Set();
  for (const item of examples) {
    const key = item.link || item.title;
    if (seen.has(key)) continue;
    seen.add(key);
    unique.push(item);
  }

  els.newsList.innerHTML = unique.slice(0, 8).map((item) => `
    <article class="event-card">
      <strong>${escapeHtml(item.title)}</strong>
      <p>${escapeHtml(stripHtml(item.summary || ""))}</p>
      <div class="event-meta">
        <span class="${sentimentClass(item.sentiment)}">${sentimentLabel(item.sentiment)}</span>
        <span>${item.published_at || ""}</span>
        ${item.link ? `<a href="${escapeHtml(item.link)}" target="_blank" rel="noreferrer">читать</a>` : ""}
      </div>
    </article>
  `).join("");
}

function renderNewsSentimentChart(news) {
  if (!news.length) {
    els.newsSentimentChart.innerHTML = "";
    return;
  }

  const counts = news.reduce((acc, item) => {
    const sentiment = item.sentiment || "unknown";
    acc[sentiment] = (acc[sentiment] || 0) + 1;
    return acc;
  }, { negative: 0, positive: 0, neutral: 0, unknown: 0 });

  const total = news.length;
  const rows = [
    ["negative", "Негативные", counts.negative || 0],
    ["positive", "Позитивные", counts.positive || 0],
    ["neutral", "Нейтральные", counts.neutral || 0],
  ];

  els.newsSentimentChart.innerHTML = `
    <div class="sentiment-stack" aria-label="Распределение тональности новостей">
      ${rows.map(([key, label, count]) => `
        <span class="sentiment-segment sentiment-${key}" style="width: ${percent(count, total)}%" title="${label}: ${percent(count, total)}%"></span>
      `).join("")}
    </div>
    <div class="sentiment-legend">
      ${rows.map(([key, label, count]) => `
        <div>
          <span class="legend-dot sentiment-${key}"></span>
          <strong>${percent(count, total)}%</strong>
          <span>${label}</span>
          <small>${count}</small>
        </div>
      `).join("")}
    </div>
  `;
}

function formatDays(value) {
  if (value === null || value === undefined) return "н/д";
  return `${Math.round(value)} дн.`;
}

function formatPercent(value) {
  if (value === null || value === undefined) return "н/д";
  return `${Math.round(value * 100)}%`;
}

function percent(value, total) {
  if (!total) return 0;
  return Math.round((value / total) * 100);
}

function formatArea(value) {
  if (!value) return "н/д";
  return `${Math.round(value).toLocaleString("ru-RU")} м²`;
}

function statusByDelay(days) {
  if (!days) return '<span class="tag tag-ok">Без срыва</span>';
  if (days > 180) return '<span class="tag tag-danger">Срыв > 6 мес.</span>';
  return '<span class="tag tag-warn">Есть задержка</span>';
}

function legalType(type) {
  const labels = {
    court_case_defendant: "Судебное дело: ответчик",
  };
  return labels[type] || type || "Правовое событие";
}

function sentimentLabel(value) {
  return {
    negative: "негатив",
    positive: "позитив",
    neutral: "нейтрально",
  }[value] || "не оценено";
}

function sentimentClass(value) {
  if (value === "negative") return "tag tag-danger";
  if (value === "positive") return "tag tag-ok";
  return "tag";
}

function stripHtml(value) {
  const div = document.createElement("div");
  div.innerHTML = value;
  return div.textContent || div.innerText || "";
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function makeCacheKey(type, id) {
  return `${CACHE_VERSION}:${type}:${id}`;
}

function readCache(key, maxAgeMs) {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return null;

    const entry = JSON.parse(raw);
    if (!entry || !entry.savedAt || !entry.value) return null;
    if (Date.now() - entry.savedAt > maxAgeMs) return null;

    return entry.value;
  } catch {
    return null;
  }
}

function writeCache(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify({
      savedAt: Date.now(),
      value,
    }));
  } catch {
    // Если хранилище браузера заполнено или отключено, сайт просто работает без кэша.
  }
}
