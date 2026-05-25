// Übersetzungen DE / AR
// Frontend-Texte. Speisennamen + Bildausgabe bleiben IMMER Deutsch.

const TRANSLATIONS = {
  de: {
    date:           "📅 Datum",
    today:          "Heute",
    tomorrow:       "Morgen",
    ki_input:       "✏ KI-Freitext (optional)",
    ki_placeholder: "Beispiel: Tomatensuppe, Schnitzel, Bratkartoffeln, Spaghetti Bolognese ...",
    ki_analyze:     "🤖 KI-Analyse starten",
    ki_running:     "⏳ KI analysiert ...",
    menu:           "📋 Menü zusammenstellen",
    preview:        "👁 Live-Vorschau",
    save:           "🖼 Speichern",
    saving:         "⏳ Speichere ...",
    saved:          "✓ Gespeichert",
    history:        "🕐 Letzte 7 Tage",
    optional:       "(optional)",
    ready:          "Bereit.",

    cat_suppe:       "🥣 Suppe",
    cat_haupt:       "🍖 Hauptgericht",
    cat_pasta:       "🍝 Pasta",
    cat_beilagen:    "🥦 Beilage",
    cat_salate:      "🥗 Salate",
    cat_partypfanne: "🍳 Partypfanne",
    cat_dessert:     "🍮 Dessert",

    err_render:    "Fehler beim Rendern",
    err_save:      "Fehler beim Speichern",
    err_ki:        "KI-Fehler",
    err_ki_off:    "KI nicht verfügbar (API-Key fehlt)",
    err_no_text:   "Bitte erst Speisen eingeben",
  },

  ar: {
    date:           "📅 التاريخ",
    today:          "اليوم",
    tomorrow:       "غداً",
    ki_input:       "✏ نص حر (ذكاء اصطناعي)",
    ki_placeholder: "مثال: حساء طماطم، شنيتزل، بطاطس مقلية، سباغيتي بولونيز ...",
    ki_analyze:     "🤖 بدء التحليل بالذكاء الاصطناعي",
    ki_running:     "⏳ جارٍ التحليل ...",
    menu:           "📋 تجميع القائمة",
    preview:        "👁 معاينة مباشرة",
    save:           "🖼 حفظ",
    saving:         "⏳ جارٍ الحفظ ...",
    saved:          "✓ تم الحفظ",
    history:        "🕐 آخر 7 أيام",
    optional:       "(اختياري)",
    ready:          "جاهز.",

    cat_suppe:       "🥣 حساء",
    cat_haupt:       "🍖 طبق رئيسي",
    cat_pasta:       "🍝 معكرونة",
    cat_beilagen:    "🥦 طبق جانبي",
    cat_salate:      "🥗 سلطات",
    cat_partypfanne: "🍳 مقلاة الحفلة",
    cat_dessert:     "🍮 حلوى",

    err_render:    "خطأ في العرض",
    err_save:      "خطأ في الحفظ",
    err_ki:        "خطأ في الذكاء الاصطناعي",
    err_ki_off:    "الذكاء الاصطناعي غير متوفر (مفتاح API مفقود)",
    err_no_text:   "يرجى إدخال الأطباق أولاً",
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
