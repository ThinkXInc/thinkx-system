'use strict'
/**
 * @fileoverview business/view_controllers/step_indicator.js
 * StepIndicator view component.
 * 
 * @author kaz@thinkxinc.com (Kazuki Otsuka)
 **/

/**
 * Step data object.
 * 
 * @param {string} title
 * @param {string} icon_image_src
 */
class Step {
    title
    icon_done_src
    icon_current_src
    icon_unreach_src

    constructor(title, icon_done_src, icon_current_src, icon_unreach_src) {
        this.title = title;
        this.icon_done_src = icon_done_src;
        this.icon_current_src = icon_current_src;
        this.icon_unreach_src = icon_unreach_src;
    }
}

/**
 * StepIndicator component class
 * @constructor
 * @classdesc `<div id={id} class=stepIndicator>` is necessary in HTML.
 * usage:
 * `<code>`
 *     stepIndicator = new StepIndicator(
 *         'SignupStepIndicator',
 *         [
 *          Step('Start', '/img/done.svg', '/img/current_0.svg', 'img/unreach_0.svg'),
 *          Step('Step 1', '/img/done.svg', '/img/current_1.svg', 'img/unreach_1.svg'),
 *          Step('Step 2', '/img/done.svg', '/img/current_2.svg', 'img/unreach_2.svg'),
 *          ]
 *      )
 * `</code>`
 * @param {string} _id - The DOM id where this view is inserted.
 * @param {Array of Step} steps - Step object array.
 * @param {Number} defaultIndex - The default index when loaded.
 */
class StepIndicator {
    __id__
    __steps__

    __stepIndex__

    constractor(id, steps, defaultIndex = 0) {
        this.__id__ = id;
        // setup page components
        if (steps.length == 0) {
            console.error(`${this.__id__} requires a list of steps.`)
        }
        // set elements
        this._setElements(steps);
        // set events
        this._setEventHandlers();
        // initialize values
        this.__stepIndex__ = defaultIndex
    }

    /**
     * DOM nodes as variables.
     */
    _setElements(steps) {
        this.$stepIndicator = document.getElementById(this.__id__);
        if (this.$stepIndicator == null) {
            console.warn(
                `<div id=${this.__id__} class=stepIndicator></div> is necessary in HTML.`);
        }
        // create pages
        let $steps = document.createElement('ul');
        $steps.classList.add('stepIndicatorSteps');
        steps.forEach((step, i) => {
            console.log(`${this.__id__} step ${i} title ${step.title}`);

            // create page DOM element
            let $step = document.createElement('li');
            $step.id = `${this.__id__}Step${i}`;
            $step.classList.add('stepIndicatorStep');
            $step.dataset.stepIndex = i;

            // TODO: set up html

            $steps.appendChild($step);
        });
        this.$stepIndicator.appendChild($steps);
    }

    /**
     * Set event handlers.
     */
    _setEventHandlers() {
        const _this = this;
    }
}

 