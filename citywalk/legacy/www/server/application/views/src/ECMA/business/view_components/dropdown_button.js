'use strict'
/**
 * @fileoverview business/view_components/dropdown_button.js
 * Dropdown button component class.
 * 
 * usage:
 * <code>
 * </code>
 * 
 * @author kaz@thinkxinc.com (Kazuki Otsuka)
 */


/**
 * Dropdown Button State Enum.
 */
const DropdownButtonState = Object.freeze({
    onclose: 1,
    onopen: 2,
    onselected: 3,  // not in use
});


/**
 * Dropdown Menu type Enum.
 */
const DropdownMenuType = Object.freeze({
    list: 1,
    widelist: 2,
    calendar: 3,
});


/**
 * Dropdown Menu Display Position type Enum.
 */
const DropdownMenuDisplayPositionType = Object.freeze({
    bottom: 1,
    bottomover: 2,
    upper: 3,
    upperover: 4,
});


/**
 * Dropdown list Data Model.
 */
class ListMenu {
    title = null;
    value = null; // value of enum
    constructor(title, value) {
        this.title = title;
        this.value = value;
        if (this.title == null || this.value == null) {
            console.error('both title and value of ListMenu are necessary but null.')
        }
    }
}


/**
 * Dropdownbutton component class.
 * @constructor
 * @classdesc `<div class=dropdownButton id={id}></ul>` is necessary in HTML.
 * usage:
 * `<code>`
 *  var dropdownButton = new DropdownButton(
 *      'countrySelectButton', 'Your Country', 'Please select your country.',
 *      'country',
        DropdownMenuType.list, 
        DropdownMenuDisplayPositionType.upper,
        [
            new ListMenu('Afganistan', 12),
            new ListMenu('Belarus', 73),
            new ListMenu('China', 981),
            new ListMenu('Denmark', 33),
            ...
        ]);
 *  dropdownButton.state = close;
 * `</code>`
 * @param {string} id - The DOM id where this view is inserted.
 * @param {string} title - displayed title.
 * @param {string} desctiption - displayed description.
 * @param {DropdownMenuType} type - {list|widelist|calender}. (list: 100% width options list, widelist: list of any width, calendar: calendar)
 * @param {DropdownMenuDisplayPositionType} position - {bottom|bottomover|upper|upperover} 
 * @param {[ListMenu]} listMenuItems - list of ListMenu with title, value.
 */
class DropdownButton {
    __outer_template_sample__ = `
        <div id=dropdown1 class=dropdownButton></div>
    `
    __inner_template__ = `
        <div class="dropdownButtonClickable cf">
            <h6 class=description>$description</h6>
            <span class=title>$title</span>
            <img class=downarrow src=/img/icons/arrow-down.png srcset="/img/icons/arrow-down@2x.png 2x"/>
            <div class="footer cf"></div>
        </div>
    `
    __list_menu_template__ = `
        <ul class=listmenu style=display:none;>
        </ul>
    `
    __list_item_template__ = `
        <li class=listitem data-value=$value data-title="$title">$title</li>
    `

    __id__ = null;
    __description__ = null;
    __field_name__ = null;
    __items__ = null;
    __menu_position__ = DropdownMenuDisplayPositionType.upper;
    __width__ = null;  // TODO: widelist

    _state = DropdownButtonState.onclose;
    _selectedValue = null;
    _title = null;

    constructor(id, title, description, fieldName, type, position, listMenuItems) {
        // set configuration variables
        this.__id__ = id;
        this.__description__ = description;
        this.__field_name__ = fieldName;
        this.__type__ = type;
        this.__items__ = listMenuItems;
        this.__menu_position__ = position;

        this._title = title;

        // set html elements
        document.getElementById(id).innerHTML = this.__inner_template__
            .replace('$title', title).replace('$description', description);
        if (type == DropdownMenuType.list || type == DropdownMenuType.widelist) {
            document.getElementById(id).innerHTML += this.__list_menu_template__;
        }
        this._setElements();

        // set list menu items
        if (type == DropdownMenuType.list || type == DropdownMenuType.widelist) {
            this._setListMenuItems(listMenuItems);
        }

        // set event handlers
        this._setEventHandlers();
    }

    /* setters */

    /**
     * state setter.
     */
    set state(state) {
        const previousState = this._state;
        this._state = state;
        switch (state) {
            case DropdownButtonState.onclose:
                console.log(`DropdownButton state changed -> onclose`);
                this._removeClosingUnderSheet();
                this.$toggleItem.style.display = 'none';
                break
            case DropdownButtonState.onopen:
                console.log(`DropdownButton state changed -> onopen`);
                console.log(this.$toggleItem);
                this.$toggleItem.style.display = 'block';
                console.log(this.__menu_position__);
                if (this.__menu_position__ == DropdownMenuDisplayPositionType.bottom) {
                    this.$toggleItem.style.top = `${this.$dropdownButton.offsetTop + this.$dropdownButton.offsetHeight}px`;
                } else if (this.__menu_position__ == DropdownMenuDisplayPositionType.bottomover) {
                    this.$toggleItem.style.top = `${this.$dropdownButton.offsetTop}px`;
                } else if (this.__menu_position__ == DropdownMenuDisplayPositionType.upper) {
                    this.$toggleItem.style.top = `${this.$dropdownButton.offsetTop - this.$listMenu.offsetHeight}px`;
                } else if (this.__menu_position__ == DropdownMenuDisplayPositionType.upperover) {
                    this.$toggleItem.style.top = `${this.$dropdownButton.offsetTop - this.$listMenu.offsetHeight - this.$dropdownButton.offsetHeight}px`;
                } else {
                    console.error(`${this.__menu_position__} is unknown position.`);
                }
                // add click outside -> close event
                this._addClosingUnderSheet(this, this.$listMenu);
                break
            case DropdownButtonState.onselected:
                console.log(`DropdownButton state changed -> onselected`);
                // NOTE: not in use so far
                break
        }
    }
 
    /**
     * selectedValue setter.
     */
    set selectedValue(selectedValue) {
        const previousState = this._selectedValue;
        this._selectedValue = selectedValue;
        if (selectedValue != null) {
            const item = this.__items__.find((item) => item.value == selectedValue);
            if (item == null) {
                console.error(`${selectedValue} is not in items. see below.`);
                console.table(this.__items__);}
            else {
                this._setTitle(item.title);
            }
        }
        const event = new CustomEvent(
            'selected', {detail: {value: selectedValue, id: this.__id__}});
        this.$dropdownButton.dispatchEvent(event);
    }

    /**
     * selectedValue getter.
     */
    get selectedValue() {return this._selectedValue;}
 
    /* private methods */

    /**
     * DOM nodes as variables.
     */
    _setElements() {
        this.$dropdownButton = document.getElementById(this.__id__);
        if (this.$dropdownButton == null) {
            console.warn(
                `<div id=${this.__id__} class=dropdownButton></div> is necessary in HTML.`);
        }
        this.$title = this.$dropdownButton.querySelector('.title');
        if (this.$title == null) {
            console.warn(
                `<span class=title></span> is necessary in HTML.`);
        }
        this.$dropdownButtonClickable = this.$dropdownButton.querySelector('.dropdownButtonClickable');
        if (this.$dropdownButtonClickable == null) {
            console.warn(
                `<div class=dropdownButtonClickable></div> is necessary in HTML.`);
        }
        if (this.__type__ == DropdownMenuType.list || this.__type__ == DropdownMenuType.widelist) {
            this.$listMenu = this.$dropdownButton.querySelector('.listmenu');
            this.$toggleItem = this.$listMenu;
            if (this.$listMenu == null) {
                console.warn(
                    `<ul class=listmenu></ul> is necessary in HTML.`);
            }
        }
    }

    /**
     * Initialize the layout for display.
     */
    _initLayout() {
    }

    /**
     * Set list menu items (type: list, widelist).
     * @param {ListMenu} items - list of ListMenu with (title, value)
     */
    _setListMenuItems(items) {
        console.log(`set ${items.length} list menu items into ${this.__id__}.`)
        if (IS_DEBUG) { console.table(items) };
        items.forEach((item) => {
            this.$listMenu.innerHTML += 
                this.__list_item_template__
                .replaceAll('$title', item.title).replace('$value', item.value);
        });
    }

    /**
     * Set selected title.
     * @param {string} title - 
     */
    _setTitle(title) {
        console.log(`set ${title} as title.`)
        this.$title.innerHTML = title;
    }

    /**
     * Set event handlers.
     */
    _setEventHandlers() {
        const _this = this;
        this.$dropdownButtonClickable.addEventListener('click', e => {
            console.log(`button ${_this.__id__} clicked`)
            if (_this._state == DropdownButtonState.onclose) {
                _this.state = DropdownButtonState.onopen;
                e.stopPropagation();
            }
            else if (_this._state == DropdownButtonState.onopen) {
               _this.state = DropdownButtonState.onclose;
            }
            else {
                console.error(`unknown current state of ${_this.__id__} ${_this._state}`)
            }
        });
        this.$listMenu.addEventListener('click', e => {
            console.log(this.$listMenu.querySelector(':hover'));
            console.table(this.$listMenu.querySelector(':hover').dataset);
            const selectedValue = this.$listMenu.querySelector(':hover').dataset.value;
            console.log(`selected value: ${selectedValue}`);
            this._selectedValue = selectedValue;
            this._setTitle(this.$listMenu.querySelector(':hover').dataset.title);
            this.state = DropdownButtonState.onclose;
            // dispatch event
            const event = new CustomEvent('selected', {detail: {id: this.__id__, value: selectedValue}});
            this.$dropdownButton.dispatchEvent(event);
        });
    }

    /**
     * Add the element that changes state to close when clicked.
     * 
     * @description This function is reusable for similar cases
     * by changing lines `modify this`.
     * @param {DropdownButton} this - the instance of the UI component.
     * @param {Element} $before - the element where this sheet is inserted.
     */
    _addClosingUnderSheet(_this, $before) {
        let under = document.createElement('span');
        under.id = this.__id__ + '-under';
        under.style.position = 'absolute';
        under.style.width = `${screen.width + 1000}px`;
        under.style.height = `${screen.height + 1000}px`;
        //under.style.background = 'rgb(0,0,0,0.2)'; // visible test
        under.style.top = '0px';
        under.style.left = '0px';
        under.style.zIndex = 1;
        this.$dropdownButton.insertBefore(under, $before); // modify this
        const __this = _this;
        under.addEventListener('click', e => {
            if (__this._state == DropdownButtonState.onopen) { // modify this
                __this.state = DropdownButtonState.onclose; // modify this
                e.currentTarget.remove();
            } else {
                console.log('nothing happens.')
            }
        }, {capture: true, once: true});
    }

    /**
     * Remove undersheet element when close.
     */
    _removeClosingUnderSheet() {
        document.getElementById(this.__id__ + '-under').remove();
    }

    /* public functions */

    /**
     * Add/Remove alert.
     * 
     * @param {bool} onAlert 
     * @param {string} message
     */
    alert(onAlert, message) {
        const id =  this.__id__ + '_alert';
        let $parent = this.$dropdownButton;
        let $footer = $parent.querySelector('.footer');
        if (onAlert) {
            // add alert to css
            $parent.classList.add('alert');

            // if the alertMessage already exists
            if (document.getElementById(id) != null) {
                // the same alert is displayed, return
                if (message == document.getElementById(id).innerText) {
                    return
                // or update the message
                } else {
                    document.getElementById(id).innerText = message;
                    return
                }
            };

            // if no alertMessage exists, add new alert message
            let $alertMessage = document.createElement('p');
            $alertMessage.classList.add('alertMessage');
            $alertMessage.id = id;
            $alertMessage.innerText = message;
            $footer.appendChild($alertMessage);
        } else {
            // return if alertMessage is already removed
            if (document.getElementById(id) == null) { return };

            // add alert to css
            $parent.classList.remove('alert');

            // remove alert message
            let $alertMessage = document.getElementById(id);
            $footer.removeChild($alertMessage);
        }
    }
}
