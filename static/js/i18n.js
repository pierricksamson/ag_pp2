(function () {
  "use strict";

  const SUPPORTED_LANGS = ["fr", "en"];
  const DEFAULT_LANG = "fr";
  const STORAGE_KEY = "ademi_lang";
  const NAMESPACES = [
    "common",
    "academics",
    "attendance",
    "drive",
    "infirmerie",
    "messaging",
    "schedule",
    "users",
    "vie_scolaire",
  ]; // un fichier JSON par partie/app, chargé globalement (fichiers courts)

  const STATIC_BASE = (document.currentScript && document.currentScript.dataset.staticBase) || "/static/";

  // Cache en mémoire des dictionnaires déjà résolus (par langue), pour ne
  // jamais recharger deux fois le même fichier JSON pendant la session
  // (ex : aller-retour fr -> en -> fr).
  const dictCache = Object.create(null);

  function getStoredLang() {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored && SUPPORTED_LANGS.includes(stored)) return stored;
    const nav = (navigator.language || DEFAULT_LANG).slice(0, 2);
    return SUPPORTED_LANGS.includes(nav) ? nav : DEFAULT_LANG;
  }

  function setStoredLang(lang) {
    window.localStorage.setItem(STORAGE_KEY, lang);
  }

  async function loadNamespace(lang, ns) {
    const url = `${STATIC_BASE}i18n/${lang}/${ns}.json`;
    const res = await fetch(url, { cache: "force-cache" });
    if (!res.ok) throw new Error(`i18n: impossible de charger ${url}`);
    return res.json();
  }

  async function loadDictionary(lang) {
    // Les namespaces sont indépendants : on les charge tous en parallèle
    // plutôt qu'en séquence, ce qui divise le temps de chargement par le
    // nombre de fichiers (au lieu de les attendre un par un).
    const results = await Promise.all(NAMESPACES.map((ns) => loadNamespace(lang, ns)));
    const dict = {};
    NAMESPACES.forEach((ns, i) => {
      for (const [key, value] of Object.entries(results[i])) {
        // "common" garde ses clés telles quelles (ex: "nav.dashboard"),
        // les autres namespaces sont préfixés pour matcher data-i18n="ns.key"
        // et éviter toute collision entre fichiers (ex: "Retards" traduit
        // différemment selon la page).
        const finalKey = ns === "common" ? key : `${ns}.${key}`;
        dict[finalKey] = value;
      }
    });
    return dict;
  }

  async function getDictionary(lang) {
    if (!dictCache[lang]) dictCache[lang] = loadDictionary(lang);
    return dictCache[lang];
  }

  function applyTranslations(dict) {
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      if (dict[key] !== undefined) el.textContent = dict[key];
    });
    document.querySelectorAll("[data-i18n-attr]").forEach((el) => {
      // format: data-i18n-attr="placeholder:key1|title:key2"
      el.getAttribute("data-i18n-attr")
        .split("|")
        .forEach((pair) => {
          const [attr, key] = pair.split(":");
          if (attr && key && dict[key] !== undefined) el.setAttribute(attr, dict[key]);
        });
    });
    document.querySelectorAll("[data-lang-flag]").forEach((el) => {
      el.classList.toggle("hidden", el.getAttribute("data-lang-flag") !== window.AdemiI18n.currentLang);
    });
  }

  async function setLang(lang) {
    if (!SUPPORTED_LANGS.includes(lang)) return;
    setStoredLang(lang);
    window.AdemiI18n.currentLang = lang;
    document.documentElement.setAttribute("lang", lang);
    const dict = await getDictionary(lang);
    applyTranslations(dict);
    document.dispatchEvent(new CustomEvent("ademi:lang-changed", { detail: { lang, dict } }));
  }

  window.AdemiI18n = {
    supportedLangs: SUPPORTED_LANGS,
    currentLang: getStoredLang(),
    setLang,
  };

  // Le contenu textuel n'existe plus dans le HTML : tout passe par le
  // dictionnaire i18n, y compris pour le français par défaut. On lance le
  // fetch (parallélisé) dès que possible, sans attendre DOMContentLoaded,
  // pour réduire le délai avant l'affichage du texte.
  function boot() {
    setLang(window.AdemiI18n.currentLang);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
