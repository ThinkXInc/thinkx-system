'use strict'
/**
 * @fileoverview business/appconfig.js
 * A collection of app configurations 
 * @author kaz@thinkxinc.com (Kazuki Otsuka)
 */

/**
 * The global name space.
 * 
 */
let app = {};

/**
 * The global data storage.
 * 
 */
app.data = {};

/**
 * The global session storage.
 * 
 */
app.session = {};

/**
 * Debug level
 */
const DebugLevel = Object.freeze({
    DEBUG: 0,
    INFO: 1,
    WARN: 2,
    ERROR: 3
})

const DEBUG_LEVEL = DebugLevel.INFO;
const IS_DEBUG = (DEBUG_LEVEL == DebugLevel.DEBUG) ? true : false;

/**
 * Configurations
 */
const ENV = 'local';

app.config = {
    env: ENV,
    host: (ENV == 'local') ? 'http://citywalkservers.localhost:8000' : 'https://citywalk.app',
    defaultLang: "en",
    GOOGLEMAP_API_KEY: 'AIzaSyArpYMqJmFKUJlpdv90ZGwQZ0aOIL-O5VI'
};

app.routes = {
    SIGNUP: "/organizations/signup",
    SIGNUP_CONFIRM: "/organizations/signup/confirm",
}