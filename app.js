let state = null;
let autoTimer = null;

const tabs = document.querySelectorAll(".tab");
const standingsPanel = document.querySelector("#standingsPanel");
const treePanel = document.querySelector("#treePanel");
const playersPanel = document.querySelector("#playersPanel");
const refreshBtn = document.querySelector("#refreshBtn");
const resetBtn = document.querySelector("#resetBtn");
const autoRefresh = document.querySelector("#autoRefresh");
const teamSearch = document.querySelector("#teamSearch");
const playerSearch = document.querySelector("#playerSearch");
const toast = document.querySelector("#toast");
const TEAM_FLAGS = {
  Algeria: "🇩🇿",
  Argentina: "🇦🇷",
  Australia: "🇦🇺",
  Austria: "🇦🇹",
  Belgium: "🇧🇪",
  "Bosnia and Herzegovina": "🇧🇦",
  Brazil: "🇧🇷",
  Canada: "🇨🇦",
  "Cabo Verde": "🇨🇻",
  Colombia: "🇨🇴",
  Croatia: "🇭🇷",
  Curaçao: "🇨🇼",
  Czechia: "🇨🇿",
  "Côte d'Ivoire": "🇨🇮",
  "DR Congo": "🇨🇩",
  Ecuador: "🇪🇨",
  Egypt: "🇪🇬",
  England: "🏴",
  France: "🇫🇷",
  Germany: "🇩🇪",
  Ghana: "🇬🇭",
  Haiti: "🇭🇹",
  Iran: "🇮🇷",
  Iraq: "🇮🇶",
  Japan: "🇯🇵",
  Jordan: "🇯🇴",
  Mexico: "🇲🇽",
  Morocco: "🇲🇦",
  Netherlands: "🇳🇱",
  "New Zealand": "🇳🇿",
  Norway: "🇳🇴",
  Panama: "🇵🇦",
  Paraguay: "🇵🇾",
  Portugal: "🇵🇹",
  Qatar: "🇶🇦",
  "Saudi Arabia": "🇸🇦",
  Scotland: "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
  Senegal: "🇸🇳",
  "South Africa": "🇿🇦",
  "South Korea": "🇰🇷",
  Spain: "🇪🇸",
  Sweden: "🇸🇪",
  Switzerland: "🇨🇭",
  Tunisia: "🇹🇳",
  Türkiye: "🇹🇷",
  "United States": "🇺🇸",
  Uruguay: "🇺🇾",
  Uzbekistan: "🇺🇿",
};
const FEATURED_PLAYERS = new Set(["Kylian Mbappé", "Lionel Messi", "Cristiano Ronaldo", "Erling Haaland"]);

function showToast(message) {
  toast.textContent = message;
  toast.hidden = false;
  setTimeout(() => {
    toast.hidden = true;
  }, 3200);
}

async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) {
    const message = payload.error || "Request failed";
    if (payload.data) {
      state = payload.data;
      render();
    }
    throw new Error(message);
  }
  return payload;
}

function formatDate(value) {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: value.includes("T") ? "numeric" : undefined,
    minute: value.includes("T") ? "2-digit" : undefined,
  }).format(new Date(value.includes("T") ? value : `${value}T12:00:00`));
}

function statusLabel(status) {
  if (status === "advanced") return "Qualified";
  if (status === "eliminated") return "Out";
  if (status === "third") return "3rd";
  return "";
}

function teamLabel(team) {
  const flag = TEAM_FLAGS[team];
  return `${flag ? `<span class="flag" aria-hidden="true">${flag}</span>` : ""}<span>${team}</span>`;
}

function renderMeta() {
  document.querySelector("#lastUpdated").textContent = state.lastUpdated
    ? `Updated ${formatDate(state.lastUpdated)}`
    : "Not updated yet";
  document.querySelector("#sourceNote").textContent = state.sourceNote || "";
}

function groupVisible(group, rows) {
  const query = teamSearch.value.trim().toLowerCase();
  if (!query) return true;
  return group.toLowerCase().includes(query) || rows.some((row) => row.team.toLowerCase().includes(query));
}

function renderGroups() {
  const grid = document.querySelector("#groupsGrid");
  grid.innerHTML = "";
  Object.entries(state.groups).forEach(([group, rows]) => {
    if (!groupVisible(group, rows)) return;
    const card = document.createElement("article");
    card.className = "group-card";
    card.innerHTML = `
      <div class="group-title"><strong>Group ${group}</strong><span>${rows.length} teams</span></div>
      <table>
        <thead>
          <tr><th>Team</th><th>GD</th><th>GF</th><th class="pts-head">Pts</th><th></th></tr>
        </thead>
        <tbody>
          ${rows
            .map(
              (row) => `
                <tr class="${row.status}">
                  <td>${teamLabel(row.team)}</td>
                  <td>${row.gd > 0 ? `+${row.gd}` : row.gd}</td>
                  <td>${row.gf}</td>
                  <td class="pts-cell">${row.pts}</td>
                  <td>${statusLabel(row.status)}</td>
                </tr>
              `,
            )
            .join("")}
        </tbody>
      </table>
    `;
    grid.appendChild(card);
  });
}

function renderMatches() {
  const list = document.querySelector("#matchesList");
  const query = teamSearch.value.trim().toLowerCase();
  const matches = state.matches.filter((match) => {
    if (!query) return true;
    return (
      match.group.toLowerCase().includes(query) ||
      match.home.toLowerCase().includes(query) ||
      match.away.toLowerCase().includes(query)
    );
  });
  list.innerHTML = matches
    .map(
      (match) => `
        <article class="match-card" data-id="${match.id}">
          <div class="match-meta">
            <span>Group ${match.group} · ${formatDate(match.date)}</span>
            <span>${match.status}</span>
          </div>
          <div class="score-row">
            <span class="team-name">${match.home}</span>
            <input type="number" min="0" class="home-score" value="${match.homeScore ?? ""}" aria-label="${match.home} score" />
            <strong>:</strong>
            <input type="number" min="0" class="away-score" value="${match.awayScore ?? ""}" aria-label="${match.away} score" />
          </div>
          <div class="score-row">
            <span class="team-name">${match.away}</span>
            <span></span><span></span><span></span>
          </div>
          <div class="match-actions">
            <select class="match-status" aria-label="Match status">
              ${["Scheduled", "Live", "FT"].map((status) => `<option ${status === match.status ? "selected" : ""}>${status}</option>`).join("")}
            </select>
            <button class="save-match">Save</button>
          </div>
        </article>
      `,
    )
    .join("");
}

function groupTeam(group, place) {
  const rows = state.groups[group] || [];
  return rows[place - 1]?.team || null;
}

function resolveSlot(label) {
  let match = label.match(/^Winner Group ([A-L])$/);
  if (match) return { text: groupTeam(match[1], 1) || label, filled: Boolean(groupTeam(match[1], 1)) };
  match = label.match(/^Runner-up Group ([A-L])$/);
  if (match) return { text: groupTeam(match[1], 2) || label, filled: Boolean(groupTeam(match[1], 2)) };
  match = label.match(/^3rd Group ([A-L/]+)$/);
  if (match) return { text: `3rd place: ${match[1]}`, filled: false };
  return { text: label, filled: false };
}

function slotHtml(slot) {
  return slot.filled ? teamLabel(slot.text) : slot.text;
}

function cardHtml(match, side = "") {
  const home = resolveSlot(match.home);
  const away = resolveSlot(match.away);
  return `
    <article class="tree-card ${side}">
      <div class="tree-slot">${match.slot} · ${formatDate(match.date)}</div>
      <div class="tree-pair">
        <div class="tree-team ${home.filled ? "filled" : "pending"}">${slotHtml(home)}</div>
        <div class="tree-team ${away.filled ? "filled" : "pending"}">${slotHtml(away)}</div>
      </div>
    </article>
  `;
}

function renderTreeSide(label, roundGroups, side) {
  return `
    <section class="bracket-side ${side}">
      <h3>${label}</h3>
      <div class="tree-side-grid">
        ${roundGroups
          .map(
            (group) => `
              <section class="round-column ${side}">
                <div class="round-heading">${group.title}</div>
                ${group.matches.map((match) => cardHtml(match, side)).join("")}
              </section>
            `,
          )
          .join("")}
      </div>
    </section>
  `;
}

function renderBracket() {
  const bracket = document.querySelector("#bracket");
  const bySlot = Object.fromEntries(state.knockout.map((match) => [match.slot, match]));
  const left = [
    { title: "Round of 32", matches: Array.from({ length: 8 }, (_, index) => bySlot[`R32-${index + 1}`]) },
    { title: "Round of 16", matches: Array.from({ length: 4 }, (_, index) => bySlot[`R16-${index + 1}`]) },
    { title: "Quarterfinal", matches: [bySlot["QF-1"], bySlot["QF-2"]] },
    { title: "Semifinal", matches: [bySlot["SF-1"]] },
  ];
  const right = [
    { title: "Semifinal", matches: [bySlot["SF-2"]] },
    { title: "Quarterfinal", matches: [bySlot["QF-3"], bySlot["QF-4"]] },
    { title: "Round of 16", matches: Array.from({ length: 4 }, (_, index) => bySlot[`R16-${index + 5}`]) },
    { title: "Round of 32", matches: Array.from({ length: 8 }, (_, index) => bySlot[`R32-${index + 9}`]) },
  ];
  bracket.innerHTML = `
    ${renderTreeSide("Left Side", left, "left")}
    <section class="final-column">
      <h3>Final Side</h3>
      ${cardHtml(bySlot.Final, "final")}
      ${cardHtml(bySlot["3P"], "final")}
    </section>
    ${renderTreeSide("Right Side", right, "right")}
  `;
}

function renderPlayerStats() {
  const body = document.querySelector("#playerStatsBody");
  const summary = document.querySelector("#statsSummary");
  const query = playerSearch.value.trim().toLowerCase();
  const rows = [...(state.playerStats || [])]
    .filter((row) => !query || row.player.toLowerCase().includes(query) || row.team.toLowerCase().includes(query))
    .sort((a, b) => b.goals - a.goals || b.assists - a.assists || a.player.localeCompare(b.player));
  const totals = rows.reduce(
    (acc, row) => {
      acc.goals += row.goals;
      acc.assists += row.assists;
      acc.yellowCards += row.yellowCards;
      acc.redCards += row.redCards;
      return acc;
    },
    { goals: 0, assists: 0, yellowCards: 0, redCards: 0 },
  );
  document.querySelector("#playerStatsNote").textContent = state.playerStatsNote || "";
  summary.innerHTML = `
    <div><strong>${rows.length}</strong><span>Players</span></div>
    <div><strong>${totals.goals}</strong><span>Goals</span></div>
    <div><strong>${totals.assists}</strong><span>Assists</span></div>
    <div><strong>${totals.yellowCards}</strong><span>Yellow cards</span></div>
    <div><strong>${totals.redCards}</strong><span>Red cards</span></div>
  `;
  body.innerHTML = rows
    .map(
      (row) => `
        <tr class="${FEATURED_PLAYERS.has(row.player) ? "featured-player" : ""}">
          <td>${row.player}</td>
          <td>${teamLabel(row.team)}</td>
          <td>${row.goals}</td>
          <td>${row.assists}</td>
          <td>${row.yellowCards}</td>
          <td>${row.redCards}</td>
        </tr>
      `,
    )
    .join("");
}

function render() {
  renderMeta();
  renderGroups();
  renderMatches();
  renderBracket();
  renderPlayerStats();
}

async function loadInitial() {
  state = await request("/api/data");
  render();
}

tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    tabs.forEach((item) => item.classList.toggle("active", item === tab));
    standingsPanel.classList.toggle("active", tab.dataset.tab === "standings");
    playersPanel.classList.toggle("active", tab.dataset.tab === "players");
    treePanel.classList.toggle("active", tab.dataset.tab === "tree");
  });
});

refreshBtn.addEventListener("click", async () => {
  refreshBtn.disabled = true;
  refreshBtn.textContent = "Refreshing";
  try {
    state = await request("/api/refresh", { method: "POST" });
    render();
    showToast("Latest standings refresh complete");
  } catch (error) {
    showToast(`Refresh could not reach/parse live source: ${error.message}`);
  } finally {
    refreshBtn.disabled = false;
    refreshBtn.textContent = "Refresh";
  }
});

resetBtn.addEventListener("click", async () => {
  state = await request("/api/reset", { method: "POST" });
  render();
  showToast("Seed data restored");
});

autoRefresh.addEventListener("change", () => {
  if (autoTimer) {
    clearInterval(autoTimer);
    autoTimer = null;
  }
  if (autoRefresh.checked) {
    autoTimer = setInterval(() => refreshBtn.click(), 60000);
  }
});

teamSearch.addEventListener("input", render);
playerSearch.addEventListener("input", renderPlayerStats);

document.querySelector("#matchesList").addEventListener("click", async (event) => {
  const button = event.target.closest(".save-match");
  if (!button) return;
  const card = button.closest(".match-card");
  const payload = {
    id: card.dataset.id,
    homeScore: card.querySelector(".home-score").value,
    awayScore: card.querySelector(".away-score").value,
    status: card.querySelector(".match-status").value,
  };
  button.disabled = true;
  try {
    state = await request("/api/update-match", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    render();
    showToast("Match saved and standings recalculated");
  } catch (error) {
    showToast(error.message);
  } finally {
    button.disabled = false;
  }
});

loadInitial().catch((error) => showToast(error.message));
