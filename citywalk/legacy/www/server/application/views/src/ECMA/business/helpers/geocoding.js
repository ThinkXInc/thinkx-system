'use strict'
/**
 * @fileoverview business/helpers/geocoding.js
 * Geocoding API helper functions.
 * 
 * @author kaz@thinkxinc.com (Kazuki Otsuka)
 */

/**
 * Request geocoding API (postal -> address).
 * @param {string} country - ISO 3166-1 two letter code
 * @param {string} zipcode - 1070052, 107-0052
 * @param {language} language
 * @param {callback function} onsuccess - called on seccess.
 * @param {callback function} onfailed - called on failed.
 */
function geocodePostalToAddress(country, zipcode, language, onsuccess, onfailed) {
    const params = {
        'key': app.config.GOOGLEMAP_API_KEY,
        'zipcode': zipcode,
        'country': country,
        'language': language,
    }
    const url = `https://maps.googleapis.com/maps/api/geocode/json?latlng=${params.latlng}&key=${params.key}`
    fetch(
        url,
        {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json; charset=UTF-8',
            }
        }
    )
    .then(response => response.json())
    .then(data => {
        console.info('fetch success:', data);
        onsuccess(data);
    })
    .catch((error) => {
        console.error('fetch error:', error);
        onfailed(error);
    })
}

/**
 * Request geocoding API (address -> latlng).
 * @param {string} country - ISO 3166-1 two letter code eg. JP
 * @param {string} province - eg. 東京都
 * @param {string} city - eg. 港区
 * @param {string} address1 - eg. 六本木7-7-7
 * @param {language} language - eg. (ja|en|fr|..)
 * @param {callback function} onsuccess - with data 
 * @param {callback function} onfailed - called on failed.
 */
function geocodeAddressToCoordinate(
    country, province, city, address1, onsuccess, onfailed) {
    const address = `${address1} ${city} ${province}`
    const params = {
        'key': app.config.GOOGLEMAP_API_KEY,
        'address': address,
        'country': country,
        //'language': language,  <- not affect (only designable when map src is loaded.)
    }
    console.log(`call geocoding API with parameters below`);
    console.log(params);

    const geocoder = new google.maps.Geocoder();
    geocoder.geocode(
        {'country': country, 'address': address},
        (results, status) => {
        if (status == 'OK') {
            console.log(`result of => ${results[0].formatted_address}`);
            console.log(results[0]);
            const latLng = results[0].geometry.location;
            console.log(`${latLng.lat()} ${latLng.lng()}`)
            const coordinate = new Coordinate(latLng.lat(), latLng.lng());
            onsuccess(coordinate);
        } else {
            console.error(
                'Geocode failed for the following reason: ' + status);
            onfailed(status);
        }
    })
    /*
    const url = `https://maps.googleapis.com/maps/api/geocode/json?country=${country}&address=${params.address}&language=${language}&key=${params.key}`
    fetch(
        url,
        {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json; charset=UTF-8',
                'Access-Control-Allow-Origin': '*',
                'Access-Contorl-Allow-Credentials': "true",
            }
        }
    )
    .then(response => response.json())
    .then(data => {
        console.info('fetch success:', data);
        onsuccess(data);
    })
    .catch((error) => {
        console.error('fetch error:', error);
        onfailed(error);
    })
    */
}

/**
 * Request reverse geocoding API (latlng -> address).
 * @param {string} country - ISO 3166-1 two letter code eg. JP
 * @param {latLng} latlng
 * @param {callback function} onsuccess - called on seccess.
 * @param {callback function} onfailed - called on failed.
 */
function geocodeCoordinateToAddress(latlng, language, onsuccess, onfailed) {
    const params = {
        'key': app.config.GOOGLEMAP_API_KEY,
        'country': country,
        'latlng': `${latlng.lat},${latlng.lng}`,
        'language': language,
        //'result_type': 
    }
    const url = `https://maps.googleapis.com/maps/api/geocode/json?latlng=${params.latlng}&key=${params.key}`
    fetch(
        url, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json; charset=UTF-8',
        }
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
}