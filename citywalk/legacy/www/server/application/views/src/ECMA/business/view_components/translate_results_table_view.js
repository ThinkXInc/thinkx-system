'use strict'
/**
 * @fileoverview business/view_components/translate_results_table_view.js
 * TranslateResultsTableView component class.
 * 
 * TODO: inherit from TableView and TableViewCell class.
 * 
 * usage:
 * <code>
 *   var translateResultsTableView = new TranslateResultsTableView('translateResultsTableView');
 * </code>
 * 
 * @author kaz@thinkxinc.com (Kazuki Otsuka)
 */


/**
 * TranslateResultsTableViewCell State Enum.
 */
const TranslateResultsTableViewCellState = Object.freeze({
    onhide: 0,
    onshow: 1,
    onloading: 2,  // waiting speech synthesize
    onready: 3,  // speech is ready
    onediting: 4
});


/**
 * TranslateResult
 */
class TranslateResult {
    lang = null;
    text = null;
    manual = false;
    constructor(lang, text) {
        this.lang = lang;
        this.text = text;
    }
}


/**
 * ContentTalbeViewCell component class.
 * @constructor
 * @classdesc `<ul class=contentTableView id={id}></ul>` is necessary in HTML.
 * usage:
 * `<code>`
 *  var cell = new TranslateResultsTableViewCell(table_view_id, index_of_cell);  // insert to table automatically
 *  cell.content = content; // update html automatically
 * `</code>`
 * @param {string} id - The DOM id where this view is inserted.
 */
class TranslateResultsTableViewCell {
    __template__ = `\
    <li id=$id class=translateResultsTableViewCell>
        <div class=left>
           <span class=lang>$lang</span>
        </div>
        <div class=main>
            <span class=text>$text</span>
        </div>
        <div class=right>
            <span class=play>
            <!--
                <svg width="50px" height="50px" class="material-loader">
                    <circle cx="25" cy="25" r="20" class="material-loader__circle" />
                </svg>
                -->
            </span>
        </div>
    </li>
    `;
    // settings
    __id__ = null;
    __table_view_id__ = null;
    __index__ = null;
    __fade_out_duration__ = 2;
    __fade_in_duration__ = 2;

    // values
    _result = null;
    _lang = null;
    _text = null;
    _manual = null;
    _state = null;
    index = null;

    //constructor(table_view_id, index, content) {
    constructor(table_view_id, index) {
        // set veiw id
        this.__table_view_id__ = table_view_id;
        this.__index__ = index;
        this.__id__ = `${table_view_id}_${index}`
        // set elements
        this._setElements();
    }

    /**
     * result setter.
     */
    set result(result) {
        this._result = result;
        this._lang = result.lang;
        this._text = result.text;
        this._manual = result.manual;
        this._resetCell();
        this._setElements();
        this._setEventHandlers();
    }

    /**
     * result getter
     */
    get result() {return this._result}

    /**
     * state setter.
     */
    set state(state) {
        const previousState = this._state;
        this._state = state;
        switch (state) {
            case TranslateResultsTableViewCellState.onhide:
                console.log('translateResultsTableView state changed -> onhide');
                this.$cellView.classList.add('hide');
                setTimeout(()=>{
                    this.$cellView.style.display = 'none';
                }, 500);
                break
            case TranslateResultsTableViewCellState.onshow:
                console.log('translateResultsTableView state changed -> onshow');
                this.$cellView.style.display = 'flex';
                this.$cellView.classList.add('show');
                setTimeout(()=>{
                    this.state = TranslateResultsTableViewCellState.onloading;
                }, 500);
                break
            case TranslateResultsTableViewCellState.onloading:
                console.log(`translateResultsTableView state changed -> onloading`);
                break
          case TranslateResultsTableViewCellState.onready:
                console.log('translateResultsTableView state changed -> onready');
                break
            case TranslateResultsTableViewCellState.onediting:
                console.log('translateResultsTableView state changed -> onediting');
                break
        }
    }
 

    /**
     * DOM nodes as variables.
     */
    _setElements() {
        this.$tableView = document.getElementById(this.__table_view_id__);
        if (this.$tableView == null) {
            console.warn(`<ul id=${this.__table_view_id__}></ul> not found.`);
        }
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
    }


    /* private functions */

    /**
     * Reset cell content.
     */
    _resetCell() {
        ///this.state = TranslateResultsTableViewCellState.onhide;
        // set texts by this._content
        this.__template__ = this.__template__.replace('$id', this.__id__);
        this.__template__ = this.__template__.replace('$lang', this._lang);
        this.__template__ = this.__template__.replace('$text', this._text);
        // TODO: switch if manual is true
        this.$tableView.querySelector('.listContainer').innerHTML += this.__template__;
        // set elements
        this.$cellView = document.getElementById(this.__id__);
        if (this.$cellView == null) {
            console.warn(`<li id=${this.__id__} class=translateResultsTableViewCell></li> not found.`);
        }
        this.$lang = this.$cellView.querySelector('.lang');
        this.$text = this.$cellView.querySelector('.text');
        this.$play = this.$cellView.querySelector('.play');
        this.state = TranslateResultsTableViewCellState.onshow;

    }

    ///**
    // * Show cell
    // * @param {string} animationClass 
    // */
    //_show(animationClass='fadeInToBottom', interval=500) {
    //    console.log(`show function called in ${this.__id__}`);
    //    this.$translateResultsTableView.style.display = 'block';
    //    document.getElementById(this.__id__).classList.add(animationClass);
    //    setTimeout(()=>{
    //        this.state = TranslateResultsTableViewCellState.onloading;
    //    }, interval);
    //}

    ///**
    // * Hide cell
    // * @param {string} animationClass 
    // */
    //_hide(animationClass='fadeOutToLeft', interval=500) {
    //    console.log(`hide function called in ${this.__id__}`);
    //    document.getElementById(this.__id__).classList.add(animationClass);
    //    setTimeout(()=>{
    //        this.state = TranslateResultsTableViewCellState.onhide;
    //        this.$translateResultsTableView.style.display = 'none';
    //    }, interval);

    //}
}

/**
 * TranslateResultsTableView State Enum.
 */
const TranslateResultsTableViewState = Object.freeze({
    onshow: 1,
    onhide: 2,
    onselected: 3,
    onclosestart: 4,
    onclosecomplete: 5,
});

/**
 * TranslateResultsTableView component class.
 * @constructor
 * @classdesc `<ul class=translateResultsTableView id={id}></ul>` is necessary in HTML.
 * usage:
 * `<code>`
 *   // initialize table
 *   var translateResultsTableView = new TranslateResultsTableView('translateResultsTableView');
 *   translateResultsTableView.state = TranslateResultsTableViewState.onshow;
 *   
 *   // update cell
 *   let results = translateResultsTableView.results;
 *   results[lang] = new TranslateResult(lang, text, manual);
 *   translateResultsTableView.results = results; // automatically reconstruct cells.
 * `</code>`
 * @param {string} id - The DOM id where this view is replaced.
 */
class TranslateResultsTableView {
    __id__ = null;
    __innter_template__ = `
    <ul class=listContainer></ul>
    <div class=footer>
        <span class=translatedby>translate by</span><img class=DeepLLogo src=/img/parts/deepl64.png srcset="/img/parts/deepl128.png 2x" />
    </div>
    `
    $listContainer;

    __max_default_cell_number__ = 20;
    __adding_cell_number__ = 20;

    _state = null;
    _cells = []; // list of TranslateResultsTableViewCell
    _selectedIndex = null;
    _results = {};

    constructor(id) {
        // set veiw id
        this.__id__ = id;
        // initialize view elements
        this._setElements();
        // initialize layout
        this._initLayout();
    }

    /**
     * results setter.
     */
    set results(results) {
       this._results = results;
       this._resetCells();
       console.log(`${results.length} cells successfully set.`);
    }

    /**
     * results getter.
     */
    get results() {return this._results;}

    /**
     * state setter.
     */
    set state(state) {
        const previousState = this._state;
        this._state = state;
        switch (state) {
            case TranslateResultsTableViewState.onhide:
                console.log('translateResultsTableView state changed -> onhide');
                this.$translateResultsTableView.style.display = 'none';
                this._hideFooter();
                break
            case TranslateResultsTableViewState.onshow:
                console.log('translateResultsTableView state changed -> onshow');
                this.$translateResultsTableView.style.display = 'flex';
                break
           case TranslateResultsTableViewState.onselected:
                console.log('translateResultsTableView state changed -> onselected');
                break
            case TranslateResultsTableViewState.onclosestart:
                console.log('translateResultsTableView state changed -> onclosestart');
                this._close(shouldAnimateCells=true);
                break
            case TranslateResultsTableViewState.onclosecomplete:
                console.log(`translateResultsTableView state changed  ${TranslateResultsTableViewState[previousState]}-> onclosecomplete`);
                this.$translateResultsTableView.style.display = 'none';
                if (previousState != state) {
                    this.$translateResultsTableView.dispatchEvent(
                        new CustomEvent('onclosecomplete', {detail: {previousState: previousState, selected: null}}));
                }
        }
    }

    /**
     * DOM nodes as variables.
     */
    _setElements() {
        this.$translateResultsTableView = document.getElementById(this.__id__);
        if (this.$translateResultsTableView == null) {
            console.warn(
                `<section id=${this.__id__} class=translateResultsTableView></section> is necessary in HTML.`);
        }
        this.$translateResultsTableView.innerHTML = this.__innter_template__;
        this.$listContainer = this.$translateResultsTableView.querySelector('.listContainer');
        if (this.$listContainer == null) {
            console.warn(
                `<ul class=listContainer></ul> is necessary in HTML.`);
        }
        this.$footer = this.$translateResultsTableView.querySelector('.footer');
        if (this.$footer == null) {
            console.warn(
                `<div class=footer></div> is necessary in HTML.`);
        }
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
        this._cells.forEach((cell, index) => {
            console.log(`set event for ${cell.__id__}`);
            document.getElementById(cell.__id__).addEventListener('click', e => {
                console.log(`cell ${cell.__id__} clicked`)
                _this._selectedIndex = cell.__index__;
                _this.state = TranslateResultsTableViewState.onselected;
            });
            document.getElementById(cell.__id__).addEventListener('mouseover', e => {
                _this.$translateResultsTableView.dispatchEvent(
                    new CustomEvent(
                        'onmouseover', {detail: {cellId: cell.__id__, index: cell.__index__}}
                    ));
            });
            document.getElementById(cell.__id__).addEventListener('mouseout', e => {
                _this.$translateResultsTableView.dispatchEvent(
                    new CustomEvent(
                        'onmouseout', {detail: {cellId: cell.__id__, index: cell.__index__}}
                    ));
            });
        })
    }

    /* private functions */

    /**
     * Reset table view cells by the latest cells data.
     */
    _resetCells() {
        // set table view cells from contents
        this.$listContainer.innerHTML = '';
        this._cells = Object.keys(this._results).map((key, i) => {
            var cell = new TranslateResultsTableViewCell(this.__id__, i);
            const result = this._results[key];
            cell.result = result;
            return cell;
        })
        console.log(`translateResultsTableView was reset by ${this._cells.length} cell`)
        if (this._cells.length > 0) {
            this._showFooter();
        } else {
            this._hideFooter();
        }
        this._setEventHandlers();
    }

    /**
     * show footer
     */
    _showFooter() {
        this.$footer.style.display = 'flex';
    }

    /**
     * hide footer
     */
    _hideFooter() {
        this.$footer.style.display = 'none';
    }

    /**
    * To show this view component.
    */
    _show() {
    }

    /**
    * Close this view component.
    */
    _close(shouldAnimateCells=true) {
        console.log(`${this.__id__} close function called. (previousState ${this.state})`);
        var _this = this;
        const interval = 50;
        if (shouldAnimateCells) {
            this._cells.forEach(cell =>{
                setTimeout(()=>{cell.hide()}, cell.__index__*interval);
            })
        }
        this.$translateResultsTableView.animate({
            opacity: 0
        }, interval*this._cells.length, 'easeInSine').finished.then(()=> {
            _this.state = TranslateResultsTableViewState.onclosecomplete;
        })
    }
}
