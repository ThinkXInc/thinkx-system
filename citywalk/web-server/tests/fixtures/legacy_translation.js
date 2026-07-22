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

const CITYWALK_TRANSLATION_FIXTURE_SHORT = Object.freeze({
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

const CITYWALK_TRANSLATION_FIXTURE_LONG = Object.freeze({
    JA: "この地下にフランスとの国境地帯にまたがり円形に位置する全長27kmの大型ハドロン衝突型加速器が埋め込まれている。",
    EN: "Embedded in this basement is the 27km-long Large Hadron Collider, which is located in a circle spanning the border region with France.",
    ES: "El Gran Colisionador de Hadrones, de 27 km de longitud, a caballo entre la frontera francesa y situado en un círculo, está incrustado bajo tierra.",
    ZH: "大型强子对撞机长27公里，横跨法国边境，位于一个圆圈中，被嵌入地下。",
    SV: "Den 27 km långa Large Hadron Collider, som ligger i en cirkel runt den franska gränsen, är inbäddad under jorden.",
    FR: "Le Grand collisionneur de hadrons, long de 27 km, à cheval sur la frontière française et situé en cercle, est enfoui sous terre.",
    IT: "Un grande impattatore di adroni, lungo 27 km, si trova sottoterra in una formazione circolare a cavallo del confine francese.",
    HU: "A Nagy Hadronütköztető 27 km hosszú, a francia határon átívelő, kör alakban elhelyezkedő, a föld alá ágyazott.",
    PT: "O Grande Colisor de Hadron, com 27 km de comprimento, que atravessa a fronteira francesa e está situado num círculo, está embutido no subsolo.",
    NL: "De 27 km lange Large Hadron Collider, die de Franse grens overschrijdt en in een cirkel ligt, is ondergronds ingebed.",
    RU: "Большой адронный коллайдер длиной 27 км, расположенный по кругу вдоль границы с Францией, встроен под землю.",
});

const CITYWALK_TRANSLATION_ORDER = Object.freeze([
    "JA", "EN", "ES", "ZH", "SV", "FR", "IT", "HU", "PT", "NL", "RU",
]);

function translate(text, lang, onsuccess, onfailed) {
    const fixture = text.includes('27km')
        ? CITYWALK_TRANSLATION_FIXTURE_LONG
        : CITYWALK_TRANSLATION_FIXTURE_SHORT;
    const translatedText = fixture[lang];
    if (!translatedText) {
        if (onfailed) onfailed(new Error(`No legacy translation fixture for ${lang}`));
        return;
    }
    const delay = CITYWALK_TRANSLATION_ORDER.indexOf(lang) * 120;
    window.setTimeout(() => {
        onsuccess({translations: [{detected_source_language: "JA", text: translatedText}]});
    }, delay);
}
