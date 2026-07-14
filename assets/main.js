const AH_LANGUAGES = {
  ar: { dir: "rtl", htmlLang: "ar", buttonText: "EN", switchLabel: "التبديل إلى الإنجليزية" },
  en: { dir: "ltr", htmlLang: "en", buttonText: "AR", switchLabel: "Switch to Arabic" }
};

function safeStorageGet(key) {
  try { return window.localStorage.getItem(key); } catch (error) { return null; }
}
function safeStorageSet(key, value) {
  try { window.localStorage.setItem(key, value); } catch (error) { /* Site remains usable. */ }
}
function setTranslatedAttributes(lang) {
  document.querySelectorAll("[data-aria-label-ar][data-aria-label-en]").forEach((element) => {
    const value = element.getAttribute(`data-aria-label-${lang}`);
    if (value) element.setAttribute("aria-label", value);
  });
  document.querySelectorAll("[data-label-ar][data-label-en]").forEach((element) => {
    const value = element.getAttribute(`data-label-${lang}`);
    if (value) {
      element.setAttribute("aria-label", value);
      element.setAttribute("title", value);
    }
  });
}
function updateMenuLabel(lang) {
  const menuButton = document.querySelector(".menu-btn");
  if (!menuButton) return;
  const open = menuButton.getAttribute("aria-expanded") === "true";
  const label = open
    ? (lang === "ar" ? "إغلاق قائمة التنقل" : "Close navigation menu")
    : (lang === "ar" ? "فتح قائمة التنقل" : "Open navigation menu");
  menuButton.setAttribute("aria-label", label);
  menuButton.setAttribute("title", label);
}
function setLanguage(lang) {
  const selected = AH_LANGUAGES[lang] ? lang : "ar";
  const config = AH_LANGUAGES[selected];
  document.documentElement.lang = config.htmlLang;
  document.documentElement.dir = config.dir;
  document.body.classList.remove("rtl", "ltr");
  document.body.classList.add(config.dir);
  document.body.dataset.language = selected;
  document.querySelectorAll("[data-ar][data-en]").forEach((element) => {
    const value = element.getAttribute(`data-${selected}`);
    if (value !== null) element.textContent = value;
  });
  document.querySelectorAll("[data-href-ar][data-href-en]").forEach((element) => {
    const value = element.getAttribute(`data-href-${selected}`);
    if (value) element.setAttribute("href", value);
  });
  setTranslatedAttributes(selected);
  document.querySelectorAll(".lang-btn").forEach((button) => {
    button.textContent = config.buttonText;
    button.setAttribute("aria-label", config.switchLabel);
    button.setAttribute("title", config.switchLabel);
  });
  updateMenuLabel(selected);
  const isHomePage = document.body.classList.contains("rm003");
  if (isHomePage) {
    document.title = selected === "ar"
      ? "أحمد حسونة | مستشار نظم العمليات والأعمال"
      : "Ahmed Hassouna | Operations & Business Systems Consultant";
  }

  safeStorageSet("ah-lang", selected);
  document.dispatchEvent(new CustomEvent("ah:languagechange", { detail: { lang: selected } }));
}

function setupMobileNavigation() {
  const menuButton = document.querySelector(".menu-btn");
  const navigation = document.querySelector(".nav-links");
  if (!menuButton || !navigation) return;
  const setOpen = (open, returnFocus = false) => {
    navigation.classList.toggle("open", open);
    menuButton.setAttribute("aria-expanded", String(open));
    const currentLang = document.documentElement.lang === "en" ? "en" : "ar";
    const label = open
      ? (currentLang === "ar" ? "إغلاق قائمة التنقل" : "Close navigation menu")
      : (currentLang === "ar" ? "فتح قائمة التنقل" : "Open navigation menu");
    menuButton.setAttribute("aria-label", label);
    menuButton.setAttribute("title", label);
    if (!open && returnFocus) menuButton.focus();
  };
  menuButton.addEventListener("click", () => setOpen(menuButton.getAttribute("aria-expanded") !== "true"));
  navigation.querySelectorAll("a").forEach((link) => link.addEventListener("click", () => setOpen(false)));
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && menuButton.getAttribute("aria-expanded") === "true") setOpen(false, true);
  });
  document.addEventListener("click", (event) => {
    if (menuButton.getAttribute("aria-expanded") === "true" && !navigation.contains(event.target) && !menuButton.contains(event.target)) setOpen(false);
  });
  window.addEventListener("resize", () => { if (window.innerWidth > 980) setOpen(false); });
}

function setupProjectCarousel(carousel) {
  const viewport = carousel.querySelector(".carousel-viewport");
  const track = carousel.querySelector(".carousel-track");
  const cards = Array.from(carousel.querySelectorAll(".project-card"));
  const prev = carousel.querySelector(".carousel-prev");
  const next = carousel.querySelector(".carousel-next");
  const dotsHost = carousel.querySelector(".carousel-dots");
  const status = carousel.querySelector(".carousel-status");
  if (!viewport || !track || !cards.length || !prev || !next || !dotsHost) return;

  let index = 0;
  let maxIndex = 0;
  let timer = null;
  let pointerStart = null;
  let paused = false;
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  const visibleCount = () => window.innerWidth >= 1100 ? 3 : (window.innerWidth >= 720 ? 2 : 1);
  const language = () => document.documentElement.lang === "en" ? "en" : "ar";

  function makeDots() {
    dotsHost.innerHTML = "";
    maxIndex = Math.max(0, cards.length - visibleCount());
    index = Math.min(index, maxIndex);
    for (let i = 0; i <= maxIndex; i += 1) {
      const dot = document.createElement("button");
      dot.className = "carousel-dot";
      dot.type = "button";
      dot.addEventListener("click", () => goTo(i, true));
      dotsHost.appendChild(dot);
    }
  }

  function updateLabels() {
    const lang = language();
    Array.from(dotsHost.children).forEach((dot, i) => {
      const label = lang === "ar" ? `الانتقال إلى موضع المشروع ${i + 1}` : `Go to project position ${i + 1}`;
      dot.setAttribute("aria-label", label);
      dot.setAttribute("title", label);
    });
    const shown = Math.min(cards.length, index + visibleCount());
    const message = lang === "ar"
      ? `عرض المشروعات من ${index + 1} إلى ${shown} من إجمالي ${cards.length}`
      : `Showing projects ${index + 1} to ${shown} of ${cards.length}`;
    status.textContent = message;
  }

  function updateDirectionControls() {
    const rtl = language() === "ar";
    prev.textContent = rtl ? "›" : "‹";
    next.textContent = rtl ? "‹" : "›";
  }

  function render(announce = false) {
    const first = cards[0];
    const gap = parseFloat(getComputedStyle(track).gap) || 0;
    const cardWidth = first.getBoundingClientRect().width;
    const directionSign = language() === "ar" ? 1 : -1;
    track.style.transform = `translate3d(${directionSign * index * (cardWidth + gap)}px,0,0)`;
    updateDirectionControls();
    Array.from(dotsHost.children).forEach((dot, i) => dot.setAttribute("aria-current", i === index ? "true" : "false"));
    prev.disabled = maxIndex === 0;
    next.disabled = maxIndex === 0;
    updateLabels();
    if (!announce) status.textContent = "";
  }

  function goTo(target, announce = false) {
    index = Math.max(0, Math.min(maxIndex, target));
    render(announce);
  }
  function goNext(userAction = false) { goTo(index >= maxIndex ? 0 : index + 1, userAction); }
  function goPrev(userAction = false) { goTo(index <= 0 ? maxIndex : index - 1, userAction); }

  function stopAutoplay() { if (timer) { window.clearInterval(timer); timer = null; } }
  function startAutoplay() {
    stopAutoplay();
    if (reduceMotion.matches || maxIndex === 0 || paused || document.hidden) return;
    timer = window.setInterval(() => goNext(false), 6500);
  }
  function pause() { paused = true; stopAutoplay(); }
  function resume() { paused = false; startAutoplay(); }

  prev.addEventListener("click", () => { goPrev(true); startAutoplay(); });
  next.addEventListener("click", () => { goNext(true); startAutoplay(); });
  carousel.addEventListener("mouseenter", pause);
  carousel.addEventListener("mouseleave", resume);
  carousel.addEventListener("focusin", pause);
  carousel.addEventListener("focusout", (event) => { if (!carousel.contains(event.relatedTarget)) resume(); });
  viewport.addEventListener("keydown", (event) => {
    const rtl = language() === "ar";
    if (event.key === "ArrowRight") { event.preventDefault(); rtl ? goPrev(true) : goNext(true); }
    if (event.key === "ArrowLeft") { event.preventDefault(); rtl ? goNext(true) : goPrev(true); }
  });
  viewport.addEventListener("pointerdown", (event) => { pointerStart = event.clientX; pause(); });
  viewport.addEventListener("pointerup", (event) => {
    if (pointerStart !== null) {
      const delta = event.clientX - pointerStart;
      if (Math.abs(delta) > 45) {
        const rtl = language() === "ar";
        if (rtl) delta > 0 ? goNext(true) : goPrev(true);
        else delta < 0 ? goNext(true) : goPrev(true);
      }
    }
    pointerStart = null;
    resume();
  });
  viewport.addEventListener("pointercancel", () => { pointerStart = null; resume(); });
  document.addEventListener("visibilitychange", () => document.hidden ? stopAutoplay() : startAutoplay());
  document.addEventListener("ah:languagechange", () => {
    index = 0;
    updateLabels();
    render(false);
    startAutoplay();
  });
  reduceMotion.addEventListener?.("change", startAutoplay);

  let resizeTimer = null;
  window.addEventListener("resize", () => {
    window.clearTimeout(resizeTimer);
    resizeTimer = window.setTimeout(() => { makeDots(); render(false); startAutoplay(); }, 120);
  });

  makeDots();
  render(false);
  startAutoplay();
}

document.addEventListener("DOMContentLoaded", () => {
  const saved = safeStorageGet("ah-lang");
  setLanguage(saved === "en" ? "en" : "ar");
  document.querySelectorAll(".lang-btn").forEach((button) => {
    button.addEventListener("click", () => {
      const current = document.documentElement.lang === "en" ? "en" : "ar";
      setLanguage(current === "ar" ? "en" : "ar");
    });
  });
  setupMobileNavigation();
  document.querySelectorAll("[data-carousel]").forEach(setupProjectCarousel);
});
