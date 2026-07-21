'use strict'
/**
 * @fileoverview business/view_components/content_table_view.js
 * ContentTableView component class.
 * 
 * usage:
 * <code>
 *   var contentTableView = new ContentTableView('contentTableView');
 *   contentTableView.contents = contents; // automatically reconstruct cells.
 * </code>
 * 
 * @author kaz@thinkxinc.com (Kazuki Otsuka)
 */


/**
 * ContentTalbeViewCell component class.
 * @constructor
 * @classdesc `<ul class=contentTableView id={id}></ul>` is necessary in HTML.
 * usage:
 * `<code>`
 *  var cell = new ContentTableViewCell(table_view_id, index_of_cell);  // insert to table automatically
 *  cell.content = content; // update html automatically
 * `</code>`
 * @param {string} id - The DOM id where this view is inserted.
 */
class ContentTableViewCell {
    __template__ = `\
    <li id=$id class=contentTableViewCell>
        <div class="header cf">
           <span class=label>$label</span>
           <span class=title>$title</span>
        </div>
        <div class="body cf">
            <span class=text>$text</span>
        </div>
        <div class="footer cf">
            <span class=updated>$updated</span>
            <span class=edited>
                <span class=by>by</span><span class=author>$author</span>
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
    _content = {};
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
     * content setter.
     */
    set content(content) {
       this._content = content;
       this._resetCell();
       this._setElements();
       this._setEventHandlers();
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
        // set texts by this._content
        this.__template__ = this.__template__.replace('$id', this.__id__);
        this.__template__ = this.__template__.replace('$label', this._content.label);
        this.__template__ = this.__template__.replace('$title', this._content.title);
        this.__template__ = this.__template__.replace('$text', this._content.text);
        this.__template__ = this.__template__.replace('$updated', this._content.updated);
        this.__template__ = this.__template__.replace('$author', this._content.author);
        this.$tableView.innerHTML += this.__template__;
        this.$cellView = document.getElementById(this.__id__);
        if (this.$cellView == null) {
            console.warn(`<li id=${this.__id__} class=contentTableViewCell></li> not found.`);
        }
    }

    /* public functions */
    hide() {
        console.log(`hide function called in ${this.__id__}`);
        document.getElementById(this.__id__).classList.add('fadeOutToLeft');
    }
}

/**
 * ContentTableView State Enum.
 */
const ContentTableViewState = Object.freeze({
    onloading: 1,
    onshow: 2,
    onhide: 3,
    onselected: 4,
    onclosestart: 5,
    onclosecomplete: 6,
});

/**
 * ContentTableView component class.
 * @constructor
 * @classdesc `<ul class=contentTableView id={id}></ul>` is necessary in HTML.
 * usage:
 * `<code>`
 *   var contentTableView = new ContentTableView('contentTableView');
 *   contentTableView.contents = contents; // automatically reconstruct cells.
 * `</code>`
 * @param {string} id - The DOM id where this view is replaced.
 */
class ContentTableView {
    __id__ = null;
    __max_default_cell_number__ = 20;
    __adding_cell_number__ = 20;

    _state = null;
    _cells = []; // list of ContentTableViewCell
    _selectedIndex = null;
    _contents = [];

    constructor(id) {
        // set veiw id
        this.__id__ = id;
        // initialize view elements
        this._setElements();
        // initialize layout
        this._initLayout();
   }

    /**
     * contents setter.
     */
    set contents(contents) {
       this._contents = contents;
       this._resetCells();
       console.log(`${contents.length} cells successfully set.`);
    }

    /**
     * state setter.
     */
    set state(state) {
        const previousState = this._state;
        this._state = state;
        switch (state) {
            case ContentTableViewState.onloading:
                // TODO: loading action
                console.log(`contentTableView state changed -> onloading`);
                this.$contentTableView.style.display = 'block';
                break
            case ContentTableViewState.onshow:
                console.log('contentTableView state changed -> onshow');
                this.$contentTableView.style.display = 'block';
                break
            case ContentTableViewState.onhide:
                console.log('contentTableView state changed -> onhide');
                this.$contentTableView.style.display = 'none';
                break
            case ContentTableViewState.onselected:
                console.log('contentTableView state changed -> onselected');
                this._close(state);
                break
            case ContentTableViewState.onclosestart:
                console.log('contentTableView state changed -> onclosestart');
                this._close(state);
                break
            case ContentTableViewState.onclosecomplete:
                console.log(`contentTableView state changed  ${ContentTableViewState[previousState]}-> onclosecomplete`);
                this.$contentTableView.style.display = 'none';
                switch (previousState) {
                    case ContentTableViewState.onselected:
                        // dispatch statechange event to other object
                        if (previousState != state) {
                            this.$contentTableView.dispatchEvent(
                                new CustomEvent(
                                    'onclosecomplete', {
                                        detail: {
                                            previous: previousState,
                                            new: state,
                                            selected: this._selectedIndex,
                            }}));
                        }
                        break
                    case ContentTableViewState.onclosestart:
                        // dispatch statechange event to other object
                        if (previousState != state) {
                            this.$contentTableView.dispatchEvent(
                                new CustomEvent(
                                    'onclosecomplete', {
                                        detail: {
                                            previous: previousState,
                                            new: state,
                                            selected: null,
                            }}));
                        }
                        break
                    }
        }
    }

    /**
     * DOM nodes as variables.
     */
    _setElements() {
        this.$contentTableView = document.getElementById(this.__id__);
        if (this.$contentTableView == null) {
            console.warn(
                `<ul id=${this.__id__} class=contentTableView></ul> is necessary in HTML.`);
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
                _this.state = ContentTableViewState.onselected;
            });
            document.getElementById(cell.__id__).addEventListener('mouseover', e => {
                _this.$contentTableView.dispatchEvent(
                    new CustomEvent(
                        'onmouseover', {detail: {cellId: cell.__id__, index: cell.__index__}}
                    ));
            });
            document.getElementById(cell.__id__).addEventListener('mouseout', e => {
                _this.$contentTableView.dispatchEvent(
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
        this.$contentTableView.innerHTML = '';
        this._cells = this._contents.map((content, i) => {
            var cell = new ContentTableViewCell(this.__id__, i);
            cell.content = content;
            return cell;
        })
        console.table(this._cells);
        this._setEventHandlers();
    }

    /**
    * To show this view component.
    */
    _show() {
    }

    /**
    * Close this view component.
    */
    _close() {
        console.log(`${this.__id__} close function called. (previousState ${this.state})`);
        var _this = this;
        const interval = 50;
        this._cells.forEach(cell =>{
            setTimeout(()=>{cell.hide()}, cell.__index__*interval);
        })
        this.$contentTableView.animate({
            opacity: 0
        }, interval*this._cells.length, 'easeInSine').finished.then(()=> {
            _this.state = ContentTableViewState.onclosecomplete;
        })
    }
}
