'use strict'
/**
 * @fileoverview business/view_controllers/position_map.js
 * PositionMap view component.
 * 
 * This UI component allows us to make a map where we can point a location.
 * 
 * @author kaz@thinkxinc.com (Kazuki Otsuka)
 **/


/**
 * Global Google map object.
 */
let map;

/**
 * Global map pointer object.
 */
let mapPointer;
let settings = {
    'defaultMapCoordinate': null,
    'defaultPointerCoordinate': null,
    'pointerLabel': null,
    'mapTypeControl': null,
    'streetViewControl': null,
    'fullScreenControl': null,
}

/**
 * PositionMap component class
 * @constructor
 * @classdesc `<div id={id} class=positionMap>` is necessary in HTML.
 * usage:
 * `<code>`
 *     itemPositionMap = new PositionMap(
 *         'ItemPositionMap',
 *         new Coordinate(lat, lng),
 *         new Coordinate(lat, lng),
 *         'Here is your home',
 *      )
 * `</code>`
 * 
 * html:
 * <div id={id} class=positionMap>
 *    <div class=positionMapContainer>
 *        <div id=map></div>
 *        <p id=positionMapCoordinate></p>
 *        <p id=positionMapAddress></p>
 * 
 *        <input id=positionMapInputLat name=maplat hidden/>
 *        <input id=positionMapInputLng name=maplng hidden/>
 *        <input id=positionMapInputProvince name=mapprovince hidden/>
 *        <input id=positionMapInputCity name=mapcity hidden/>
 *        <input id=positionMapInputArea name=mapparea hidden/>
 *    </div>
 * </div>
 *
 * @param {string} _id - The DOM id where this view is inserted.
 * @param {string} fieldNameLat - storing field name in values
 * @param {string} fieldNameLng - storing field name in values
 * @param {Coordinate} defaultMapCoordinate - default map center coordinate
 * @param {Coordinate} defaultPointerCoordinate - default pin coordinate
 * @param {string} _label - pointer text label.
 * @param {bool} mapTypeControl - if true, (Map|Satellite) menu appears
 * @param {bool} streetViewControl - if true, Pegman icon menu appears
 * @param {bool} fullScreenControl - if true, Pegman icon menu appears
 */
class PositionMap {
    __id__;
    __field_name_lat__;
    __field_name_lng__;

    //_googlemapSource = `<script src='https://maps.googleapis.com/maps/api/js?key=${app.config.GOOGLEMAP_API_KEY}&callback=initMap' async defer></script>`

    _mapCoordinate;
    _pointerCoordinate;
    _label;

    constructor(
            id, fieldNameLat, fieldNameLng,
            defaultMapCoordinate, defaultPointerCoordinate, label,
            mapTypeControl = false, streetViewControl = false,
            fullScreenControl = false) {
        this.__id__ = id;
        this.__field_name_lat__ = fieldNameLat;
        this.__field_name_lng__ = fieldNameLng;
        this._label = label;

        // set map center coordinate
        this._mapCoordinate = defaultMapCoordinate;
        if (typeof this._mapCoordinate !== "object") {
            console.error(`mapCoordinate of ${this.__id__} must be type of Coordinate. but ${typeof latLng}`);
        }
        // set default pin coordinate
        this._pointerCoordinate = defaultPointerCoordinate;
        if (typeof this._pointerCoordinate !== "object") {
            console.error(`pointerCoordinate of ${this.__id__} must be type of Coordinate. but ${typeof latLng}`);
        }

        // create default pin
        /**
        NOTE: TypeError: MapPointer is not a constructor

        mapPointer = new MapPointer(
            'positionMapPointer',
            defaultPointerCoordinate.latLng,
            [
                new MapPointerOption(
                    label, '-', MapPointerAction.show)
            ]
        )
        */
        settings.defaultMapCoordinate = defaultMapCoordinate;
        settings.defaultPointerCoordinate = defaultPointerCoordinate;
        settings.pointerLabel = label;
        settings.mapTypeControl = mapTypeControl;
        settings.streetViewControl = streetViewControl;
        settings.fullScreenControl = fullScreenControl;

        // set elements
        this._setElements();
        // set events
        this._setEventHandlers();
    }

    /**
     * mapCoordinate setter.
     */
    set mapCoordinate(mapCoordinate) {
        const previousState = this._mapCoordinate;
        this._mapCoordinate = mapCoordinate;
        console.log(`${this.__id__}.mapCoordinate updated`)
        // reset center position
        if (window.map != null) {
            window.map.setCenter(mapCoordinate.latlng)
        } else {
            // no map object when cookie is restored
            console.log('update defaultMapCoordinate.')
            settings.defaultMapCoordinate = mapCoordinate
        }
    }

    /**
     * mapCoordinate getter.
     */
    get mapCoordinate() {return this._mapCoordinate;}


    /**
     * pointerCoordinate setter.
     */
    set pointerCoordinate(pointerCoordinate) {
        const previousState = this._pointerCoordinate;
        this._pointerCoordinate = pointerCoordinate;
        console.log(`${this.__id__}.pointerCoordinate updated`)

        if (window.map != null) {

            // dispatch pointer coordinate update event
            const event = new CustomEvent(
                'pointerCoordinateUpdated', {
                    detail: {
                        id: this.__id__,
                        coordinate: pointerCoordinate
                    }});
            this.$positionMap.dispatchEvent(event);
 
        } else {
            // no map object when cookie is restored
            console.log('update defaultPointerCoordinate.')
            settings.defaultPointerCoordinate = pointerCoordinate
        }
    }

    /**
     * pointerCoordinate getter.
     */
    get pointerCoordinate() {return this._pointerCoordinate;}



    /**
     * DOM nodes as variables.
     */
    _setElements() {
        this.$positionMap = document.getElementById(this.__id__);
        if (this.$positionMap == null) {
            console.warn(
                `<div id=${this.__id__} class=positionMap></div> is necessary in HTML.`);
        }
 
        // google map element
        let $map = document.createElement('div');
        $map.id = 'map';
        this.$positionMap.appendChild($map);
        this.$map = $map;

        // display coordinate
        let $coordinate = document.createElement('p');
        $coordinate.classList.add('positionMapCoordinate');
        this.$positionMap.appendChild($coordinate);
        this.$coordinate = $coordinate;

        // display address
        let $address = document.createElement('p');
        $address.classList.add('positionMapAddress');
        this.$positionMap.appendChild($address);
        this.$address = $address;

        // input lat/lng/city/province/area
        let $inputLat = document.createElement('input');
        let $inputLng = document.createElement('input');
        let $inputProvince = document.createElement('input');
        let $inputCity = document.createElement('input');
        let $inputArea = document.createElement('input');
        $inputLat.name = 'mapLat';
        $inputLng.name = 'mapLng';
        $inputProvince.name = 'mapProvince';
        $inputCity.name = 'mapCity';
        $inputArea.name = 'mapArea';
        $inputLat.type = 'text';
        $inputLng.type = 'text';
        $inputProvince.type = 'text';
        $inputCity.type = 'text';
        $inputArea.type = 'text';
        $inputLat.setAttribute('type', 'hidden');
        $inputLng.setAttribute('type', 'hidden');
        $inputProvince.setAttribute('type', 'hidden');
        $inputCity.setAttribute('type', 'hidden');
        $inputArea.setAttribute('type', 'hidden');
        this.$positionMap.appendChild($inputLat);
        this.$positionMap.appendChild($inputLng);
        this.$positionMap.appendChild($inputProvince);
        this.$positionMap.appendChild($inputCity);
        this.$positionMap.appendChild($inputArea);
    }

    /**
     * Update MapPointer
     *
     * @param {Coordinate} coordinate 
     */
    updateMapPointer(coordinate) {
        renewMapPointer(coordinate, settings.pointerLabel)
    }

    /**
     * Set event handlers.
     */
    _setEventHandlers() {
        const _this = this;

        // new mapPointer is created when this positionMap is clicked
        document.addEventListener('positionMapPointerCoordinateUpdated', 
            (event) => {
                console.log(`positionMapPointerCoordinateUpdated event listened in ${_this.__id__}`)
                const mapPointerId = event.detail.__id__;
                const newCoordinate = event.detail.coordinate; 
                // update pointerCoordinate
                this.pointerCoordinate = newCoordinate;
            }
        )
    }
}


 /**
 * Initialize view from Google Map API Callback function.
 * 
 * This function is called firstly after googlemap canvas was setup.
 */
function initMap() {
    console.log('initialize google map');

    // TODO: use organization's default center
    // center: {lat: 35.6603976, lng: 139.7292361},
    // const lat = 48.6358 // roppongi
    // const lon = -1.511  // roppongi
    const lat = 46.943986; // bern
    const lng = 7.426123; // bern
    const zoom = 14;

    // initialize google map by center and zoom
    map = new google.maps.Map(document.getElementById('map'), {
        center: settings.defaultMapCoordinate.latlng,
        zoom: zoom,
        mapTypeControl: settings.mapTypeControl,
        streetViewControl: settings.streetViewControl,
        fullScreenControl: settings.fullScreenControl
    });
    window.map = map;

    // set map custom layers
    // Custom layer classes need to be defined after google.map is loaded.
    // Since import('/path') is unavailable, dynamically create the <script>.
    let script_1 = document.createElement('script');
    script_1.src = '/js/business/view_components/map_pointer.js';
    document.getElementById('content').appendChild(script_1);
    script_1.onload = ()=> {
        // add map pointer
        addMapPointer(
            settings.defaultPointerCoordinate,
            settings.pointerLabel);
        // map components
        // observe map events
        map.addListener('click', (event) => {
            const newLatLng = event.latLng;
            const newCoordinate = new Coordinate.initFromLatLng(newLatLng);
            console.log(`map clicked at ${newLatLng}`)
            if (mapPointer 
                && (mapPointer.state == MapPointerState.onhide)) {
                // soon after selected. do nothing .
            } else if (mapPointer
                && (mapPointer.state == MapPointerState.onshow)) {
                // close old & create new mapPointer
                renewMapPointer(
                    newCoordinate,
                    settings.pointerLabel);
                // dispatch pointer coordinate update event
                const event = new CustomEvent(
                    'positionMapPointerCoordinateUpdated', {
                        detail: {
                            id: mapPointer.__id__,
                            coordinate: newCoordinate
                        }});
                document.dispatchEvent(event);
            } else if (mapPointer
                && (mapPointer.state == MapPointerState.onclosecomplete)) {
                // no pointer. create new.
            } else if (mapPointer == null) {
                // no pointer. create new.
            } else {
                console.error('unkown state');
            }
        });
        map.addListener('dblclick', (event) => {
            // TODO: if needed
        });
    }
}
 
/**
 * Add new MapPointer.
 */
function addMapPointer(coordinate, label) {
    // create new map pointer
    console.log(
        `create new mapPointer with coordinate ${coordinate.lat} ${coordinate.lng}`)
    mapPointer = new MapPointer(
        'positionMapPointer', 
        coordinate,
        [new MapPointerOption(
            label, '-', MapPointerAction.show)]
    )
    mapPointer.state = MapPointerState.onshow;
    mapPointer.setMap(map);
}

/**
 *  Renew MapPointer.
 */
function renewMapPointer(coordinate, label) {
    // close old map pointer
    if (mapPointer) {
        mapPointer.state = MapPointerState.onclosestart;
    }
    // create new mappointer
    addMapPointer(coordinate, label)
}

/**
 * Update input form data
 * 
 * update these data:
 *  - lat (fieldName: maplat)
 *  - lng (fieldName: maplng)
 *  - province (fieldName: mapprovince)
 *  - city (fieldName: mapcity)
 *  - area (fieldName: maparea)
 */
function updateData(latLng) {
    // fetch adress via google map reverse geocoding API


}
