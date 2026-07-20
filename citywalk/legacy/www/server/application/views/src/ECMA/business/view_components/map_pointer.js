'use strict'
/**
 * @fileoverview business/view_components/map_pointer.js
 * MapPointer view component class.
 * 
 * usage:
 * <code>
 * </code>
 * 
 * @author kaz@thinkxinc.com (Kazuki Otsuka)
 */


/**
 * MapPointer State Enum.
 */
const MapPointerState = Object.freeze({
    onhide: 0,
    onshow: 1,
    onhover: 2,
    onclosestart: 3,
    onclosecomplete: 4,
});


/**
 * MapPointer Action Enum.
 */
const MapPointerAction = Object.freeze({
    show: 0,
    close: 1,
    selectAndClose: 2,
});


/**
 * MapPointer option.
 * usage:
 * `<code>`
 *      MapPointer.options = [
 *          new MapPointerOption('title1', Options.A),
 *          new MapPointerOption('title2', Options.B),
 *      ]
 * @param {string} title - displayed title of option.
 * @param {string} value - any value. eg. createnew.
 * @param {MapPointerAction} action - 
 */
class MapPointerOption {
    title = null;
    value = null;
    action = null;

    constructor(title, value, action) {
        this.title = title;
        this.value = value;
        this.action = action;
        if (typeof this.title !== 'string') {
            console.error('[MapPointerOption] ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓');
            console.error(title);
            console.error(`title must be type of string, but ${typeof this.title}`);
        }
        if (typeof this.value !== 'string') {
            console.error('[MapPointerOption] ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓');
            console.error(value);
            console.error(`value must be type of string, but ${typeof this.value}`);
        }
        if (typeof this.action !== 'number') {
            console.error('[MapPointerOption] ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓');
            console.error(action);
            console.error(`action must be type of number, but ${typeof this.value}`);
        }
    }
}


/**
 * MapPointer component class.
 * @constructor
 * @classdesc 
 * GoogleMap custom layer:
 * https://developers.google.com/maps/documentation/javascript/customoverlays#javascript
 * usage:
 * `<code>`
 * function initMap() {
 *     let script = document.createElement('script');
 *     script.src = '/js/business/view_components/map_pointer.js';
 *     document.getElementById('content').appendChild(script);
 *     script.onload = ()=> {
 *          // map components
 *          this.mapPointer = new MapPointer('newGuidePointer', Coordinate(lat, lng),
 *              [new MapPointerOption('Create Guide Here', 0, MapPointerAction.selectAndClose)]
 *          )
 *     this.mapPointer.setMap(map);
 *   }
 * `</code>`
 * @param {string} id - The DOM id where this view is set.
 * @param {Coordinate} coordinate - 
 * @param {MapPointerOption} options - Select options with pairs of title and value.
 */
class MapPointer extends google.maps.OverlayView {
    __id__ = null;

    __template_sample__ = `
    <div id=$id class=mapPointer>
        <img class=arrow src=/img/parts/map_pointer_arrow.png srcset="/img/parts/map_pointer_arrow@2x.png"/>
        <ul class=listmenu>
            <li class=listitem data-value=$value data-action=$action>$title</li>
        </ul>
    </div>
    `
    __image_arrow_src__ = '/img/parts/map_pointer_arrow.png';
    __image_arrow_src_2x__ = '/img/parts/map_pointer_arrow@2x.png';

    // data
    _coordinate = null;
    _state = null;
    _options = null;
    _value = null;
    _action = null;

    constructor(id, coordinate, options) {
        super();
        // set veiw id
        this.__id__ = id;
        // set data
        this._coordinate = coordinate;
        if (typeof coordinate !== "object") {
            console.error(`coordinate of ${this.__id__} must be type of Coordinate . but ${typeof coordinate}`);
        }
        this.options = options;
    }

    /**
     * value setter.
     */
    set value(value) {
        const previousState = this._value;
        this._value = value;
    }

    /**
     * value getter.
     */
    get value() {return this._value;}

    /**
     * action setter.
     */
    set action(action) {
        const previousState = this._action;
        this._action = action;
    }

    /**
     * action getter.
     */
    get action() {return this._action;}

    /**
     * options setter.
     */
    set options(options) {
        this._options = options;
        console.log(`${options.length} options set.`);
        // TODO: reconstruct html
    }

    /**
     * options getter.
     */
    get options() { return this._options };
 
    /**
     * coordinate getter.
     */
    get coordinate() { return this._coordinate };
 
    /**
     * state setter.
     */
    set state(state) {
        const previousState = this._state;
        this._state = state;
        switch (state) {
            case MapPointerState.onhide:
                console.log(`MapPointer ${this.__id__} state changed -> onhide`);
                break
            case MapPointerState.onshow:
                console.log(`MapPointer ${this.__id__} state changed -> onshow`);
                break
            //case MapPointerState.onhover:
            //    console.log(`MapPointer ${this.__id__} state changed -> onhover`);
            //    break
            case MapPointerState.onclosestart:
                console.log(`MapPointer ${this.__id__} state changed -> onclosestart`);
                console.log(`action: ${this.action} value: ${this._value}`)
                switch (this.action) {
                    case MapPointerAction.selectAndClose:
                        // dispatch statechange event to other object
                        const event = new CustomEvent(
                            'mapPointerSelected', {
                                detail: {
                                    previous: previousState,
                                    new: state,
                                    value: this.value,
                                    action: this.action,
                                }});
                        // MEMO: cannot receive from viewController when the mapPointer node dispatches.
                        //document.getElementById('newGuidePointer').dispatchEvent(event);
                        document.dispatchEvent(event);
                        console.log('dispatch');
                        break
                    case MapPointerAction.close:
                        break
                }
                this._close();
                break
             case MapPointerState.onclosecomplete:
                console.log(`MapPointer ${this.__id__} state changed -> onclosecomplete`);
                // NOTE: process something before hide
                break
        }
    }

    /**
     * state getter.
     */
    get state() {return this._state};

    /**
     * Set elements.
     * @description Called when this instance is created.
     * (OverlayView class override)
     */
    onAdd() {
        // set initial state
        this.state = MapPointerState.onhide;
        // container element
        this.$mapPointer = document.createElement('div');
        this.$mapPointer.id = this.__id__;
        this.$mapPointer.classList.add('mapPointer');
        if (this._options.length == 1 ) {this.$mapPointer.classList.add('single');}
        if (this._options.length == 2 ) {this.$mapPointer.classList.add('double');}
        if (this.$mapPointer == null) {
            console.warn(`<div id=${this.__id__} class=mapPointer> is necessary.`)
        }

        // arrow
        let $arrow = document.createElement('img');
        $arrow.src = this.__image_arrow_src__;
        $arrow.srcset = this.__image_arrow_src_2x__;
        $arrow.classList.add('arrow');
        this.$mapPointer.appendChild($arrow);
        this.$arrow = $arrow;
        if (this.$arrow == null) {
            console.warn(`<img class=arrow> is necessary in ${this.__id__}.`)
        }

        // select items container
        let $listMenu = document.createElement('ul');
        $listMenu.classList.add('listMenu');
        this.$mapPointer.appendChild($listMenu);
        this.$listMenu = $listMenu;
        if (this.$listMenu == null) {
            console.warn(`<ul class=listMenu> is necessary in ${this.__id__}.`)
        }

        // set items
        this._options.forEach((option) => {
            let $listItem = document.createElement('li');
            $listItem.classList.add('listItem');
            $listItem.dataset.value = option.value;
            $listItem.dataset.action = option.action;
            $listItem.innerHTML = option.title;
            this.$listMenu.appendChild($listItem);
        });

        // add to map
        const panes = this.getPanes();
        //panes.overlayLayer.appendChild(this.$mapPointer);
        panes.overlayMouseTarget.appendChild(this.$mapPointer);
        this.$mapPointer.classList.add('show');

        // set state
        this.state = MapPointerState.onshow;

        // set event handlers
        this._setEventHandlers();
    }

    /**
     * Draw the layer.
     * @description Called everytime when map is lendered.
     * (OverlayView class override)
    */
    draw() {
       // https://developers.google.com/maps/documentation/javascript/reference/overlay-view#MapCanvasProjection
       // *no need to resize according to zooming
       const overlayProjection = this.getProjection();
       const point = overlayProjection.fromLatLngToDivPixel(this._coordinate.latlng)
       this.$mapPointer.style.left = point.x + 'px';
       this.$mapPointer.style.top = point.y + 'px';
    }
   
    /**
     * Cleanup.
     * @description Called when this layer is removed by this.setMap(null).
     * (OverlayView class override)
    */
    onRemove() {
        if (this.$mapPointer) {
          this.$mapPointer.parentNode.removeChild(this.$mapPointer);
          delete this.$mapPointer;
          delete this
        }
    }

    /**
     * Set event handlers.
     */
    _setEventHandlers() {
        const _this = this;
        //this.$listMenu.addEventListener('mouseover', (e) => {
        //    _this.state = MapPointerState.onhover;
        //})
        //this.$listMenu.addEventListener('mouseout', (e) => {
        //    _this.state = MapPointerState.onshow;
        //})
        this.$listMenu.addEventListener('click', (e) => {
            if (this.state == MapPointerState.onshow || this.state == MapPointerState.onhover) {
                console.log(this.$listMenu.querySelector(':hover'));
                console.table(this.$listMenu.querySelector(':hover').dataset);
                const value = this.$listMenu.querySelector(':hover').dataset.value;
                const action = parseInt(this.$listMenu.querySelector(':hover').dataset.action);
                console.log(`selected value: ${value} action ${action}`);
                this._value = value;
                this._action = action;
                switch (action) {
                    case MapPointerAction.close:
                        _this.state = MapPointerState.onclosestart;
                        break
                    case MapPointerAction.selectAndClose:
                        _this.state = MapPointerState.onclosestart;
                        break
                }
            } else {
                console.log(`${this.__id__} is busy. nothing happens.`);
            }
        })
    }

    /**
     * Close this view component.
     */
    _close() {
        console.log(`${this.__id__} close function called.`);
        let _this = this;
        const interval = 1000;
        let timeOutID;
        // start animation
        this.$mapPointer.classList.add('close');
        timeOutID = window.setTimeout(()=>{
            // set state
            _this.state = MapPointerState.onclosecomplete;
            // remove from map
            if (this.getMap()) {this.setMap(null);}
        }, interval);
    }
}

