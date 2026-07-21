'use strict'
/**
 * @fileoverview business/models.js
 * Widely used data model definitions
 * @author kaz@thinkxinc.com (Kazuki Otsuka)
 */


/**
 * Coordinate Data class.
 * @param {float} lat - eg. 134.533323
 * @param {float} lng - eg. -32.232545
 */
class Coordinate {
    lat = null;
    lng = null;
    constructor(lat, lng) {
        this.lat = lat;
        this.lng = lng;
    }

    static initFromLatLng(latLng) {
        return new Coordinate(latLng.lat(), latLng.lng())
    }

    /**
     * Returns Google Map API LatLng format.
     * @returns {google.maps.LatLng} - eg. {lat: 141.314, lng: -12.553} 
     */
    get latlng() {
        return new google.maps.LatLng(this.lat, this.lng);
    }
}

