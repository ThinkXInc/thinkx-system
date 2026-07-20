'use strict'
/**
 * @fileoverview business/helpers/language.js
 * Language helper functions.
 * 
 * prerequisite:
 *   <script src=/js/data/countries.js></script>
 * 
 * language codes:
 *  ja
 *  en
 *  zh
 *  fr
 *  ru
 *  ar
 * 
 * @author kaz@thinkxinc.com (Kazuki Otsuka)
 */

/*
TODO: make funcations
const sublang = !(lang in ['ja', 'en', 'zh', 'fr', 'es', 'ru', 'ar']) ? 'en' : lang
const country_names = zip([countries[sublang], countries['numeric']])
const country_dials = zip([countries[sublang], countries['dial'], countries['numeric']])
const country_codes = countries['alpha2']
*/
 

const LANG_KEYS = ['ja', 'en', 'zh', 'fr', 'es', 'ru', 'ar']
const LANG_KEYS_AVAILABLE = ['ja', 'en', 'zh', 'fr', 'es', 'ru', 'ar']
const DEFAULT_LANG = 'en'  // TODO: from browser setting

/**
 * Returns names list in designated language.
 * 
 * @param {string} lang - eg. ja, en, .. 
 * @returns {Array} - eg. ['Afghanistan', 'Albania',..]
 */
function countryNames(lang) {
    // check availability
    const _lang = !(lang in LANG_KEYS_AVAILABLE) ? DEFAULT_LANG : lang
    // names
    const country_names = countriesISO3166[_lang]
    return country_names
}

/**
 * Returns ISO3166-1-numeric list.
 * 
 * @returns {Array} - eg. [4, 8,..]
 */
function countryNumerics() {
    // numerics
    const country_numerics = countriesISO3166['numeric']
    return country_numerics
}

/**
 * Returns dial country code list.
 * 
 * @param {string} lang - eg. ja, en, .. 
 * @returns {Array} - eg. ['93', '355', ..]
 */
function countryDials(lang, value='dial') {
    // check availability
    const _lang = !(lang in LANG_KEYS_AVAILABLE) ? DEFAULT_LANG : lang
    // dials
    const country_dials = countriesISO3166['dial']
    return country_dials
}

/**
 * Retuens ISO3166 alpha2 country code
 * 
 * @returns {Array} - eg. 
 */
function countryCodes() {
    // ISO3166 alpha2 country code
    const country_codes = countriesISO3166['alpha2']
    // alpha2 codes
    return country_codes
}

/**
 * Returns [names, dials, codes] data defined above.
 * 
 * @param {string} lang - eg. ja, en, .. 
 * @returns {object} countries
 *  - countries.names  # (name, numeric)
 *  - countries.dials  # (name, dial, numeric)
 *  - countries.codes  # (alpha2)
 */
function countriesFormData(lang) {
    const names = countryNames(lang);
    const numerics = countryNumerics();
    const dials = countryDials(lang);
    const codes = countryCodes();
    return { 
        names, numerics, dials, codes
    }
}