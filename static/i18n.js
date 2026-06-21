// Übersetzungen DE / AR
// Frontend-Texte. Speisennamen + Bildausgabe bleiben IMMER Deutsch.
// Hinweis: bewusst KEINE Emojis / Mini-Icons in der UI.

const TRANSLATIONS = {
  de: {
    today:          "Heute",
    tomorrow:       "Morgen",
    menu:           "Menü zusammenstellen",
    preview:        "Live-Vorschau",
    save:           "Speichern",
    saving:         "Speichere ...",
    saved:          "Gespeichert",
    history:        "Verlauf nach Wochentag",
    history_hint:   "Tag wählen · Menü anklicken übernimmt die Gerichte (Datum bleibt)",
    history_empty_wd: "Keine gespeicherten Menüs für {weekday}.",
    menu_loaded:    "Gerichte übernommen (Datum bleibt)",
    wd_abbr:        ["Mo","Di","Mi","Do","Fr","Sa","So"],
    wd_full:        ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"],
    optional:       "(optional)",
    ready:          "Bereit.",

    cat_suppe:       "Suppe",
    cat_haupt:       "Hauptgericht",
    cat_pasta:       "Pasta",
    cat_beilagen:    "Beilage",
    cat_salate:      "Salate",
    cat_partypfanne: "Partypfanne",
    cat_dessert:     "Dessert",

    err_render:    "Fehler beim Rendern",
    err_save:      "Fehler beim Speichern",
  },

  ar: {
    today:          "اليوم",
    tomorrow:       "غداً",
    menu:           "تجميع القائمة",
    preview:        "معاينة مباشرة",
    save:           "حفظ",
    saving:         "جارٍ الحفظ ...",
    saved:          "تم الحفظ",
    history:        "السجل حسب اليوم",
    history_hint:   "اختر اليوم · اضغط على القائمة لنقل الأطباق (يبقى التاريخ)",
    history_empty_wd: "لا توجد قوائم محفوظة لـ {weekday}.",
    menu_loaded:    "تم نقل الأطباق (يبقى التاريخ)",
    wd_abbr:        ["اث","ثل","أر","خم","جم","سب","أح"],
    wd_full:        ["الإثنين","الثلاثاء","الأربعاء","الخميس","الجمعة","السبت","الأحد"],
    optional:       "(اختياري)",
    ready:          "جاهز.",

    cat_suppe:       "حساء",
    cat_haupt:       "طبق رئيسي",
    cat_pasta:       "معكرونة",
    cat_beilagen:    "طبق جانبي",
    cat_salate:      "سلطات",
    cat_partypfanne: "مقلاة الحفلة",
    cat_dessert:     "حلوى",

    err_render:    "خطأ في العرض",
    err_save:      "خطأ في الحفظ",
  },
};

const I18N = {
  current: "de",

  t(key) {
    return TRANSLATIONS[this.current]?.[key] ?? key;
  },

  apply() {
    // Alle Elemente mit data-i18n bekommen den passenden Text
    document.querySelectorAll("[data-i18n]").forEach(el => {
      const key = el.getAttribute("data-i18n");
      el.textContent = this.t(key);
    });
    // Placeholder-Übersetzungen
    document.querySelectorAll("[data-i18n-ph]").forEach(el => {
      const key = el.getAttribute("data-i18n-ph");
      el.setAttribute("placeholder", this.t(key));
    });
    // <html lang> setzen
    document.documentElement.setAttribute("lang", this.current);
  },

  setLang(lang) {
    if (!TRANSLATIONS[lang]) return;
    this.current = lang;
    localStorage.setItem("buffet.lang", lang);

    document.querySelectorAll(".lang-btn").forEach(btn => {
      btn.classList.toggle("active", btn.dataset.lang === lang);
    });
    this.apply();

    // Slot-Labels (haben numerierte Suffixe) müssen neu generiert werden
    if (window.renderSlots) window.renderSlots();
    // Wochentag-Verlauf neu aufbauen (Abkürzungen/Texte sind übersetzt)
    if (window.onLanguageChanged) window.onLanguageChanged();
  },

  init() {
    const saved = localStorage.getItem("buffet.lang");
    if (saved && TRANSLATIONS[saved]) this.current = saved;
    document.querySelectorAll(".lang-btn").forEach(btn => {
      btn.addEventListener("click", () => this.setLang(btn.dataset.lang));
    });
    this.apply();
  },
};
