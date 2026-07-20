'use strict'
/**
 * @fileoverview business/helpers/pagecontrol.js
 * Browswer control class.
 * 
 * @author kaz@thinkxinc.com (Kazuki Otsuka)
 */


class PageControl {
    /**
     * TODO:
     *  create global PageControl class that can use like Browswer.getUrl()
     */

    constructor() {
    }

    /**
     * Syncronously move page.
     * 
     * @param {String} relativePath 
     */
    static goTo(relativePath) {
        window.location = relativePath;
    }


    /**
     * Update url in address bar.
     * 
     * @public
     * @param {string} path /path/to?key1=val1&key2=val2 or #key=val
     * @param {bool} withHTML whether to push the current html and title into history.
     */
    static pushHistoryState(path, withHTML=true) {
        let htmlState = null;
        if (withHTML) {
            const html = this.getHTML();
            const title = document.title;
            htmlState = {"html": html, "pageTitle": title};
        }
        window.history.pushState(htmlState, "", path);
    }

    /**
     * Get html in <content>.
     * 
     * @returns {string} html in <document><content>
     */
    static getHTML() {
        const html = document.getElementById('content').innerHTML;
        return html
    }

    /**
     * Get search params string.
     * 
     * @returns {string} ?key1=value1&key2=value2
     */
    static getSearchParamsString() {
        return window.location.search;
    }

    /**
     * Get relative path string.
     * 
     * @param {bool} withSearchParams whether to include search params
     * @param {bool} withHash whether to include hash string
     * @returns {string} /path/to?key1=val1&key2=val2#fragment
     */
    static getRelativePath(withSearchParams=true, withHash=true) {
        let searchParams = new URLSearchParams(window.location.search);
        return `${window.location.pathname}?${searchParams.toString()}${window.location.hash}`;
    }

    /**
     * Get href string
     * 
     * @returns {string} https://domain.com/path/to?key1=val1&key2=val2
     */
    static getUrl() {
        return window.location.href;
    }

    /**
     * Get host string
     * 
     * @param withPort whether to add port number like :0000
     * @returns {string} https://domain.com/path/to?key1=val1&key2=val2
     */
    static getHost(withPort=true) {
        if (withPort) {
            // domain.com:8000
            return window.location.host
        } else {
            // domain.com
            return window.location.hostname
        }
    }

    /**
     * Get value from search params string /path/to?key=value.
     * 
     * @param {string} key 
     * @param {string} type  {'string', 'int', 'float'}
     * @returns {string/number} value according to the designated type. null if not in url.
     */
    static getValueFromSearchParams(key, type = 'string') {
        const searchstring = window.location.search;
        console.log(`get value of ${key} in ${searchstring}`);
        const params = new Proxy(new URLSearchParams(searchstring), {
            get: (searchParams, prop) => searchParams.get(prop),
        })
        return this._getValueFromParams(key, type, params);
    }

    /**
     * Update value in query string /path/to?key=value.
     * 
     * @param {string} key target key
     * @param {string} value new value
     * @returns {string} new url string
     */
    static updateValueInSearchParams(key, value, withHTML=true) {
        let searchParams = new URLSearchParams(window.location.search);
        searchParams.set(key, value);
        const newRelativePath = `${window.location.pathname}?${searchParams.toString()}`;
        this.pushHistoryState(newRelativePath, withHTML);
    }

    /**
     * Get value from hash string /path/to?key1=val1#key2=val2
     * 
     * @param {string} key 
     * @param {string} type  {'string', 'int', 'float'}
     * @returns {string/number} value according to the designated type. null if not in url.
     */
    static getValueFromHash(key, type = 'string') {
        const searchstring = window.location.hash;
        console.log(`get value of ${key} in ${searchstring}`);
        const params = new Proxy(new URLSearchParams(searchstring.replace("#", "?")), {
            get: (searchParams, prop) => searchParams.get(prop),
        })
        return this._getValueFromParams(key, type, params);
    }

    /**
     * Update value in hash string /path/to?key1=val1#key2=val2
     * 
     * @param {string} key 
     * @param {string} value 
     * @param {boolean} withHTML 
     */
    static updateValueInHash(key, value, withHTML=false) {
        // TODO: decoldeURI(location.hash))
        let hash = window.location.hash.replace('#', '');
        let keyVals;
        if (hash == '') {
            keyVals = [];
        } else {
            keyVals = hash.split('&');
        }
        let newhash = '';
        let foundInHash = false;
        console.log(`update hash ${hash} with key:${key} val:${value}`);
        keyVals.forEach((keyval, i) => {
            const _key = keyval.split('=')[0];
            const _val = keyval.split('=')[1];
            if (_key == key) {
                foundInHash = true;
                if (i == 0) {
                    newhash = `${_key}=${value}`;
                } else {
                    newhash = `${newhash}&${_key}=${value}`;
                }
            } else {
                if (i == 0) {
                    newhash = `${_key}=${_val}`;
                } else {
                    newhash = `${newhash}&${_key}=${_val}`;
                }
            }
        })
        console.log(`check ${newhash} ${newhash.length}`);
        if (!foundInHash) {
            if (newhash.length > 0) {
                newhash = `${newhash}&${key}=${value}`
            } else {
                newhash = `${key}=${value}`;
            }
        }
        newhash = `#${newhash}`;
        this.pushHistoryState(newhash, withHTML);
        console.log(`hash string updated #${hash} -> ${newhash}`);
    }

    /**
     * Get value from params dict.
     * 
     * @param {string} key 
     * @param {string} type  {'string', 'int', 'float'}
     * @param {dict} params {key: value} dictionary
     * @returns {string/number} value according to the designated type. null if not in url.
 
     */
    _getValueFromParams(key, type = 'string', params) {
        if (params[key] == null) {
            console.error(`${key} not in the url query string.`);
        }
        console.log(`found ${key} in params. the value is ${params[key]}.`);
        switch (type) {
            case 'string':
                return params[key];
                break
            case 'int':
                return parseInt(params[key]);
                break
            case 'float':
                return parseFloat(params[key]);
                break
            default:
                console.error(`${type} is unrecognized type to read query strings.`);
                return null;
        }
    }
}