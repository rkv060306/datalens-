/**
 * DataLens Palette & Theme Manager
 * Manages modern light theme default and multi-palette options.
 */

(function () {
  const PALETTE_KEY = "datalens_active_palette";
  const DEFAULT_PALETTE = "slate-light";

  const PALETTES = [
    { id: "slate-light", name: "☀️ Modern Light (Indigo)", bg: "#f8fafc", primary: "#4f46e5" },
    { id: "emerald-light", name: "🌿 Emerald Mint Light", bg: "#f0fdf4", primary: "#059669" },
    { id: "amber-light", name: "🌅 Sunset Amber Light", bg: "#fffbeb", primary: "#d97706" },
    { id: "violet-light", name: "💜 Royal Violet Light", bg: "#faf5ff", primary: "#7c3aed" },
    { id: "dark-obsidian", name: "🌙 Dark Obsidian Mode", bg: "#090d16", primary: "#6366f1" }
  ];

  function getActivePalette() {
    return localStorage.getItem(PALETTE_KEY) || DEFAULT_PALETTE;
  }

  function setActivePalette(paletteId) {
    const palette = PALETTES.find(p => p.id === paletteId) ? paletteId : DEFAULT_PALETTE;
    localStorage.setItem(PALETTE_KEY, palette);
    document.documentElement.setAttribute("data-theme", palette);
    
    // Broadcast event for dynamic chart re-rendering
    window.dispatchEvent(new CustomEvent("datalensThemeChanged", { detail: { palette } }));
  }

  function initTheme() {
    const current = getActivePalette();
    document.documentElement.setAttribute("data-theme", current);
  }

  function injectThemeSelector() {
    const headerActions = document.querySelector(".top-header .header-actions");
    if (!headerActions || document.getElementById("palette-theme-select")) return;

    const select = document.createElement("select");
    select.id = "palette-theme-select";
    select.className = "form-control theme-select-dropdown";
    select.title = "Switch Color Palette & Theme";

    const current = getActivePalette();

    PALETTES.forEach(p => {
      const opt = document.createElement("option");
      opt.value = p.id;
      opt.textContent = p.name;
      if (p.id === current) opt.selected = true;
      select.appendChild(opt);
    });

    select.addEventListener("change", (e) => {
      setActivePalette(e.target.value);
    });

    // Insert as first action item in top header
    headerActions.insertBefore(select, headerActions.firstChild);
  }

  // Expose globally
  window.DataLensTheme = {
    getActivePalette,
    setActivePalette,
    PALETTES
  };

  // Run initial theme application immediately to prevent light/dark flicker
  initTheme();

  document.addEventListener("DOMContentLoaded", () => {
    injectThemeSelector();
  });
})();
