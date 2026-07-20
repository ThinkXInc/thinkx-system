'use strict'
/**
 * @fileoverview business/models/session_model.js
 * Session model parent class.
 * 
 * @author kaz@thinkxinc.com (Kazuki Otsuka)
 */

class SessionModel {

    /**
     * Initialize object from <input type=hidden /> session syncronization elements.
     * 
     * @public
     * 
     * @param {String} modelName 
     * @returns {Object} ModelClass instance
     */
    static load(modelName) {
        let d = {}
        document.querySelectorAll(`input[model=${modelName}`).forEach((elem) => {
          d[elem.id] = elem.value;
        })
        return Object.assign(d, this)
    }
}


