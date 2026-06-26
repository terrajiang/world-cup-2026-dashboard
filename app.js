let state = null;

const tabs = document.querySelectorAll(".tab");
const standingsPanel = document.querySelector("#standingsPanel");
const schedulePanel = document.querySelector("#schedulePanel");
const rulesPanel = document.querySelector("#rulesPanel");
const treePanel = document.querySelector("#treePanel");
const playersPanel = document.querySelector("#playersPanel");
const imagePanel = document.querySelector("#imagePanel");
const refreshBtn = document.querySelector("#refreshBtn");
const generateImageBtn = document.querySelector("#generateImageBtn");
const countryLookup = document.querySelector("#countryLookup");
const dateLookup = document.querySelector("#dateLookup");
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
const PST_SLOTS = ["9:00 AM PST", "11:00 AM PST", "1:00 PM PST", "3:00 PM PST", "5:00 PM PST", "7:00 PM PST"];

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

function formatDateLong(value) {
  return new Intl.DateTimeFormat("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
  }).format(new Date(`${value}T12:00:00`));
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

function pstTime(match, collection) {
  if (match.timePst) return match.timePst;
  const sameDate = collection.filter((item) => item.date === match.date);
  const index = Math.max(
    0,
    sameDate.findIndex((item) => (match.id && item.id === match.id) || (match.slot && item.slot === match.slot)),
  );
  return PST_SLOTS[index % PST_SLOTS.length];
}

function scoreText(match) {
  if (match.homeScore === null || match.homeScore === undefined || match.awayScore === null || match.awayScore === undefined) {
    return match.status === "Live" ? "Live" : "vs";
  }
  return `${match.homeScore} - ${match.awayScore}`;
}

function renderMeta() {
  document.querySelector("#lastUpdated").textContent = state.lastUpdated
    ? `Updated ${formatDate(state.lastUpdated)}`
    : "Not updated yet";
  const sourceNote = document.querySelector("#sourceNote");
  if (sourceNote) sourceNote.textContent = "";
}

function renderImagePreview() {
  const image = document.querySelector("#standingsImage");
  if (state.imagePath) {
    image.src = `${state.imagePath}?v=${encodeURIComponent(state.lastUpdated || Date.now())}`;
  } else {
    image.removeAttribute("src");
  }
}

function countryOptions() {
  return Object.values(state.groups)
    .flat()
    .map((row) => row.team)
    .sort((a, b) => a.localeCompare(b));
}

function gameDates() {
  return [...new Set(state.matches.map((match) => match.date))].sort();
}

function renderLookupControls() {
  const selectedCountry = countryLookup.value;
  const selectedDate = dateLookup.value;
  countryLookup.innerHTML = `<option value="">All countries</option>${countryOptions()
    .map((team) => `<option value="${team}">${TEAM_FLAGS[team] ? `${TEAM_FLAGS[team]} ` : ""}${team}</option>`)
    .join("")}`;
  dateLookup.innerHTML = `<option value="">All dates</option>${gameDates()
    .map((date) => `<option value="${date}">${formatDateLong(date)}</option>`)
    .join("")}`;
  countryLookup.value = selectedCountry;
  dateLookup.value = selectedDate;
}

function renderGroups() {
  const grid = document.querySelector("#groupsGrid");
  grid.innerHTML = "";
  Object.entries(state.groups).forEach(([group, rows]) => {
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

function knockoutTeams(match) {
  return {
    home: resolveSlot(match.home).text,
    away: resolveSlot(match.away).text,
  };
}

function scheduleItems() {
  const groupItems = state.matches.map((match) => ({
    ...match,
    phase: `Group ${match.group}`,
    homeLabel: match.home,
    awayLabel: match.away,
    score: scoreText(match),
  }));
  const knockoutItems = state.knockout.map((match) => {
    const teams = knockoutTeams(match);
    return {
      ...match,
      id: match.slot,
      phase: match.round,
      homeLabel: teams.home,
      awayLabel: teams.away,
      status: "Pending",
      score: "Result TBD",
    };
  });
  return [...groupItems, ...knockoutItems].sort((a, b) => a.date.localeCompare(b.date) || a.id.localeCompare(b.id));
}

function matchResultHtml(match, compact = false, collection = state.matches) {
  const isFinished = match.status === "FT";
  const isLive = match.status === "Live";
  return `
    <article class="result-card ${isFinished ? "finished" : ""} ${isLive ? "live" : ""}">
      <div class="result-meta">
        <span>${match.phase || `Group ${match.group}`} · ${formatDate(match.date)} · ${pstTime(match, collection)}</span>
        <span>${match.status}</span>
      </div>
      <div class="result-main">
        <span>${teamLabel(match.homeLabel || match.home)}</span>
        <strong>${match.score || scoreText(match)}</strong>
        <span>${teamLabel(match.awayLabel || match.away)}</span>
      </div>
      ${compact ? "" : `<div class="result-date">${match.date}</div>`}
    </article>
  `;
}

function matchesByDate() {
  return [...state.matches].sort((a, b) => a.date.localeCompare(b.date) || a.id.localeCompare(b.id));
}

function renderMatchLookup() {
  const container = document.querySelector("#matchLookupResults");
  const country = countryLookup.value;
  const date = dateLookup.value;
  if (!country && !date) {
    container.innerHTML = `<div class="empty-state">Choose a country, a date, or both to find group-stage match results.</div>`;
    return;
  }
  const matches = matchesByDate().filter((match) => {
    const countryMatch = !country || match.home === country || match.away === country;
    const dateMatch = !date || match.date === date;
    return countryMatch && dateMatch;
  });
  container.innerHTML = matches.length
    ? matches.map((match) => matchResultHtml(match, true, state.matches)).join("")
    : `<div class="empty-state">No group-stage games match those filters.</div>`;
}

function renderSchedule() {
  const container = document.querySelector("#scheduleList");
  const items = scheduleItems();
  let currentDate = "";
  container.innerHTML = items
    .map((match) => {
      const heading = match.date === currentDate ? "" : `<h3>${formatDateLong(match.date)}</h3>`;
      currentDate = match.date;
      return `${heading}${matchResultHtml(match, false, items)}`;
    })
    .join("");
}

function renderMatches() {
  const list = document.querySelector("#matchesList");
  const matches = state.matches;
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

function treeRow(total, index) {
  const rows = {
    8: [1, 3, 5, 7, 9, 11, 13, 15],
    4: [2, 6, 10, 14],
    2: [4, 12],
    1: [8],
  };
  return rows[total]?.[index] || index * 2 + 1;
}

function cardHtml(match, side = "", row = null) {
  const home = resolveSlot(match.home);
  const away = resolveSlot(match.away);
  const rowStyle = row ? `style="grid-row: ${row} / span 2"` : "";
  return `
    <article class="tree-card ${side}" data-slot="${match.slot}" ${rowStyle}>
      <div class="tree-slot"><span>${match.slot} · ${formatDate(match.date)}</span><span>${pstTime(match, state.knockout)}</span></div>
      <div class="tree-pair">
        <div class="tree-team ${home.filled ? "filled" : "pending"}">${slotHtml(home)}</div>
        <div class="tree-team ${away.filled ? "filled" : "pending"}">${slotHtml(away)}</div>
      </div>
      <div class="tree-result">Result: TBD</div>
    </article>
  `;
}

function renderTreeSide(roundGroups, side) {
  return `
    <section class="bracket-side ${side}">
      <div class="tree-side-grid">
        ${roundGroups
          .map(
            (group) => `
              <section class="round-column ${side}">
                <div class="round-heading">${group.title}</div>
                <div class="round-stack">
                  ${group.matches.map((match, index) => cardHtml(match, side, treeRow(group.matches.length, index))).join("")}
                </div>
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
    ${renderTreeSide(left, "left")}
    <section class="final-column">
      <div class="round-heading">Final</div>
      <div class="round-stack final-stack">
        ${cardHtml(bySlot.Final, "final", 8)}
        ${cardHtml(bySlot["3P"], "final", 12)}
      </div>
    </section>
    ${renderTreeSide(right, "right")}
    <svg class="connector-layer" id="connectorLayer" aria-hidden="true"></svg>
  `;
  requestAnimationFrame(drawBracketConnectors);
}

function branchPairs(prefix, count, targetPrefix) {
  return Array.from({ length: count }, (_, index) => [
    `${prefix}-${index * 2 + 1}`,
    `${targetPrefix}-${index + 1}`,
    `${prefix}-${index * 2 + 2}`,
  ]);
}

function bracketConnections() {
  return [
    ...branchPairs("R32", 8, "R16"),
    ...branchPairs("R16", 4, "QF"),
    ...branchPairs("QF", 2, "SF"),
    ["SF-1", "Final", "SF-2"],
    ["SF-1", "3P", "SF-2"],
  ];
}

function cardAnchor(card, mapRect, towardCenter) {
  const bracket = document.querySelector("#bracket");
  const rect = card.getBoundingClientRect();
  const scrollLeft = bracket?.scrollLeft || 0;
  const scrollTop = bracket?.scrollTop || 0;
  const y = rect.top - mapRect.top + rect.height / 2 + scrollTop;
  const left = rect.left - mapRect.left + scrollLeft;
  const right = rect.right - mapRect.left + scrollLeft;
  if (towardCenter === "left") return { x: left, y };
  if (towardCenter === "right") return { x: right, y };
  return { x: left + rect.width / 2, y };
}

function drawCurve(svg, from, to, color) {
  const direction = to.x > from.x ? 1 : -1;
  const bend = Math.max(52, Math.min(180, Math.abs(to.x - from.x) * 0.42));
  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("d", `M ${from.x} ${from.y} C ${from.x + direction * bend} ${from.y}, ${to.x - direction * bend} ${to.y}, ${to.x} ${to.y}`);
  path.setAttribute("fill", "none");
  path.setAttribute("stroke", color);
  path.setAttribute("stroke-width", "2");
  path.setAttribute("stroke-linecap", "round");
  path.setAttribute("stroke-linejoin", "round");
  svg.appendChild(path);
}

function drawBranch(svg, points, color) {
  const [a, target, b] = points;
  const midX = (a.x + b.x) / 2;
  const bend = Math.max(32, Math.min(120, Math.abs(target.x - midX) * 0.45));
  const outDirection = target.x > midX ? 1 : -1;
  const stemX = midX + outDirection * bend;
  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute(
    "d",
    [
      `M ${a.x} ${a.y}`,
      `C ${a.x + outDirection * bend} ${a.y}, ${stemX} ${a.y}, ${stemX} ${(a.y + b.y) / 2}`,
      `C ${stemX} ${b.y}, ${b.x + outDirection * bend} ${b.y}, ${b.x} ${b.y}`,
      `M ${stemX} ${(a.y + b.y) / 2}`,
      `C ${stemX} ${target.y}, ${target.x - outDirection * bend} ${target.y}, ${target.x} ${target.y}`,
    ].join(" "),
  );
  path.setAttribute("fill", "none");
  path.setAttribute("stroke", color);
  path.setAttribute("stroke-width", "2");
  path.setAttribute("stroke-linecap", "round");
  path.setAttribute("stroke-linejoin", "round");
  svg.appendChild(path);
}

function drawBracketConnectors() {
  const bracket = document.querySelector("#bracket");
  const svg = document.querySelector("#connectorLayer");
  if (!bracket || !svg) return;
  const mapRect = bracket.getBoundingClientRect();
  const width = bracket.scrollWidth;
  const height = bracket.scrollHeight;
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("width", width);
  svg.setAttribute("height", height);
  svg.innerHTML = "";

  const finalRect = bracket.querySelector('[data-slot="Final"]')?.getBoundingClientRect();
  const finalCenter = finalRect ? finalRect.left + finalRect.width / 2 : mapRect.left + mapRect.width / 2;
  bracketConnections().forEach(([upperSlot, targetSlot, lowerSlot], index) => {
    const color = index % 3 === 0 ? "#d7d1c3" : index % 3 === 1 ? "#cbd8cf" : "#d4cbe0";
    const upper = bracket.querySelector(`[data-slot="${upperSlot}"]`);
    const target = bracket.querySelector(`[data-slot="${targetSlot}"]`);
    const lower = bracket.querySelector(`[data-slot="${lowerSlot}"]`);
    if (!upper || !target || !lower) return;

    if (targetSlot === "Final" || targetSlot === "3P") {
      drawCurve(svg, cardAnchor(upper, mapRect, "right"), cardAnchor(target, mapRect, "left"), color);
      drawCurve(svg, cardAnchor(lower, mapRect, "left"), cardAnchor(target, mapRect, "right"), color);
      return;
    }

    const upperCenter = upper.getBoundingClientRect().left + upper.getBoundingClientRect().width / 2;
    const toward = upperCenter < finalCenter ? "right" : "left";
    const targetToward = toward === "right" ? "left" : "right";
    drawBranch(
      svg,
      [
        cardAnchor(upper, mapRect, toward),
        cardAnchor(target, mapRect, targetToward),
        cardAnchor(lower, mapRect, toward),
      ],
      color,
    );
  });
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
  renderLookupControls();
  renderGroups();
  renderMatchLookup();
  renderSchedule();
  renderMatches();
  renderBracket();
  renderPlayerStats();
  renderImagePreview();
}

async function loadInitial() {
  state = await request("/api/data");
  render();
}

tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    tabs.forEach((item) => item.classList.toggle("active", item === tab));
    standingsPanel.classList.toggle("active", tab.dataset.tab === "standings");
    schedulePanel.classList.toggle("active", tab.dataset.tab === "schedule");
    rulesPanel.classList.toggle("active", tab.dataset.tab === "rules");
    playersPanel.classList.toggle("active", tab.dataset.tab === "players");
    treePanel.classList.toggle("active", tab.dataset.tab === "tree");
    imagePanel.classList.toggle("active", tab.dataset.tab === "image");
    if (tab.dataset.tab === "tree") {
      requestAnimationFrame(drawBracketConnectors);
    }
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

generateImageBtn.addEventListener("click", async () => {
  generateImageBtn.disabled = true;
  generateImageBtn.textContent = "Generating";
  try {
    state = await request("/api/generate-image", { method: "POST" });
    render();
    showToast("Standings image generated");
  } catch (error) {
    showToast(`Image generation failed: ${error.message}`);
  } finally {
    generateImageBtn.disabled = false;
    generateImageBtn.textContent = "Generate Image";
  }
});

countryLookup.addEventListener("change", renderMatchLookup);
dateLookup.addEventListener("change", renderMatchLookup);
playerSearch.addEventListener("input", renderPlayerStats);
window.addEventListener("resize", drawBracketConnectors);
document.querySelector("#bracket").addEventListener("scroll", drawBracketConnectors);

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
