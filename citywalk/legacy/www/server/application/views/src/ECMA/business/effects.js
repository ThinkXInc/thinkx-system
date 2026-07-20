'use strict'
/**
 * @fileoverview business/effects.js
 * This code doesn't effect to any functionality of the app.
 * Just adding visual effects.
 * @author kaz@thinkxinc.com (Kazuki Otsuka)
 */


/**
 * Apply cursor ripple effect to a DOM element.
 * 
 * usage:
 * `<code>`
 *  applyCursorRippleEffect($someButton);
 * `</code>`
 * 
 * *`.ripple` and `.rippleEffect` is required in css.
 */
function applyCursorRippleEffect($elem) {
    console.log(`apply cursor ripple effect to ${$elem}`);
    $elem.onclick = () => cursorRippleEffect(event, $elem); 
    $elem.style.overflow = 'hidden';
    function cursorRippleEffect(e, $elem) {
        console.log(`click (${e.clientX},${e.clientY}) detected in ${$elem.className}`);
        const $ripple = document.createElement("div");

        $ripple.className = "ripple";
        $elem.appendChild($ripple);

        const left = e.clientX - $elem.offsetLeft;
        const top = e.clientY - $elem.offsetTop;
        //console.log(`ripple center (${left}, ${top})`)
        $ripple.style.left = `${left}px`;
        $ripple.style.top = `${top}px`; 

        $ripple.classList.add('rippleEffect');
        $ripple.onanimationend = () => $elem.removeChild($ripple);
    }
}


const GradientPattern = Object.freeze({
    // generate => https://cssgradient.io/
    rainbow: 'linear-gradient(90deg,#ffd33d,#ea4aaa 17%,#b34bff 34%,#01feff 51%,#ffd33d 68%,#ea4aaa 85%,#b34bff)',
    anslim: 'linear-gradient(90deg, rgba(60,128,167,1) 0%, rgba(158,188,200,1) 14%, rgba(255,255,255,1) 30%, rgba(167,47,178,1) 51%, rgba(158,188,200,1) 78%, rgba(60,128,167,1) 100%)',
    smilan: 'linear-gradient(90deg, rgba(60,128,167,1) 0%, rgba(158,188,200,1) 14%, rgba(203,194,49,1) 30%, rgba(167,47,178,1) 51%, rgba(158,188,200,1) 78%, rgba(60,128,167,1) 100%)',

    pear: 'linear-gradient(90deg, rgba(34,193,195,1) 0%, rgba(253,187,45,1) 100%)',
    scash: 'linear-gradient(90deg, rgba(158,188,200,1) 0%, rgba(34,193,195,1) 51%, rgba(203,194,49,1) 100%)',
    paradice: 'linear-gradient(90deg, rgba(158,188,200,1) 0%, rgba(167,47,178,1) 51%, rgba(203,194,49,1) 100%)',
    villea: 'linear-gradient(90deg, rgba(158,188,200,1) 0%, rgba(60,128,167,1) 51%, rgba(203,194,49,1) 100%)',
    bougen: 'linear-gradient(90deg, rgba(158,188,200,1) 0%, rgba(167,47,178,1) 51%, rgba(60,128,167,1) 100%)',
    bougen2: 'linear-gradient(90deg, rgba(60,128,167,1) 0%, rgba(158,188,200,1) 14%, rgba(167,47,178,1) 51%',
    milsan: 'linear-gradient(90deg, rgba(60,128,167,1) 0%, rgba(158,188,200,1) 14%, rgba(203,194,49,1) 30%, rgba(167,47,178,1) 51%, rgba(60,128,167,1) 100%)',
    casabranca: 'linear-gradient(90deg, rgba(131,58,180,1) 0%, rgba(253,29,29,1) 50%, rgba(252,176,69,1) 100%)',
    ocean: 'linear-gradient(90deg, rgba(29,138,147,1) 0%, rgba(9,79,121,1) 35%, rgba(0,212,255,1) 100%)', 
    marine: 'linear-gradient(90deg, rgba(122,239,255,1) 0%, rgba(36,110,198,1) 35%, rgba(0,212,255,1) 100%)',
    cooler: 'linear-gradient(90deg, rgba(128,246,255,1) 0%, rgba(57,162,204,1) 35%, rgba(164,251,255,1) 100%)',
})

function toggleGradientLoader($elem, isLoading=true, pattern=GradientPattern.smilan) {

    // define and add @keyframe animation
    var style = document.createElement('style');
    var keyFrames = '\
    @keyframes gradientLoadingBar {\
        0% {\
        background-position: 100%;\
        }\
        100% {\
        background-position: 0;\
        }\
    }\
    ';
    style.innerHTML = keyFrames;
    document.head.appendChild(style);

    // create bar element
    let $bar = document.createElement('span');
    $bar.id = $elem.id + '_bar';
    $bar.style.display = 'block';
    $bar.style.height = '100%';
    $bar.style.background = pattern;
    $bar.style.backgroundSize = '300% 100%';
    $bar.style.animation = 'gradientLoadingBar 2s linear infinite';
    if (isLoading) {
        $elem.appendChild($bar);
    } else {
        document.getElementById($bar.id).remove();
    }
}