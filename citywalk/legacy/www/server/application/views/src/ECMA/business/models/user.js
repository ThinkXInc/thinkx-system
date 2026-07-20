'use strict'
/**
 * @fileoverview business/models/user.js
 * User data model class.
 * 
 * <code>
 * 
 * usage:
 *   var user = User({
 *       _id: 'abcdefgh',
 *       ...
 *   });
 * 
 * functions:
 *   - validate()
 *       params:
 *       returns:
 *         {bool} - true if valid
 * 
 * </code>
 * 
 * @author kaz@thinkxinc.com (Kazuki Otsuka)
 */


/**
 * User Data Model.
 * @param {string} _id -
 * @param {string} user_id - 
 * @param {string} email -
 * @param {string} last_name -
 * @param {string} first_name -
 * @param {string} gender -  
 * @param {string} birth -  
 * @param {string} nationality -  
 * @param {string} language -  
 * @param {string} zipcode -  
 * @param {string} country -  
 * @param {string} city -  
 * @param {string} province -  
 * @param {string} address1 -  
 * @param {string} address2 -  
 * @param {string} tel1 -  
 * @param {string} tel2 -  
 * @param {string} tel3 -  
 */
class User {
    _id = null

    user_id = null
    email = null
    first_name = null
    last_name = null
    gender = null
    birth = null  // TODO: datetime.date
    nationality = null
    language = null

    zipcode = null
    country = null
    city = null
    province = null
    address1 = null
    address2 = null
    tel1 = null
    tel2 = null
    tel3 = null

    constructor(
        _id, user_id,
        email, first_name, last_name,
        gender, birth, nationality, language,
        zipcode, country, city, province, address1, address2,
        tel1, tel2, tel3) {
            this._id = _id;
            this.user_id = user_id;
            this.email = email;
            this.first_name = first_name;
            this.last_name = last_name;
            this.gender = gender;
            this.birth = birth; // TODO: 
            this.nationality = nationality;
            this.language = language;
            this.zipcode = zipcode;
            this.country = country;
            this.city = city;
            this.province = province;
            this.address1 = address1;
            this.address2 = address2;
            this.tel1 = tel1;
            this.tel2 = tel2;
            this.tel3 = tel3;
    }

    /**
    * Minimum validation.
    * @param
    * @return {bool} true if valid.
    */
    validate() {

    }
}