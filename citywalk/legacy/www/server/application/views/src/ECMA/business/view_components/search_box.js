'use strict'
/**
 * @fileoverview business/view_components/search_box.js
 * Searchbox view component class.
 * 
 * usage:
 * <code>
 * </code>
 * 
 * @author kaz@thinkxinc.com (Kazuki Otsuka)
 */


/**
 * Searchbox State Enum.
 */
const SearchState = Object.freeze({
    onhide: 0,
    onshow: 1,
    onfocus: 2,
    onediting: 3,
    onsearching: 4,
    ondisplaycandidates: 5,
});


/**
 * SearchBox component class.
 * @constructor
 * @classdesc 
 * usage:
 * `<code>`
 * `</code>`
 * @param {string} id - The DOM id where this view is set.
 */
class SearchBox {
    __template__ = `
    `
    __id__ = null;

    _state = null;

    // data
    _text = null;

    constructor(id) {
        // set veiw id
        this.__id__ = id;
        // initialize view elements
        this._setElements();
        // initialize layout
        this._initLayout();
   }

    /**
     * text setter.
     */
    set text(text) {
        this._text = text;
        console.log(`text updated: ${text}`);
        // dispatch event
        const event = new CustomEvent('textupdated', {detail: {new: text,}});
        this.$searchBox.dispatchEvent(event);
    }

    /**
     * state setter.
     */
    set state(state) {
        this._state = state;
        switch (state) {
            case SearchBoxState.onhide:
                console.log(`SearchBox ${this.__id__} state changed -> onhide`);
                break
        }
    }

    /**
     * DOM nodes as variables.
     */
    _setElements() {
        this.$searchBox = document.getElementById(this.__id__);
        if (this.$searchBox == null) {
            console.warn(
                `< id=${this.__id__} class=searchBox></> is necessary in HTML.`);
        }
        // TODO: other elements
 
    }

    /**
     * Initialize the layout for display.
     */
    _initLayout() {
    }

    /**
     * Set event handlers.
     */
    _setEventHandlers() {
        const _this = this;
    }

    /* private functions */

    /* public functions */

}

