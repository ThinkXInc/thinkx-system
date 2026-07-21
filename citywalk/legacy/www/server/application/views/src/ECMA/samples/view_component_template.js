'use strict'
/**
 * @fileoverview samples/view_component_template.js
 * A view component sample class.
 * 
 * <code>
 * 
 * usage:
 *  var viewComponent = new ViewComponent(
 *      _id="view_component_1",
 *      view_component_type=window.ViewComponentType.question,
 *  );
 * 
 * args:
 *  - id {string} - id of this view component.
 *  - view_component_type {ViewComponentType} - choose type {1 inquiry|2 question}.
 * 
 * functions:
 *  - show
 *      params:
 *      returns:
 *  - hide
 *      params:
 *      returns:
 * 
 * </code>
 * 
 * @author kaz@thinkxinc.com (Kazuki Otsuka)
 */


/**
 * ViewComponentType Enum.
 */
const ViewComponentType = Object.freeze({
    inquiry: 1,
    question: 2,
});


/**
 * RequestDataModel.
 * @param {string} last_name - last name input value
 * @param {string} first_name - first name input value
 * @param {string} email - email input value
 * @param {string} maintext - maintext input value
 */
class RequestDataModel {
    last_name = null;
    first_name = null;
    email = null;
    maintext = null;

    constructor(last_name, first_name, email, maintext) {
        this.last_name = last_name;
        this.first_name = first_name;
        this.email = email;
        this.maintext = maintext
    }

    validate() {
        // write validation code here..
        return true
    }
}


/**
 * ViewComponent State Enum.
 */
const ViewComponentState = Object.freeze({
    onloading: 1,
    onshow: 2,
    onhide: 3,
});


/**
 * A ViewComponent Template Class.
 * @constructor
 * @param {string} id - The DOM id where this view is replaced.
 * @param {ViewComponentType} view_component_type - view_component_type
 *     Choose type from {1 inquiry|2 question}.
 */
class ViewComponent {
    __template__ = `\
    <div class=viewComponent id=$id>
        <span id=view_component_$id_icon_container>
            <img id=view_component_$id_icon src=/images/view_component_icon.png srcset=/images/view_component_icon@2x.png 2x/>
        </span>
        <div id=view_component_$id_input_container>
            <input type=text name=last_name/>
            <input type=text name=first_name/>
            <input type=text name=email/>
            <input type=text name=maintext/>
        </div>
        <div id=view_component_$id_button_container>
            <button type=button class=cancel>Cancel</button>
            <button type=button class=done>Done</button>
        </div>
        <p id=view_component_$id_alert></p>
    </div>
    `;

    __id__ = null;

    __min_name_length__ = 1;
    __max_name_length__ = 100;

    __view_component_type__ = null;

    constructor(component_id, view_component_type) {
        this.__id__ = component_id
        // set template to document
        const template = this.__template__.replace('$id', component_id);
        document.getQuerySelector('body').append(template);
        // settings
        this.__view_component_type__ = view_component_type;
        // setup elements
        this._setElements(id);
        // set event handlers
        this._setEventHandlers();

        this.is_shown = false;
    }

    /**
     * state setter.
     * @description should be written decralatively.
     * (good): viewComponent.state = ViewComponentState.onloading; // loading action starts automatically. then state is switched to onshow automatically. 
     * (bad): viewComponent.state; viewComponent.startLoadingAnimation(onend=()=>{$viewComponent.style.display = 'none';});  // Imperative way
     */
    set state(state) {
        this._state = state;
        switch (state) {
            case ViewComponentState.onloading:
                // TODO: loading action
                console.log('viewComponent state changed -> onloading');
                this.$viewComponent.style.display = 'block';
                break
            case ViewComponentState.onshow:
                // TODO: display action
                console.log('viewComponent state changed -> onshow');
                this.$viewComponent.style.display = 'block';
                break
            case ViewComponentState.onhide:
                // TODO: hide action
                console.log('viewComponent state changed -> onhide');
                this.$viewComponent.style.display = 'none';
                break
        }
    }

    /* initializers */

    /**
    * DOM nodes as variables.
    */
    _setElements() {
        this.$viewComponent = document.getElementById(this.__id__);
        this.$icon = this.$viewComponent.getElementById(`view_component_${id}_icon`);
        this.$last_name = this.$viewComponent.querySelector('input[name=last_name]');
        this.$first_name = this.$viewComponent.querySelector('input[name=first_name]');
        this.$email = this.$viewComponent.querySelector('input[name=email]');
        this.$maintext = this.$viewComponent.querySelector('input[name=maintext]');
        this.$cancel_button = this.$viewComponent.querySelector('button.cancel');
        this.$done_button = this.$viewComponent.querySelector('button.done');
        this.$alert = this.$viewComponent.getElementById(`view_component_${id}_alert`);
    }

    /**
     * Initialize the layout for display.
     */
    _initLayout() {
        const window_height = window.innerHeight;
        const window_width = window.innerWidth;
        const view_component_height = this.$viewComponent.innerHeight;
        const view_component_top = window_height > view_component_height 
            ? Math.floor((window_height-view_component_height)/2) : 10;
        this.$viewComponent.style.marginTop = view_component_top;
    }

    /**
     * Set event handlers.
     */
    _setEventHandlers() {
        // email input
        this.$email.addEventListener('input', e => {
            const target = e.target;
            const type = e.type;
            var value = e.target.value;
       });
        // cancel button
        this.$cancel_button.addEventListener('click', e => {
            const target = e.target;
            const type = e.type;
            return this.hide();
        });
        // done button
        this.$done_button.addEventListener('click', e => {
            const target = e.target;
            const type = e.type;
            // submit
            this.submit(this.hide);
        });
    }

    /* public functions */

    /**
    * To show this view component.
    * @param 
    * @return
    */
    show() {
        this._setLayout();
        this.$viewComponent.animate({
            opacity: 1
        }, interval*this._cells.length, 'easeInSine').finished.then(()=> {
            this.state = ViewComponentState.onshow;
        })
    }

    /**
    * To hide this view component.
    * @param 
    * @return
    */
    hide() {
        this.$viewComponent.animate({
            opacity: 0
        }, interval*this._cells.length, 'easeInSine').finished.then(()=> {
            this.state = ViewComponentState.onhide;
        })
    }

    /* private functions */

    /**
    * Collect form data into RequestDataModel.
    * @param
    * @return {RequestDataModel} - The data to be submitted.
    */
    _packData() {
        // collect form data
        const last_name = this.$last_name.value;
        const first_name = this.$first_name.value;
        const email = this.$email.value;
        const maintext = this.$maintext.value; 

        // pack into Request DataModel
        const request_data = new RequestDataModel(
            last_name, first_name, email, maintext
        )

        return request_data
    }

    /**
    * Submit form data.
    * @param {callback function} onsuccess - This function is called after sending seccess.
    * @return
    */
    _submit(onsuccess, onfailed) {
        // url by type
        switch (this.__view_component_type__) {
            case ViewComponentType.inquiry:
                var url = `${app.config.host}/business/inquiry`;
                break;
            case ViewComponentType.question:
                var url = `${app.config.host}/business/question`;
                break;
            default:
                console.error(`${this.__view_component_type__} is unknown view component type`);
        }

        // submitting data
        const request_data = this._requestData();

        // submit
        if (request_data.validate()) {
            fetch(url, {
                method: 'POST',
                headers: {'Content-Type': 'application/json',},
                body: JSON.stringify(data),
            })
            .then(response => response.json())
            .then(data => {
                console.info('fetch success:', data);
                onsuccess(data);
            })
            .catch((error) => {
                console.error('fetch error:', error);
                onfailed(error);
            })
        } else {
            this.$alert.innerHTML = 'input data in not valid.';
        }
    }
}