'use strict'
/**
 * @fileoverview business/view_components/textfield.js
 * TextField view component class.
 * 
 * usage:
 * <code>
 * </code>
 * 
 * @author kaz@thinkxinc.com (Kazuki Otsuka)
 */


/**
 * TextField State Enum.
 */
const TextFieldState = Object.freeze({
    onhide: 0,
    onshow: 1,
    //onfocus: 3,  // TODO:
    //onlock: 4,  // TODO:
});


/**
 * TextField Loading State Enum.
 */
const TextFieldLoadingState = Object.freeze({
    none: 0,
    onloading: 1,
    done: 2,
});


/**
 * TextField Validation State Enum.
 */
const TextFieldValidationState = Object.freeze({
    none: 0,
    onalert: 1,
    onverified: 1,
});


/**
 * TextField Input State Enum.
 */
const TextFieldInputState = Object.freeze({
    empty: 0,
    filled: 1,
    overmaximum: 2,
});


/**
 * TextField Type Enum.
 */
const TextFieldType = Object.freeze({
    singleline: 0,
    multiplelines: 1,
});


/**
 * TextField component class.
 * @constructor
 * @classdesc `<div id={id} class=textField>` is necessary in HTML.
 * usage:
 * `<code>`
 *     titleField = new TextField(
 *         'titleField', TextFieldType.multiplelines, 'title(reqired)', 'title',
 *         'Mona Lisa Title and subject', 140, 4, false);
 * `</code>`
 * @param {string} id - The DOM id where this view is set.
 * @param {TextFieldType} type - {singleline|multipleline}
 * @param {string} title - title text in header
 * @param {string} field_name - name={field_name} in input or textarea.
 * @param {string} placeholder - placeholder={placeholder} in input or textarea.
 * @param {number} max_text_count - maximum text count
 * @param {number} init_rows - initial textarea rows
 * @param {boolean} vertical_flex - if true, textarea expands vertically
 * @param {boolean} has_title - if true, display the inner title
 * @event textupdated - dispatched when the text is updated.
 */
class TextField {
    __inner_template_single__ = `
        <div class="name inputouter">
            <h6 class=title>$title</h6>
            <input class=$field_nameform name=$field_name type=text autocomplete=off/>
            <div class="footer cf">
                <span class=indicator></span>
                <span class=message></span>
                <span class=counter></span>
            </div>
        </div>
    `
    __inner_template_multiple__ = `
        <div class="name inputouter">
            <h6 class=title>$title</h6>
            <textarea class=$field_nameform name=$field_name rows=$rows contenteditable></textarea>
            <div class="footer cf">
                <span class=indicator></span>
                <span class=message></span>
                <span class=counter></span>
            </div>
        </div>
    `

    __counter_format__ = `$count/$maxcount`;

    __id__ = null;
    __title__ = null;
    __field_name__ = null;
    __placeholder__ = null;
    __max_text_count__ = null;

    __init_rows__ = null;
    __vertical_flex__ = null;

    // states
    _state = null;
    _loadingstate = null;
    _validationstate = null;
    _inputstate = null;

    // data
    _text = '';
    _count = null;

    constructor(
        id, type, title, field_name, placeholder,
        max_text_count=999, init_rows=6, vertical_flex=true, has_title=true,
        password_mode=false) {
        if (document.getElementById(id) == null) {
            console.error(
                `<section id=${id} class=textField></section> is necessary in HTML.`);
        }
        // set html
        document.getElementById(id).innerHTML = (type == TextFieldType.singleline) ?
            this.__inner_template_single__.replaceAll('$field_name', field_name)
                .replaceAll('$title', title).replaceAll('$rows', init_rows)
            : this.__inner_template_multiple__.replaceAll('$field_name', field_name)
                .replaceAll('$title', title).replaceAll('$rows', init_rows);
        // set veiw id
        this.__id__ = id;
        this.__type__ = type;
        this.__title__ = title;
        this.__field_name__ = field_name;
        this.__placeholder__ = placeholder;
        this.__max_text_count__ = max_text_count;
        this.__init_rows__ = init_rows;
        this.__vertical_flex__ = vertical_flex;
        this.__has_title__ = has_title;
        this.__password_mode__ = password_mode;
        if (typeof this.__type__ !== 'number') {
            console.error(`type must be type of number, but ${typeof type}`);
        }
        if (typeof this.__title__ !== 'string') {
            console.error(`title must be type of string, but ${typeof title}`);
        }
        if (typeof this.__field_name__ !== 'string') {
            console.error(`field_name must be type of string, but ${typeof field_name}`);
        }
        if (typeof this.__placeholder__ !== 'string') {
            console.error(`placeholder must be type of string, but ${typeof placeholder}`);
        }
        if (typeof this.__max_text_count__ !== 'number') {
            console.error(`max_text_count must be max_text_count of number, but ${typeof max_text_count}`);
        }
        if (typeof this.__init_rows__ !== 'number') {
            console.error(`init_rows must be init_rows of number, but ${typeof init_rows}`);
        }
        if (typeof this.__vertical_flex__ !== 'boolean') {
            console.error(`vertical_flex must be type of bool, but ${typeof vertical_flex}`);
        }
        if (typeof this.__has_title__ !== 'boolean') {
            console.error(`has_title must be type of bool, but ${typeof has_title}`);
        }
         if (typeof this.__password_mode__ !== 'boolean') {
            console.error(`password_mode must be type of bool, but ${typeof password_mode}`);
        }
 
        // initialize view elements
        this._setElements();
        // initialize layout
        this._initLayout();
        // set eventhandlers
        this._setEventHandlers();
        // set counter 
        this.count = 0;
        // password mode
        this._togglePasswordMode(this.__password_mode__);
    }

    /**
     * text setter.
     */
    set text(text) {
        this._text = text;
        this.$textArea.value = text;
        console.log(`text updated: ${text}`);
        // count
        if (text) {
            this.count = text.length;
        }
        // dispatch event
        const event = new CustomEvent('textupdated', {detail: {new: text,}});
        this.$textField.dispatchEvent(event);
    }

    /**
     * text getter.
     */
    get text() {return this._text}

    /**
     * count setter.
     */
    set count(count) {
        this._count = count;
        // update counter text
        this.$counter.innerHTML = this.__counter_format__
            .replace('$count', count).replace('$maxcount', this.__max_text_count__);
    }

    /**
     * count getter.
     */
    get count() {return this._count}

    /**
     * state setter.
     */
    set state(state) {
        this._state = state;
        switch (state) {
            case TextFieldState.onhide:
                console.log(`TextField ${this.__id__} state changed -> onhide`);
                break
            case TextFieldState.onshow:
                console.log(`TextField ${this.__id__} state changed -> onshow`);
                break
        }
    }

    /**
     * loadingstate setter.
     */
    set loadingstate(state) {
        this._loadingstate = state;
        switch (state) {
            case TextFieldLoadingState.none:
                console.log(`TextField ${this.__id__} loadingstate changed -> none`);
                break
            case TextFieldLoadingState.onloading:
                console.log(`TextField ${this.__id__} loadingstate changed -> onloading`);
                break
        }
    }

    /**
     * validationstate setter.
     */
    set validationstate(state) {
        this._validationstate = state;
        switch (state) {
            case TextFieldValidationState.none:
                console.log(`TextField ${this.__id__} validationstate changed -> none`);
                this.$textField.classList.remove('alert');
                break
            case TextFieldValidationState.onalert:
                console.log(`TextField ${this.__id__} validationstate changed -> onalert`);
                this.$textField.classList.add('alert');
                break
            case TextFieldValidationState.onverified:
                console.log(`TextField ${this.__id__} validationstate changed -> onverified`);
                this.$textField.classList.remove('alert');
                break
        }
    }

    /**
     * inputstate setter.
     */
    set inputstate(state) {
        this._inputstate = state;
        switch (state) {
            case TextFieldInputState.empty:
                console.log(`TextField ${this.__id__} inputstate changed -> empty`);
                this.$textField.classList.remove('overMaximumTextCount');
                break
            case TextFieldInputState.filled:
                console.log(`TextField ${this.__id__} inputstate changed -> filled`);
                this.$textField.classList.remove('overMaximumTextCount');
                break
            case TextFieldInputState.overmaximum:
                console.log(`TextField ${this.__id__} inputstate changed -> overmaximum`);
                this.$textField.classList.add('overMaximumTextCount');
                break
        }
    }
    /**
     * DOM nodes as variables.
     */
    _setElements() {
        // textField
        this.$textField = document.getElementById(this.__id__);
        if (this.$textField == null) {
            console.warn(
                `<section id=${this.__id__} class=textField></section> is necessary in HTML.`);
        }
        // title
        this.$title = this.$textField.querySelector('.title');
        if (this.$title == null) {
            console.warn(
                `<h6 class=title> is necessary in HTML.`);
        }
        if (!this.__has_title__) {
            this.$title.remove();
        }
        // textArea
        if (this.__type__ == TextFieldType.singleline) {
            this.$textArea = this.$textField.querySelector('input');
            if (this.$textArea == null) {
                console.warn(`<input> is necessary in HTML.`);
            }
        } else if (this.__type__ == TextFieldType.multiplelines) {
            this.$textArea = this.$textField.querySelector('textarea');
            if (this.$textArea == null) {
                console.warn(`<input> is necessary in HTML.`)
            }
        }
        this._setPlaceholder(this.__placeholder__);
        // indicator
        this.$indicator = this.$textField.querySelector('.indicator');
        if (this.$indicator == null) {
            console.warn(`<span class=indicator> is necessary in HTML.`);
        }
        // message
        this.$message = this.$textField.querySelector('.message');
        if (this.$message == null) {
            console.warn(`<span class=message> is necessary in HTML.`);
        }
        // counter
        this.$counter = this.$textField.querySelector('.counter');
        if (this.$counter == null) {
            console.warn(`<span class=counter> is necessary in HTML.`);
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
        this.$textArea.addEventListener('input', (e) => {
            console.log(`text in textarea changed. -> ${_this.$textArea.value}`)
            _this.text = _this.$textArea.value;
            _this.count = _this.$textArea.value.length;

            // set state as the text count 
            console.log(`max text count: ${_this.__max_text_count__} count: ${_this.count}`);
            if (_this.count > _this.__max_text_count__) {
                _this.validationstate = TextFieldValidationState.onalert;
                _this.inputstate = TextFieldInputState.overmaximum;
            } else if (_this.count == 0) {
                _this.validationstate = TextFieldValidationState.none;
                _this.inputstate = TextFieldInputState.empty;
            } else {
                _this.validationstate = TextFieldValidationState.none;
                _this.inputstate = TextFieldInputState.filled;
            }
        })

        // auto resize vertically
        if (_this.__vertical_flex__) {
            _this.$textArea.addEventListener('keydown', ()=> {
                setTimeout(()=> {
                    _this.$textArea.style.cssText = `height:auto;`;
                    _this.$textArea.style.cssText = `height:${_this.$textArea.scrollHeight}px;`;
                }, 0);
            });
        }

        // onfocus

        // on
    }

    /* private functions */

    /**
     * Toggle Password mode.
     * 
     * @param {boolean} passwordMode this.__password_mode__
     */
    _togglePasswordMode(passwordMode) {
        if (this.__type__ == TextFieldType.singleline) {
            if (passwordMode) {
                this.$textArea.type = 'password';
                console.log(this.$textArea.type);
            } else {
                this.$textArea.type = 'text';
            }
        } else if (this.__type__ == TextFieldType.multiplelines) {
            console.warn(`<textarea> doesn't allow password type.`);
        }
    }

    /**
     * Set placeholder.
     * @param {string} placeholder - 
     */
    _setPlaceholder(placeholder) {
        this.$textArea.placeholder = placeholder;
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
        let $parent = this.$textField;
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

