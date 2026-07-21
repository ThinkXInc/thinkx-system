'use strict'
/**
 * @fileoverview business/view_components/map_balloon.js
 * MapBalloon view component class.
 * 
 * usage:
 * <code>
 * </code>
 * 
 * @author kaz@thinkxinc.com (Kazuki Otsuka)
 */


/**
 * MapBalloon State Enum.
 */
const MapBalloonState = Object.freeze({
    onhide: 0,
    onshow: 1,
    onfocus: 2,
    onclosestart: 4,
    onclosecomplete: 5,
});


/**
 * MapBalloon component class.
 * @constructor
 * @classdesc 
 * usage:
 * `<code>`
 * `</code>`
 * @param {string} id - The DOM id where this view is set.
 */
class MapBalloon extends google.maps.OverlayView {
    __id__ = null;

    __template_sample__ = `
    <div id=$id class=mapBalloon>
        <img class=dot src=/img/parts/map_balloon_dot.png srcset="/img/parts/map__balloon_dot@2x.png"/>
        <div class=balloon>
            <span class=title>$title</span>
            <p class=text>$text</p>
        </div>
    </div>
    `
    //__image_dot_src__ = '/img/parts/map_balloon_dot.png';
    //__image_dot_src_2x__ = '/img/parts/map_balloon_dot@2x.png';
    //__image_balloon_src__ = '/img/parts/map_balloon.png';
    //__image_balloon_src_2x__ = '/img/parts/map_balloon@2x.png';
    __image_balloonleg_src__ = '/img/parts/balloon_leg.png';
    __image_balloonleg_src_2x__ = '/img/parts/balloon_leg@2x.png';

    // data
    _latLng = null;
    _state = MapBalloonState.onhide;
    _title = null;
    _text = null;

    constructor(id, latLng, title, text) {
        super();
        console.log(
            `create new MapBalloon
            id: ${id}
            latLng: ${latLng}
            title: ${title}
            text: ${text}
            `)
        // set veiw id
        this.__id__ = id;
        // set data
        this._latLng = latLng;
        this._title = title;
        this._text = text;
        if (typeof latLng !== "object") {
            console.error(`latLng of ${this.__id__} must be type of google.maps.LatLng . but ${typeof latLng}`);
        }
        if (typeof title !== "string") {
            console.error(`title of ${this.__id__} must be type of string . but ${typeof title}`);
        }
        if (typeof text !== "string") {
            console.error(`text of ${this.__id__} must be type of string . but ${typeof text}`);
        }
    }

    /**
     * text setter.
     */
    set text(text) {
        this._text = text;
        console.log(`text updated: ${text}`);
        // set text
        this.$text.innerText = text;
        // dispatch event
        const event = new CustomEvent('textupdated', {detail: {new: text, id: this.__id__}});
        this.$mapBalloon.dispatchEvent(event);
    }

    /**
     * text getter.
     */
    get text() {return this._text;}

    /**
     * title setter.
     */
    set title(title) {
        this._title = title;
        console.log(`title updated: ${title}`);
        // set title
        this.$title.innerText = title;
        // dispatch event
        const event = new CustomEvent('titleupdated', {detail: {new: title, id: this.__id__}});
        this.$mapBalloon.dispatchEvent(event);
    }

    /**
     * title getter.
     */
    get title() {return this._title;}

    /**
     * state setter.
     */
    set state(state) {
        const previousState = this._state;
        // unfocus
        if (this.$mapBalloon && previousState == MapBalloonState.onfocus) {
            this.$mapBalloon.classList.add('unfocus');
            this.$mapBalloon.classList.remove('focus');
        }
        this._state = state;
        switch (state) {
            case MapBalloonState.onhide:
                console.log(`MapBalloon ${this.__id__} state changed -> onhide`);
                break
            case MapBalloonState.onshow:
                console.log(`MapBalloon ${this.__id__} state changed -> onshow`);
                break
            case MapBalloonState.onfocus:
                console.log(`MapBalloon ${this.__id__} state changed -> onfocus`);
                // focus animation
                if (this.$mapBalloon) {
                    this.$mapBalloon.classList.remove('unfocus');
                    this.$mapBalloon.classList.add('focus');
                }
                break
             case MapBalloonState.onclosestart:
                console.log(`MapBalloon ${this.__id__} state changed -> onclosestart`);
                this._close();
                break
              case MapBalloonState.onclosecomplete:
                console.log(`MapBalloon ${this.__id__} state changed -> onclosecomplete`);
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
        this.state = MapBalloonState.onhide;
        // container element
        this.$mapBalloon = document.createElement('div');
        this.$mapBalloon.id = this.__id__;
        this.$mapBalloon.classList.add('mapBalloon');
        this.$mapBalloon.classList.add('hide');

        // dot
        let $dot = document.createElement('span');
        $dot.classList.add('dot');
        this.$mapBalloon.appendChild($dot);
        this.$dot = $dot;
        if (this.$dot == null) {
            console.warn(`<span class=dot> is necessary in ${this.__id__}.`)
        }

        // balloon
        let $balloon = document.createElement('div');
        $balloon.classList.add('balloon');
        this.$mapBalloon.appendChild($balloon);
        this.$balloon = $balloon;
        if (this.$balloon == null) {
            console.warn(`<div class=balloon> is necessary in ${this.__id__}.`)
        }

        // balloon leg
        let $balloonleg = document.createElement('img');
        $balloonleg.src = this.__image_balloonleg_src__;
        $balloonleg.srcset = this.__image_balloonleg_src_2x__;
        $balloonleg.classList.add('balloonleg');
        this.$balloon.appendChild($balloonleg);
        this.$balloonleg = $balloonleg;
        if (this.$balloonleg == null) {
            console.warn(`<ing class=balloonleg> is necessary in ${this.__id__}.`)
        }

        // title
        let $title = document.createElement('span');
        $title.classList.add('title');
        $title.innerText = this.title;
        this.$balloon.appendChild($title);
        this.$title = $title;

        // text
        let $text = document.createElement('p');
        $text.classList.add('text');
        $text.innerText = this.text;
        this.$balloon.appendChild($text);
        this.$text = $text;

        // add to map
        const panes = this.getPanes();
        //panes.overlayLayer.appendChild(this.$mapBalloon);
        panes.overlayMouseTarget.appendChild(this.$mapBalloon);
        this.$mapBalloon.classList.remove('hide');
        this.$mapBalloon.classList.add('show');

        // set state
        this.state = MapBalloonState.onshow;

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
       const point = overlayProjection.fromLatLngToDivPixel(this._latLng)
       this.$mapBalloon.style.left = point.x + 'px';
       this.$mapBalloon.style.top = point.y + 'px';
    }
   
    /**
     * Cleanup.
     * @description Called when this layer is removed by this.setMap(null).
     * (OverlayView class override)
    */
    onRemove() {
        if (this.$mapBalloon) {
          this.$mapBalloon.parentNode.removeChild(this.$mapBalloon);
          delete this.$mapBalloon;
          delete this
        }
    }

 
    /**
     * Set event handlers.
     */
    _setEventHandlers() {
        const _this = this;
        //this.$balloon.addEventListener('mouseover', (e) => {
        //    _this.state = MapBalloonState.onhover;
        //})
        //this.$balloon.addEventListener('mouseout', (e) => {
        //    _this.state = MapBalloonState.onshow;
        //})
    }

    /**
     * Close this view component.
     */
    _close() {
        console.log(`${this.__id__} close function called.`);
        var _this = this;
        const interval = 1000;
        // start animation
        this.$mapBalloon.classList.add('close');
        let timeOutID = window.setTimeout(()=>{
            // set state
            _this.state = MapBalloonState.onclosecomplete;
            // remove from map
            if (this.getMap()) {this.setMap(null);}
        }, interval);
    }
}

