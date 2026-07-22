'use strict'
/**
 * @fileoverview Legacy translation compatibility surface.
 *
 * The retired browser-side DeepL integration was removed because translation
 * belongs to the rebuilt server-side LLM path. The legacy UI oracle must never
 * send text or credentials to an external translation service.
 */

const TargetLang = Object.freeze({
    BG: "BG",
    CS: "CS",
    DA: "DA",
    DE: "DE",
    EL: "EL",
    EN_GB: "EN-GB",
    EN_US: "EN-US",
    EN: "EN",
    ES: "ES",
    ET: "ET",
    FI: "FI",
    FR: "FR",
    HU: "HU",
    IT: "IT",
    JA: "JA",
    LT: "LT",
    LV: "LV",
    NL: "NL",
    PL: "PL",
    PT: "PT",
    RO: "RO",
    RU: "RU",
    SK: "SK",
    SL: "SL",
    SV: "SV",
    ZH: "ZH",
});

function translate(text, lang, onsuccess, onfailed) {
    void text;
    void lang;
    void onsuccess;
    const error = new Error('Legacy external translation integration was removed.');
    console.warn(error.message);
    if (onfailed) {
        onfailed(error);
    }
}
