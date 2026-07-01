let state = null;

const tabs = document.querySelectorAll(".tab");
const liveScoreboardBar = document.querySelector("#liveScoreboardBar");
const standingsPanel = document.querySelector("#standingsPanel");
const schedulePanel = document.querySelector("#schedulePanel");
const rulesPanel = document.querySelector("#rulesPanel");
const historyPanel = document.querySelector("#historyPanel");
const treePanel = document.querySelector("#treePanel");
const playersPanel = document.querySelector("#playersPanel");
const refreshBtn = document.querySelector("#refreshBtn");
const countryLookup = document.querySelector("#countryLookup");
const dateLookup = document.querySelector("#dateLookup");
const historyCountry = document.querySelector("#historyCountry");
const historyFilter = document.querySelector("#historyFilter");
const playerSearch = document.querySelector("#playerSearch");
const toast = document.querySelector("#toast");
const LIVE_REFRESH_INTERVAL_MS = 45000;
let liveRefreshTimer = null;
let liveRefreshInFlight = false;
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
  "Curaçao": "🇨🇼",
  Czechia: "🇨🇿",
  "Côte d'Ivoire": "🇨🇮",
  "DR Congo": "🇨🇩",
  Ecuador: "🇪🇨",
  Egypt: "🇪🇬",
  England: "css:england",
  France: "🇫🇷",
  Germany: "🇩🇪",
  Ghana: "🇬🇭",
  Haiti: "🇭🇹",
  Hungary: "🇭🇺",
  Iran: "🇮🇷",
  Iraq: "🇮🇶",
  Italy: "🇮🇹",
  Japan: "🇯🇵",
  Jordan: "🇯🇴",
  Mexico: "🇲🇽",
  Morocco: "🇲🇦",
  Netherlands: "🇳🇱",
  "New Zealand": "🇳🇿",
  Norway: "🇳🇴",
  Panama: "🇵🇦",
  Paraguay: "🇵🇾",
  Poland: "🇵🇱",
  Portugal: "🇵🇹",
  Qatar: "🇶🇦",
  "Saudi Arabia": "🇸🇦",
  Scotland: "css:scotland",
  Senegal: "🇸🇳",
  "South Africa": "🇿🇦",
  "South Korea": "🇰🇷",
  Spain: "🇪🇸",
  Sweden: "🇸🇪",
  Switzerland: "🇨🇭",
  Tunisia: "🇹🇳",
  "Türkiye": "🇹🇷",
  "United States": "🇺🇸",
  Uruguay: "🇺🇾",
  Uzbekistan: "🇺🇿",
  Bulgaria: "🇧🇬",
  Chile: "🇨🇱",
  "Soviet Union": "css:soviet",
  Yugoslavia: "css:yugoslavia",
};
const SELECT_FLAG_FALLBACKS = {
  England: "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
  Scotland: "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
};
const FEATURED_PLAYERS = new Set(["Kylian Mbappé", "Lionel Messi", "Cristiano Ronaldo", "Erling Haaland"]);
const SEEDED_TEAMS = new Set([
  "Argentina",
  "Belgium",
  "Brazil",
  "Canada",
  "England",
  "France",
  "Germany",
  "Mexico",
  "Netherlands",
  "Portugal",
  "Spain",
  "United States",
]);
const PLACEMENT_EMOJIS = {
  Champion: "🥇",
  "Runner-up": "🥈",
  Third: "🥉",
  Fourth: "🏅",
};
const HISTORY_TOP_FOUR = [
  { year: 1930, champion: "Uruguay", runnerUp: "Argentina", third: "United States", fourth: "Yugoslavia" },
  { year: 1934, champion: "Italy", runnerUp: "Czechoslovakia", third: "Germany", fourth: "Austria" },
  { year: 1938, champion: "Italy", runnerUp: "Hungary", third: "Brazil", fourth: "Sweden" },
  { year: 1950, champion: "Uruguay", runnerUp: "Brazil", third: "Sweden", fourth: "Spain" },
  { year: 1954, champion: "West Germany", runnerUp: "Hungary", third: "Austria", fourth: "Uruguay" },
  { year: 1958, champion: "Brazil", runnerUp: "Sweden", third: "France", fourth: "West Germany" },
  { year: 1962, champion: "Brazil", runnerUp: "Czechoslovakia", third: "Chile", fourth: "Yugoslavia" },
  { year: 1966, champion: "England", runnerUp: "West Germany", third: "Portugal", fourth: "Soviet Union" },
  { year: 1970, champion: "Brazil", runnerUp: "Italy", third: "West Germany", fourth: "Uruguay" },
  { year: 1974, champion: "West Germany", runnerUp: "Netherlands", third: "Poland", fourth: "Brazil" },
  { year: 1978, champion: "Argentina", runnerUp: "Netherlands", third: "Brazil", fourth: "Italy" },
  { year: 1982, champion: "Italy", runnerUp: "West Germany", third: "Poland", fourth: "France" },
  { year: 1986, champion: "Argentina", runnerUp: "West Germany", third: "France", fourth: "Belgium" },
  { year: 1990, champion: "West Germany", runnerUp: "Argentina", third: "Italy", fourth: "England" },
  { year: 1994, champion: "Brazil", runnerUp: "Italy", third: "Sweden", fourth: "Bulgaria" },
  { year: 1998, champion: "France", runnerUp: "Brazil", third: "Croatia", fourth: "Netherlands" },
  { year: 2002, champion: "Brazil", runnerUp: "Germany", third: "Türkiye", fourth: "South Korea" },
  { year: 2006, champion: "Italy", runnerUp: "France", third: "Germany", fourth: "Portugal" },
  { year: 2010, champion: "Spain", runnerUp: "Netherlands", third: "Germany", fourth: "Uruguay" },
  { year: 2014, champion: "Germany", runnerUp: "Argentina", third: "Netherlands", fourth: "Brazil" },
  { year: 2018, champion: "France", runnerUp: "Croatia", third: "Belgium", fourth: "England" },
  { year: 2022, champion: "Argentina", runnerUp: "France", third: "Croatia", fourth: "Morocco" },
];
const HISTORY_PLACEHOLDER_2026 = { year: 2026, champion: "TBD", runnerUp: "TBD", third: "TBD", fourth: "TBD", placeholder: true };
const HISTORY_FINISHES = [
  ["champion", "Champion"],
  ["runnerUp", "Runner-up"],
  ["third", "Third"],
  ["fourth", "Fourth"],
];
const HISTORY_STAGE_OVERRIDES = {
  Algeria: { 1982: "Group stage", 1986: "Group stage", 2010: "Group stage", 2014: "Round of 16" },
  Argentina: { 1934: "Round of 16", 1958: "Group stage", 1962: "Group stage", 1974: "Second group stage", 1982: "Second group stage", 1994: "Round of 16", 1998: "Quarterfinal", 2002: "Group stage", 2006: "Quarterfinal", 2010: "Quarterfinal", 2018: "Round of 16" },
  Australia: { 1974: "Group stage", 2006: "Round of 16", 2010: "Group stage", 2014: "Group stage", 2018: "Group stage", 2022: "Round of 16" },
  Austria: { 1978: "Second group stage", 1982: "Second group stage", 1990: "Group stage", 1998: "Group stage" },
  Belgium: { 1930: "Group stage", 1934: "Round of 16", 1938: "Round of 16", 1954: "Group stage", 1970: "Group stage", 1982: "Second group stage", 1990: "Round of 16", 1994: "Round of 16", 1998: "Group stage", 2002: "Round of 16", 2014: "Quarterfinal", 2022: "Group stage" },
  "Bosnia and Herzegovina": { 2014: "Group stage" },
  Brazil: { 1930: "Group stage", 1934: "Round of 16", 1966: "Group stage", 1982: "Second group stage", 1986: "Quarterfinal", 1990: "Round of 16", 2006: "Quarterfinal", 2010: "Quarterfinal", 2018: "Quarterfinal", 2022: "Quarterfinal" },
  Canada: { 1986: "Group stage", 2022: "Group stage" },
  Colombia: { 1962: "Group stage", 1990: "Round of 16", 1994: "Group stage", 1998: "Group stage", 2014: "Quarterfinal", 2018: "Round of 16" },
  Croatia: { 2002: "Group stage", 2006: "Group stage", 2014: "Group stage" },
  Czechia: { 1982: "Group stage", 2006: "Group stage" },
  "Côte d'Ivoire": { 2006: "Group stage", 2010: "Group stage", 2014: "Group stage" },
  "DR Congo": { 1974: "Group stage" },
  Ecuador: { 2002: "Group stage", 2006: "Round of 16", 2014: "Group stage", 2022: "Group stage" },
  Egypt: { 1934: "Round of 16", 1990: "Group stage", 2018: "Group stage" },
  England: { 1950: "Group stage", 1954: "Quarterfinal", 1958: "Group stage", 1962: "Quarterfinal", 1970: "Quarterfinal", 1982: "Second group stage", 1986: "Quarterfinal", 1998: "Round of 16", 2002: "Quarterfinal", 2006: "Quarterfinal", 2010: "Round of 16", 2014: "Group stage", 2022: "Quarterfinal" },
  France: { 1930: "Group stage", 1934: "Round of 16", 1938: "Quarterfinal", 1954: "Group stage", 1966: "Group stage", 1978: "Group stage", 2002: "Group stage", 2010: "Group stage", 2014: "Quarterfinal" },
  Germany: { 1938: "Round of 16", 1978: "Second group stage", 1994: "Quarterfinal", 1998: "Quarterfinal", 2018: "Group stage", 2022: "Group stage" },
  Ghana: { 2006: "Round of 16", 2010: "Quarterfinal", 2014: "Group stage", 2022: "Group stage" },
  Haiti: { 1974: "Group stage" },
  Iran: { 1978: "Group stage", 1998: "Group stage", 2006: "Group stage", 2014: "Group stage", 2018: "Group stage", 2022: "Group stage" },
  Iraq: { 1986: "Group stage" },
  Japan: { 1998: "Group stage", 2002: "Round of 16", 2006: "Group stage", 2010: "Round of 16", 2014: "Group stage", 2018: "Round of 16", 2022: "Round of 16" },
  Mexico: { 1930: "Group stage", 1950: "Group stage", 1954: "Group stage", 1958: "Group stage", 1962: "Group stage", 1966: "Group stage", 1970: "Quarterfinal", 1978: "Group stage", 1986: "Quarterfinal", 1994: "Round of 16", 1998: "Round of 16", 2002: "Round of 16", 2006: "Round of 16", 2010: "Round of 16", 2014: "Round of 16", 2018: "Round of 16", 2022: "Group stage" },
  Morocco: { 1970: "Group stage", 1986: "Round of 16", 1994: "Group stage", 1998: "Group stage", 2018: "Group stage" },
  Netherlands: { 1934: "Round of 16", 1938: "Round of 16", 1990: "Round of 16", 1994: "Quarterfinal", 2006: "Round of 16", 2022: "Quarterfinal" },
  "New Zealand": { 1982: "Group stage", 2010: "Group stage" },
  Norway: { 1938: "Round of 16", 1994: "Group stage", 1998: "Round of 16" },
  Panama: { 2018: "Group stage" },
  Paraguay: { 1930: "Group stage", 1950: "Group stage", 1958: "Group stage", 1986: "Round of 16", 1998: "Round of 16", 2002: "Round of 16", 2006: "Group stage", 2010: "Quarterfinal" },
  Portugal: { 1986: "Group stage", 2002: "Group stage", 2010: "Round of 16", 2014: "Group stage", 2018: "Round of 16", 2022: "Quarterfinal" },
  Qatar: { 2022: "Group stage" },
  "Saudi Arabia": { 1994: "Round of 16", 1998: "Group stage", 2002: "Group stage", 2006: "Group stage", 2018: "Group stage", 2022: "Group stage" },
  Scotland: { 1954: "Group stage", 1958: "Group stage", 1974: "Group stage", 1978: "Group stage", 1982: "Group stage", 1986: "Group stage", 1990: "Group stage", 1998: "Group stage" },
  Senegal: { 2002: "Quarterfinal", 2018: "Group stage", 2022: "Round of 16" },
  "South Africa": { 1998: "Group stage", 2002: "Group stage", 2010: "Group stage" },
  "South Korea": { 1954: "Group stage", 1986: "Group stage", 1990: "Group stage", 1994: "Group stage", 1998: "Group stage", 2006: "Group stage", 2010: "Round of 16", 2014: "Group stage", 2018: "Group stage", 2022: "Round of 16" },
  Spain: { 1934: "Quarterfinal", 1962: "Group stage", 1966: "Group stage", 1978: "Group stage", 1982: "Second group stage", 1986: "Quarterfinal", 1990: "Round of 16", 1994: "Quarterfinal", 1998: "Group stage", 2002: "Quarterfinal", 2006: "Round of 16", 2014: "Group stage", 2018: "Round of 16", 2022: "Round of 16" },
  Sweden: { 1934: "Quarterfinal", 1970: "Group stage", 1974: "Second group stage", 1978: "Group stage", 1990: "Group stage", 2002: "Round of 16", 2006: "Round of 16", 2018: "Quarterfinal" },
  Switzerland: { 1934: "Quarterfinal", 1938: "Quarterfinal", 1950: "Group stage", 1954: "Quarterfinal", 1962: "Group stage", 1966: "Group stage", 1994: "Round of 16", 2006: "Round of 16", 2010: "Group stage", 2014: "Round of 16", 2018: "Round of 16", 2022: "Round of 16" },
  Tunisia: { 1978: "Group stage", 1998: "Group stage", 2002: "Group stage", 2006: "Group stage", 2018: "Group stage", 2022: "Group stage" },
  Türkiye: { 1954: "Group stage" },
  "United States": { 1934: "Round of 16", 1950: "Group stage", 1990: "Group stage", 1994: "Round of 16", 1998: "Group stage", 2002: "Quarterfinal", 2006: "Group stage", 2010: "Round of 16", 2014: "Round of 16", 2022: "Round of 16" },
  Uruguay: { 1962: "Group stage", 1966: "Quarterfinal", 1974: "Group stage", 1986: "Round of 16", 1990: "Round of 16", 2002: "Group stage", 2014: "Round of 16", 2018: "Quarterfinal", 2022: "Group stage" },
};

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
  const nameClass = SEEDED_TEAMS.has(team) ? "team-name seed-team" : "team-name";
  if (flag?.startsWith("css:")) {
    return `<span class="flag flag-css flag-${flag.slice(4)}" aria-hidden="true"></span><span class="${nameClass}">${team}</span>`;
  }
  return `${flag ? `<span class="flag" aria-hidden="true">${flag}</span>` : ""}<span class="${nameClass}">${team}</span>`;
}

function optionLabel(team) {
  const flag = TEAM_FLAGS[team];
  if (SELECT_FLAG_FALLBACKS[team]) return `${SELECT_FLAG_FALLBACKS[team]} ${team}`;
  return `${flag && !flag.startsWith("css:") ? `${flag} ` : ""}${team}`;
}

function normalizeCountry(country) {
  const aliases = {
    "West Germany": "Germany",
    Czechoslovakia: "Czechia",
    Turkey: "Türkiye",
  };
  return aliases[country] || country;
}

function pstTime(match, collection) {
  return match.timePst || "Time TBD";
}

function pstMinutes(label) {
  const match = String(label || "").match(/(\d{1,2}):(\d{2})\s*(AM|PM)/i);
  if (!match) return Number.MAX_SAFE_INTEGER;
  let hours = Number(match[1]) % 12;
  const minutes = Number(match[2]);
  if (match[3].toUpperCase() === "PM") hours += 12;
  return hours * 60 + minutes;
}

function compareByKickoff(a, b) {
  return (
    a.date.localeCompare(b.date) ||
    pstMinutes(pstTime(a)) - pstMinutes(pstTime(b)) ||
    String(a.id || a.slot).localeCompare(String(b.id || b.slot), undefined, { numeric: true })
  );
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
    .map((team) => `<option value="${team}">${optionLabel(team)}</option>`)
    .join("")}`;
  dateLookup.innerHTML = `<option value="">All dates</option>${gameDates()
    .map((date) => `<option value="${date}">${formatDateLong(date)}</option>`)
    .join("")}`;
  countryLookup.value = selectedCountry;
  dateLookup.value = selectedDate;
}

function renderHistoryControls() {
  const selected = historyCountry.value;
  historyCountry.innerHTML = `<option value="">All countries</option>${countryOptions()
    .map((team) => `<option value="${team}">${optionLabel(team)}</option>`)
    .join("")}`;
  historyCountry.value = selected;
  historyFilter.disabled = !selected;
}

function selectedCountryFinish(row, selected) {
  if (!selected) return "Choose a country";
  if (row.placeholder) return "Tournament pending";
  const finish = HISTORY_FINISHES.find(([key]) => normalizeCountry(row[key]) === selected);
  return finish ? finish[1] : HISTORY_STAGE_OVERRIDES[selected]?.[row.year] || "Did not qualify";
}

function finishDisplay(value) {
  return PLACEMENT_EMOJIS[value] || value;
}

function finishClass(value) {
  const normalized = value.toLowerCase();
  if (PLACEMENT_EMOJIS[value]) return "history-hit";
  if (normalized.includes("group stage")) return "stage-group";
  if (normalized === "round of 32" || normalized === "round of 16") return "stage-round";
  if (normalized === "quarterfinal") return "stage-quarterfinal";
  return "";
}

function historyRowMatchesFilter(finish, filterValue) {
  if (!filterValue) return true;
  const normalized = finish.toLowerCase();
  if (filterValue === "podium") return Boolean(PLACEMENT_EMOJIS[finish]);
  if (filterValue === "round") return normalized === "round of 32" || normalized === "round of 16";
  if (filterValue === "quarterfinal") return normalized === "quarterfinal";
  if (filterValue === "group") return normalized.includes("group stage");
  if (filterValue === "qualified") return normalized !== "did not qualify";
  if (filterValue === "dnq") return normalized === "did not qualify";
  return true;
}

function historyCountryCell(country) {
  if (country === "TBD") return "TBD";
  return teamLabel(normalizeCountry(country));
}

function countCell(entry) {
  if (!entry) return "";
  const [country, count] = entry;
  return `${teamLabel(country)} <strong>${count}</strong>`;
}

function resultTeams(match) {
  if (!match || match.status !== "FT" || match.homeScore === null || match.awayScore === null) return null;
  const teams = knockoutTeams(match);
  if ([teams.home, teams.away].some((team) => /^(Winner|Loser|TBD)/.test(team))) return null;
  if (match.winner && [teams.home, teams.away].includes(match.winner)) {
    return {
      winner: match.winner,
      loser: match.winner === teams.home ? teams.away : teams.home,
    };
  }
  const homeWon = Number(match.homeScore) > Number(match.awayScore);
  return {
    winner: homeWon ? teams.home : teams.away,
    loser: homeWon ? teams.away : teams.home,
  };
}

function currentTopFourRow() {
  const bySlot = Object.fromEntries((state.knockout || []).map((match) => [match.slot, match]));
  const final = resultTeams(bySlot.Final);
  const thirdPlace = resultTeams(bySlot["3P"]);
  if (!final || !thirdPlace) return HISTORY_PLACEHOLDER_2026;
  return {
    year: 2026,
    champion: final.winner,
    runnerUp: final.loser,
    third: thirdPlace.winner,
    fourth: thirdPlace.loser,
  };
}

function renderHistory() {
  const selected = historyCountry.value;
  historyFilter.disabled = !selected;
  if (!selected) historyFilter.value = "";
  const filterValue = historyFilter.value;
  const historyRows = [currentTopFourRow(), ...HISTORY_TOP_FOUR]
    .sort((a, b) => b.year - a.year)
    .filter((row) => !selected || historyRowMatchesFilter(selectedCountryFinish(row, selected), filterValue));
  document.querySelector("#historyQueryHead").textContent = selected ? `${selected} finish` : "Selected country";
  document.querySelector("#historyBody").innerHTML = historyRows.map(
    (row) => {
      const finish = selectedCountryFinish(row, selected);
      const stageClass = selected ? finishClass(finish) : "";
      return `
        <tr class="${row.placeholder ? "history-placeholder" : ""}">
          <td>${row.year}</td>
          <td>${historyCountryCell(row.champion)}</td>
          <td>${historyCountryCell(row.runnerUp)}</td>
          <td>${historyCountryCell(row.third)}</td>
          <td>${historyCountryCell(row.fourth)}</td>
          <td class="${stageClass}"><span class="history-stage">${finishDisplay(finish)}</span></td>
        </tr>
      `;
    },
  ).join("");
  if (!historyRows.length) {
    document.querySelector("#historyBody").innerHTML = `
      <tr>
        <td colspan="6" class="history-empty">No rows match that filter.</td>
      </tr>
    `;
  }

  const counts = Object.fromEntries(HISTORY_FINISHES.map(([key]) => [key, {}]));
  HISTORY_TOP_FOUR.forEach((row) => {
    HISTORY_FINISHES.forEach(([key]) => {
      const country = normalizeCountry(row[key]);
      counts[key][country] = (counts[key][country] || 0) + 1;
    });
  });
  document.querySelector("#historyCounts").innerHTML = `
    <h3>Placement Counts By Country</h3>
    <div class="history-table-wrap">
      <table class="history-table count-table">
        <thead>
          <tr>
            <th>Rank</th>
            <th>🥇</th>
            <th>🥈</th>
            <th>🥉</th>
            <th>🏅</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          ${(() => {
            const rankings = HISTORY_FINISHES.map(([key]) => Object.entries(counts[key]).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])));
            const maxRows = Math.max(...rankings.map((ranking) => ranking.length));
            return Array.from({ length: maxRows }, (_, index) => `
              <tr>
                <td>${index + 1}</td>
                ${rankings.map((ranking) => `<td>${countCell(ranking[index])}</td>`).join("")}
                <td></td>
              </tr>
            `).join("");
          })()}
        </tbody>
      </table>
    </div>
  `;
}

function liveMatches() {
  return (state.matches || []).filter((match) => match.status === "Live");
}

function liveKnockoutMatches() {
  return (state.knockout || []).filter((match) => match.status === "Live");
}

function allLiveMatches() {
  return [...liveMatches(), ...liveKnockoutMatches()];
}

function isTeamLive(team) {
  return liveMatches().some((match) => match.home === team || match.away === team);
}

function isGroupLive(group) {
  return liveMatches().some((match) => match.group === group);
}

function liveBadge(text = "Live") {
  return `<span class="live-badge">${text}</span>`;
}

function scoreboardTeam(match, side) {
  if (match.phase) return match[`${side}Label`] || match[side];
  if (match.round) return knockoutTeams(match)[side];
  return match[side];
}

function renderLiveScoreboard() {
  if (!liveScoreboardBar) return;
  const live = allLiveMatches();
  if (!live.length) {
    liveScoreboardBar.innerHTML = `
      <span class="scoreboard-kicker">Scoreboard</span>
      <strong>No live games right now</strong>
      <span>Refresh checks for new live status and score changes.</span>
    `;
    liveScoreboardBar.classList.remove("has-live");
    return;
  }
  liveScoreboardBar.classList.add("has-live");
  liveScoreboardBar.innerHTML = `
    <span class="scoreboard-kicker">Live</span>
    ${live
      .map(
        (match) => `
          <span class="scoreboard-game">
            <span>${teamLabel(scoreboardTeam(match, "home"))}</span>
            <strong>${scoreText(match)}</strong>
            <span>${teamLabel(scoreboardTeam(match, "away"))}</span>
          </span>
        `,
      )
      .join("")}
  `;
}

function advancingThirdPlaceTeams() {
  return Object.values(state.groups)
    .map((rows) => rows.find((row) => row.status === "third"))
    .filter(Boolean)
    .filter((row) => row.played === 3)
    .sort((a, b) => b.pts - a.pts || b.gd - a.gd || b.gf - a.gf || a.team.localeCompare(b.team))
    .slice(0, 8)
    .map((row) => row.team);
}

function groupRowClass(row, advancingThirds) {
  if (row.status === "third") return advancingThirds.includes(row.team) ? "third advancing-third" : "third-place";
  return row.status || "";
}

function renderGroups() {
  const grid = document.querySelector("#groupsGrid");
  const advancingThirds = advancingThirdPlaceTeams();
  grid.innerHTML = "";
  Object.entries(state.groups).forEach(([group, rows]) => {
    const card = document.createElement("article");
    card.className = "group-card";
    card.innerHTML = `
      <div class="group-title"><strong>Group ${group}</strong><span>${isGroupLive(group) ? liveBadge("Live now") : `${rows.length} teams`}</span></div>
      <table>
        <thead>
          <tr><th>Team</th><th>GD</th><th>GF</th><th class="pts-head">Pts</th><th></th></tr>
        </thead>
        <tbody>
          ${rows
            .map(
              (row) => `
                <tr class="${groupRowClass(row, advancingThirds)}">
                  <td>${teamLabel(row.team)}${isTeamLive(row.team) ? liveBadge() : ""}</td>
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
    home: match.resolvedHome || resolveSlot(match.home).text,
    away: match.resolvedAway || resolveSlot(match.away).text,
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
      status: match.status || "Scheduled",
      score: scoreText(match),
    };
  });
  return [...groupItems, ...knockoutItems].sort(compareByKickoff);
}

function matchResultHtml(match, compact = false, collection = state.matches) {
  const isFinished = match.status === "FT";
  const isLive = match.status === "Live";
  return `
    <article class="result-card ${isFinished ? "finished" : ""} ${isLive ? "live" : ""}" data-match-id="${match.id || match.slot}" data-status="${match.status}">
      <div class="result-meta">
        <span>${match.phase || `Group ${match.group}`} · ${formatDate(match.date)} · ${pstTime(match, collection)}</span>
        <span>${isLive ? liveBadge("Live now") : match.status}</span>
      </div>
      <div class="result-main">
        <span>${teamLabel(match.homeLabel || match.home)}</span>
        <strong>${match.score || scoreText(match)}${match.resultDetail ? ` · ${match.resultDetail}` : ""}</strong>
        <span>${teamLabel(match.awayLabel || match.away)}</span>
      </div>
      ${compact ? "" : `<div class="result-date">${match.date}</div>`}
    </article>
  `;
}

function matchesByDate() {
  return [...state.matches].sort(compareByKickoff);
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

function scheduleFocusMatch() {
  const items = scheduleItems();
  const live = items.find((match) => match.status === "Live");
  if (live) return live;
  const today = new Date().toISOString().slice(0, 10);
  return items.find((match) => match.status !== "FT" && match.date >= today) || items.find((match) => match.status !== "FT");
}

function scrollScheduleToFocus() {
  const focus = scheduleFocusMatch();
  if (!focus) return;
  const selector = `[data-match-id="${focus.id || focus.slot}"]`;
  const card = document.querySelector(`#scheduleList ${selector}`);
  if (!card) return;
  card.classList.add("focus-match");
  card.scrollIntoView({ behavior: "smooth", block: "center" });
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

function knockoutSideResult(match, side) {
  if (match.status !== "FT" || match.homeScore === null || match.homeScore === undefined || match.awayScore === null || match.awayScore === undefined) {
    return "";
  }
  const homeTeam = match.resolvedHome || resolveSlot(match.home).text;
  const awayTeam = match.resolvedAway || resolveSlot(match.away).text;
  if (match.winner && [homeTeam, awayTeam].includes(match.winner)) {
    return side === "home" ? (match.winner === homeTeam ? "winner" : "loser") : match.winner === awayTeam ? "winner" : "loser";
  }
  const homeScore = Number(match.homeScore);
  const awayScore = Number(match.awayScore);
  if (homeScore === awayScore) return "";
  const homeWon = homeScore > awayScore;
  return side === "home" ? (homeWon ? "winner" : "loser") : homeWon ? "loser" : "winner";
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
  const home = match.resolvedHome ? { text: match.resolvedHome, filled: true } : resolveSlot(match.home);
  const away = match.resolvedAway ? { text: match.resolvedAway, filled: true } : resolveSlot(match.away);
  const isLive = match.status === "Live";
  const resultLabel = isLive
    ? `${liveBadge("Live now")} ${scoreText(match)}${match.resultDetail ? ` · ${match.resultDetail}` : ""}`
    : match.status === "FT"
      ? `FT ${scoreText(match)}${match.resultDetail ? ` · ${match.resultDetail}` : ""}`
      : "Result: TBD";
  const homeResult = knockoutSideResult(match, "home");
  const awayResult = knockoutSideResult(match, "away");
  const matchLabel = match.matchNo ? `M${match.matchNo}` : match.slot;
  const rowStyle = row ? `style="grid-row: ${row} / span 2"` : "";
  return `
    <article class="tree-card ${side} ${isLive ? "live" : ""}" data-slot="${match.slot}" data-status="${match.status || "Scheduled"}" ${rowStyle}>
      <div class="tree-slot"><span>${matchLabel} · ${formatDate(match.date)}</span><span>${pstTime(match, state.knockout)}</span></div>
      <div class="tree-pair">
        <div class="tree-team ${home.filled ? "filled" : "pending"} ${homeResult}">${slotHtml(home)}</div>
        <div class="tree-team ${away.filled ? "filled" : "pending"} ${awayResult}">${slotHtml(away)}</div>
      </div>
      <div class="tree-result">${resultLabel}</div>
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
    ${liveKnockoutMatches().length ? `<div class="tree-live-note">${liveBadge("Live now")} Knockout games are ongoing; bracket positions can move while scores update.</div>` : ""}
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
  renderHistoryControls();
  renderGroups();
  renderMatchLookup();
  renderSchedule();
  renderHistory();
  renderMatches();
  renderBracket();
  renderPlayerStats();
  renderLiveScoreboard();
  updateLiveTabs();
  scheduleLiveScoreRefresh();
  if (schedulePanel.classList.contains("active")) {
    setTimeout(scrollScheduleToFocus, 80);
  }
}

async function loadInitial() {
  state = await request("/api/data");
  render();
  activateTab(tabFromHash());
}

function tabFromHash() {
  const tabName = window.location.hash.replace("#", "");
  return document.querySelector(`.tab[data-tab="${tabName}"]`) ? tabName : "standings";
}

function activateTab(tabName) {
  tabs.forEach((item) => item.classList.toggle("active", item.dataset.tab === tabName));
  standingsPanel.classList.toggle("active", tabName === "standings");
  treePanel.classList.toggle("active", tabName === "tree");
  schedulePanel.classList.toggle("active", tabName === "schedule");
  playersPanel.classList.toggle("active", tabName === "players");
  historyPanel.classList.toggle("active", tabName === "history");
  rulesPanel.classList.toggle("active", tabName === "rules");
  if (tabName === "tree") {
    requestAnimationFrame(drawBracketConnectors);
  }
  if (tabName === "schedule") {
    setTimeout(scrollScheduleToFocus, 80);
  }
}

function updateLiveTabs() {
  const hasGroupLive = liveMatches().length > 0;
  const hasTreeLive = liveKnockoutMatches().length > 0;
  const hasAnyLive = hasGroupLive || hasTreeLive;
  tabs.forEach((tab) => {
    const baseLabel = tab.dataset.label || tab.textContent.replace(/\s*Live\s*$/i, "").trim();
    tab.dataset.label = baseLabel;
    const shouldShow =
      (hasGroupLive && ["standings", "schedule"].includes(tab.dataset.tab)) ||
      (hasAnyLive && tab.dataset.tab === "schedule") ||
      (hasTreeLive && tab.dataset.tab === "tree");
    tab.innerHTML = `${baseLabel}${shouldShow ? ' <span class="tab-live">Live</span>' : ""}`;
    tab.classList.toggle("has-live", shouldShow);
  });
}

function scheduleLiveScoreRefresh() {
  if (liveRefreshTimer) {
    clearInterval(liveRefreshTimer);
    liveRefreshTimer = null;
  }
  if (!allLiveMatches().length) return;
  liveRefreshTimer = setInterval(async () => {
    if (liveRefreshInFlight) return;
    liveRefreshInFlight = true;
    try {
      state = await request("/api/data");
      render();
    } catch (error) {
      console.warn("Live refresh failed", error);
    } finally {
      liveRefreshInFlight = false;
    }
  }, LIVE_REFRESH_INTERVAL_MS);
}

tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    window.location.hash = tab.dataset.tab;
    activateTab(tab.dataset.tab);
  });
});

window.addEventListener("hashchange", () => activateTab(tabFromHash()));

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

countryLookup.addEventListener("change", renderMatchLookup);
dateLookup.addEventListener("change", renderMatchLookup);
historyCountry.addEventListener("change", renderHistory);
historyFilter.addEventListener("change", renderHistory);
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
