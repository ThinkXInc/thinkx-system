'use strict'
/**
 * @fileoverview business/view_components/edit_content_view.js
 * EditContentView component class.
 * 
 * usage:
 * <code>
 *   var editContentView = new EditContentView(`editContentView`, content);
 *   contentEdit.state = EditContentViewState.onshow;
 * </code>
 * 
 * @author kaz@thinkxinc.com (Kazuki Otsuka)
 */


/**
 * EditContentView State Enum.
 */
const EditContentViewState = Object.freeze({
    onhide: 0,
    onshow: 1,
    ondone: 2,
    onclosestart: 3,
    onclosecomplete: 4,
});


/**
 * EditingContent Data Model
 */
class EditingContent extends Content {

}


/**
 * EditContentView component class.
 * @constructor
 * @classdesc `<ul id={id} class=editContentView></ul>` is necessary in HTML.
 * usage:
 * `<code>`
 *   var editContentView = new EditContentView(`editContentView`, content);
 *   contentEdit.state = EditContentViewState.onshow;
 * `</code>`
 * @param {string} id - The DOM id where this view is replaced.
 */
class EditContentView {
    __id__ = null;
    _state = EditContentViewState.onhide;

    // text fields
    // TODO: set up in the constructor() with locale texts
    $labelField = new TextField(
        'labelField', TextFieldType.singleline, '名称(必須)', 'label',
        '(例) Mona Lisa', 14, 1, false);

    $titleField = new TextField(
        'titleField', TextFieldType.multiplelines, '見出し(必須)', 'title',
        '(例) Mona Lisa Title and subject', 140, 4, false);

    $textField = new TextField(
        'textField', TextFieldType.multiplelines, '本文(必須)', 'text',
        '(例) The title of the painting, which is known in English as Mona Lisa, comes from a description by Renaissance art historian Giorgio Vasari, who wrote "Leonardo undertook to paint, for Francesco del Giocondo, the portrait of Mona Lisa, his wife.Mona Lisa Title and subject',
        1000, 6, false);

    // select buttons
    $targetUserSelectButton = new DropdownButton(
        'targetUserSelectButton', '対象ユーザー', '配信対象のユーザー', 'target',
        DropdownMenuType.list, 
        DropdownMenuDisplayPositionType.upper,
        [
            new ListMenu('全員', 0),
            new ListMenu('若い世代', 1),
            new ListMenu('高リテラシー', 2),
            new ListMenu('高齢者', 3),
        ]);

    $radiusSelectButton = new DropdownButton(
        'radiusSelectButton', '半径', '配信エリアの半径', 'radius',
        DropdownMenuType.list, 
        DropdownMenuDisplayPositionType.upper,
        [
            new ListMenu('1m', 1),
            new ListMenu('3m', 3),
            new ListMenu('5m', 5),
            new ListMenu('10m', 10),
            new ListMenu('30m', 30),
        ]);

    translateResultsTableView = new TranslateResultsTableView('translateResultsTableView');

    editingMapBalloon = null;
    
    intervalID = null;  // set after setRequestInterval() is called.
    hasChange = false;  // if some value is changed, become true. false when a save request was sent.

    // data
    _content = {};
    _editingContent = {};

    constructor(id) {
        // set veiw id
        this.__id__ = id;
        // initialize view elements
        this._setElements();
        // initialize layout
        this._initLayout();
        // set event handlers
        this._setEventHandlers();
        // translateResultsTableView
        this.translateResultsTableView.state = TranslateResultsTableViewState.onhide;
   }

    /**
     * content setter.
     */
    set content(content) {
        this._content = content;
        if (content) {
            console.log(`content ${content.__id__} successfully set.`);
            this.$labelField.text = content.label;
            this.$titleField.text = content.title;
            this.$textField.text = content.text;
            this.$targetUserSelectButton.selectedValue = content.target;
            this.$radiusSelectButton.selectedValue = content.radius;
        } else {
            console.log('content is set as null.');
            this.$labelField.text = '';
            this.$titleField.text = '';
            this.$textField.text = '';
            this.$targetUserSelectButton.selectedValue = null;
            this.$radiusSelectButton.selectedValue = null;
        }
    }

    /**
     * content getter.
     */
    get content() {return this._content; }
 

    /**
     * editingContent setter.
     */
    set editingContent(editingContent) {
        this._editingContent = editingContent;
        console.log(`editingContent id:${editingContent.__id__} successfully set.`);
        console.table(this._editingContent);

        if (!editingContent.isEmpty()) {
            console.error('has change')
            this.hasChange = true;
        } else {
            console.error('no change')
        }

        // update newEditingMapBalloon
        if (editingContent.title &&
            editingContent.title.length > 0) {
                this.editingMapBalloon.title = editingContent.title;
        }
        if (editingContent.text &&
            editingContent.text.length > 0) {
                this.editingMapBalloon.text = editingContent.text;
        }

    }


    /**
     * editingContent getter.
     */
    get editingContent() {return this._editingContent; }


    /**
     * state setter.
     */
    set state(state) {
        this._state = state;
        switch (state) {
            case EditContentViewState.onhide:
                console.log('editContentView state changed -> onloading');
                this.$editContentView.style.display = 'none';
                this._removeIntervalRequest();
                break
            case EditContentViewState.onshow:
                console.log('editContentView state changed -> onshow');
                this.$editContentView.style.display = 'block';
                this.translateResultsTableView.state = TranslateResultsTableViewState.onshow;
                this._startIntervalRequest();
                break
             case EditContentViewState.onback:
                console.log('editContentView state changed -> onback');
                break
             case EditContentViewState.ondone:
                console.log('editContentView state changed -> ondone');
                break
             case EditContentViewState.onclosestart:
                console.log('editContentView state changed -> onclosestart');
                var event = new CustomEvent(
                    'onclosestart', {
                        detail: {new: state,}
                    });
                this.$editContentView.dispatchEvent(event);
                this._close();
                this.translateResultsTableView.state = TranslateResultsTableViewState.onshow;
                break
              case EditContentViewState.onclosecomplete:
                console.log('editContentView state changed -> onclosecomplete');
                var event = new CustomEvent(
                    'onclosecomplete', {
                        detail: {new: state,}
                    });
                this.$editContentView.dispatchEvent(event);
                this.$editContentView.style.display = 'none';
                break
            }
    }

    /**
     * DOM nodes as variables.
     */
    _setElements() {
        this.$editContentView = document.getElementById(this.__id__);
        if (this.$editContentView == null) {
            console.warn(
                `<section id=${this.__id__} class=editContentView></section> is necessary in HTML.`);
        }
        this.$header = this.$editContentView.querySelector('.editheader');
        if (this.$header == null) {
            console.warn(
                `<div class=editheader> is necessary in HTML.`);
        }
        this.$scrollContainer = this.$editContentView.querySelector('.editContentViewScrollContainer');
        if (this.$scrollContainer == null) {
            console.warn(
                `<div class=editContentViewScrollContainer> is necessary in HTML.`);
        }
        this.$saveButton = this.$editContentView.querySelector('.editheader .save');
        if (this.$saveButton == null) {
            console.warn(
                `<div class=editheader><button class=save> is necessary in HTML.`);
        }
        this.$cancelButton = this.$editContentView.querySelector('.editheader .cancel');
        if (this.$cancelButton == null) {
            console.warn(
                `<div class=editheader><button class=cancel> is necessary in HTML.`);
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
        // add shadow to the header when scrolling 
        this.$editContentView.onscroll = (e) => {
            if (e.target.scrollTop == 0) {
                _this.$header.classList.remove('onscroll');
            } else {
                _this.$header.classList.add('onscroll');
            }
        }
        // label
        this.$labelField.$textArea.addEventListener('input', (e) => {
            console.log(`${this.$labelField.__id__}: text in textarea changed.`)
            const label = _this.$labelField.$textArea.value;
            console.info(label);
            let c = this.editingContent;
            c.label = label;
            this.editingContent = c;
        });
        // title
        this.$titleField.$textArea.addEventListener('input', (e) => {
            console.log(`${this.$titleField.__id__}: text in textarea changed.`)
            const title = _this.$titleField.$textArea.value;
            console.info(title);
            let c = this.editingContent;
            c.title = title;
            this.editingContent = c;
        });
        // text
        this.$textField.$textArea.addEventListener('input', (e) => {
            console.log(`${this.$textField.__id__}: text in textarea changed.`)
            const text = _this.$textField.$textArea.value;
            console.info(text);
            let c = this.editingContent;
            c.text = text;
            this.editingContent = c;
        });
        // target
        this.$targetUserSelectButton.$dropdownButton.addEventListener('selected', (e) => {
            console.log(`${this.$targetUserSelectButton.__id__}: button menu selected.`)
            const val = _this.$targetUserSelectButton.selectedValue;
            let c = this.editingContent;
            c.target = val;
            this.editingContent = c;
        })
        // radius
        this.$radiusSelectButton.$dropdownButton.addEventListener('selected', (e) => {
            console.log(`${this.$radiusSelectButton.__id__}: button menu selected.`)
            const val = _this.$radiusSelectButton.selectedValue;
            let c = this.editingContent;
            c.radius = val;
            this.editingContent = c;
        })
    }

    /**
     * Validate if it's possible to request
     * @returns {bool} readyToRequest - 
     */
    _validateToRequest() {

        console.log(`
            ${this.hasChange}
            ${this._editingContent.label}
            ${this._editingContent.title}
            ${this._editingContent.text}
        `);

        if (this.hasChange &&
            
            this._editingContent.label &&
            this._editingContent.label.length > 0 &&
            this._editingContent.label.length <= this.$labelField.__max_text_count__ &&

            this._editingContent.title &&
            this._editingContent.title.length > 0 &&
            this._editingContent.title.length <= this.$titleField.__max_text_count__ &&

            this._editingContent.text &&
            this._editingContent.text.length > 0 &&
            this._editingContent.text.length <= this.$textField.__max_text_count__){

            return true;
        };

        return false;
    }


    /**
     * Set request interval.
     * @returns {string} intervalID - 
     */
    _startIntervalRequest(duration=3000) {
        this.intervalID = window.setInterval(() => {
            if (this._validateToRequest()) {
                console.log('all editing values are valid. request translation and save.');
                this.hasChange = false;
                const text = this._editingContent.text;
                const langs = [
                    TargetLang.JA,
                    TargetLang.EN,
                    TargetLang.ZH,
                    TargetLang.FR,
                    TargetLang.IT,
                    TargetLang.RU,
                    TargetLang.ES,
                    TargetLang.SV,
                    TargetLang.NL,
                    TargetLang.HU,
                    TargetLang.PT
                ]
                langs.forEach((lang) => {
                    translate(
                        text, lang,
                        (res) => {
                            const translatedText = res.translations[0].text;
                            console.log(translatedText);
                            // set result to translateResultsTableView
                            let results = this.translateResultsTableView.results;
                            results[lang] = new TranslateResult(lang, translatedText);
                            this.translateResultsTableView.results = results;
                        },
                        (res) => {
                        });
                })
            } else {
                console.error('no');
            }
        }, duration);
    }

    /**
     * Remove request interval.
     * @returns {string} intervalID - 
     */
    _removeIntervalRequest() {
        clearInterval(this.intervalID);
    }



    /**
    * To show this view component.
    * @param 
    * @return
    */
    show() {
    }

    /**
    * Close this view component.
    * @param 
    * @return
    */
    _close() {
        console.log(`${this.__id__} close`);
        const interval = 100;
        this.$editContentView.animate({
            opacity: 0
        }, interval, 'easeInSine').finished.then(()=> {
            this.state = EditContentViewState.onclosecomplete;
        })
   }
}

