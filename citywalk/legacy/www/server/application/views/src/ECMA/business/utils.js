'use strict'
/**
 * @fileoverview business/utils.js
 * A collection of utilities
 * @author kaz@thinkxinc.com (Kazuki Otsuka)
 */


/**
 * pythonic zip function
 * 
 * in: [[1,2,3], [10,20,30], [100,200,300]]
 * out: [[1,10,100], [2,20,200], [3,30,300]]
 * 
 * @param {2-dim array} arrays 
 * @returns {2-dim array}
 */
function zip(arrays) {
    return arrays[0].map(function(_,i){
        return arrays.map(function(array){return array[i]})
    });
}

