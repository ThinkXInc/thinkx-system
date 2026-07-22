'use strict'
/**
 * Test-only reproduction of the completed translation state visible in the
 * owner-provided production demo. No network request or credential is used.
 */

const TargetLang = Object.freeze({
    BG: "BG", CS: "CS", DA: "DA", DE: "DE", EL: "EL",
    EN_GB: "EN-GB", EN_US: "EN-US", EN: "EN", ES: "ES", ET: "ET",
    FI: "FI", FR: "FR", HU: "HU", IT: "IT", JA: "JA", LT: "LT",
    LV: "LV", NL: "NL", PL: "PL", PT: "PT", RO: "RO", RU: "RU",
    SK: "SK", SL: "SL", SV: "SV", ZH: "ZH",
});

const CITYWALK_TRANSLATION_FIXTURE = Object.freeze({
    JA: "この地下にフランスとの国境地帯にまたがり円形に位置するぜん",
    EN: "In this basement, there is a circular shape that spans the border area with France.",
    ES: "En el sótano de este edificio hay un círculo que abarca la zona de la frontera francesa.",
    ZH: "在这座建筑的地下室，有一个跨越法国边境地区的圆圈。",
    SV: "I byggnadens källare finns en cirkel som sträcker sig över det franska gränsområdet.",
    FR: "C'est le sous-sol de la zone frontalière française.",
    IT: "Nel seminterrato di questo edificio c'è un cerchio che attraversa la zona del confine francese.",
    HU: "Ennek az épületnek az alagsorában van egy kör, amely átível a francia határvidéken.",
    PT: "Na cave deste edifício há um círculo que atravessa a zona da fronteira francesa.",
    NL: "In de kelder van dit gebouw is een cirkel die het Franse grensgebied overspant.",
    RU: "В подвале этого здания находится круг, который охватывает пограничную зону Франции.",
});

const CITYWALK_TRANSLATION_ORDER = Object.freeze([
    "JA", "EN", "ES", "ZH", "SV", "FR", "IT", "HU", "PT", "NL", "RU",
]);

function translate(text, lang, onsuccess, onfailed) {
    void text;
    const translatedText = CITYWALK_TRANSLATION_FIXTURE[lang];
    if (!translatedText) {
        if (onfailed) onfailed(new Error(`No legacy translation fixture for ${lang}`));
        return;
    }
    const delay = CITYWALK_TRANSLATION_ORDER.indexOf(lang) * 120;
    window.setTimeout(() => {
        onsuccess({translations: [{detected_source_language: "JA", text: translatedText}]});
    }, delay);
}
