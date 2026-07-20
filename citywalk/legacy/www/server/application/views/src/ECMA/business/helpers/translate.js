'use strict'
/**
 * @fileoverview business/helpers/translate.js
 * DeepL API helper class.
 * 
 * usage:
 * <code>
 * </code>
 * 
 * @author kaz@thinkxinc.com (Kazuki Otsuka)
 */


/**
 * DeepL language Enum.
 */
const TargetLang = Object.freeze({
    BG: "BG", //  - Bulgarian
    CS: "CS", //  - Czech
    DA: "DA", //  - Danish
    DE: "DE", //  - German
    EL: "EL", //  - Greek
    EN_GB: "EN-GB", //  - English (British)
    EN_US: "EN-US", //  - English (American)
    EN: "EN", //  - English (unspecified variant for backward compatibility; please select EN-GB or EN-US instead)
    ES: "ES", //  - Spanish
    ET: "ET", //  - Estonian
    FI: "FI", //  // Finnish
    FR: "FR", // French
    HU: "HU", // Hungarian
    IT: "IT", // Italian
    JA: "JA", // Japanese
    LT: "LT", // Lithuanian
    LV: "LV", // Latvian
    NL: "NL", // Dutch
    PL: "PL", // Polish
    PT: "PT", // Portuguese (all Portuguese varieties excluding Brazilian Portuguese)
    PT: "PT", // Portuguese (Brazilian)
    PT: "PT", // Portuguese (unspecified variant for backward compatibility; please select PT//PT or PT//BR instead)
    RO: "RO", // Romanian
    RU: "RU", // Russian
    SK: "SK", // Slovak
    SL: "SL", // Slovenian
    SV: "SV", // Swedish
    ZH: "ZH", // Chinese
});

/**
 * Request Translation.
 * @param {string} text 
 * @param {DeepLLang} lang 
 * @param {callback function} onsuccess - called on seccess.
 * @param {callback function} onfailed - called on failed.
 */
function translate(text, lang, onsuccess, onfailed) {
    fetch(
        `https://api-free.deepl.com/v2/translate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            'auth_key': '44329c0b-1a4a-ca05-3804-0ff35cd2e059:fx',
            'text': text,
            'target_lang': lang,
        })
    })
    .then(response => response.json())
    .then(data => {
        console.info('fetch success:', data);
        onsuccess(data);
    })
    .catch((error) => {
        console.error('fetch error:', error);
        onfailed(error);
    })
}