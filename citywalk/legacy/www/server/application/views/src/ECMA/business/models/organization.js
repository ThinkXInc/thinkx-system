'use strict'
/**
 * @fileoverview business/models/organization.js
 * Organization data model class.
 * 
 * <code>
 * 
 * usage:
 *   var organization = Organization({
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
 * Organization Data Model.
 * @param {string} organization_id -
 * @param {string} name - 
 * @param {string} business_description -  
 * @param {string} type -
 * @param {string} country -  
 * @param {string} city -  
 * @param {string} province -  
 * @param {string} address1 -  
 * @param {string} address2 -  
 * @param {string} address_sid -  
 * @param {string} tel_country_code -  
 * @param {string} tel -  
 * @param {string} lat -  
 * @param {string} lng -  
 * @param {bool} is_authenticated -  
 */
class Organization extends SessionModel {
    organization_id = null

    name = null
    type = null
    business_description = null
    type = null
 
    country = null
    zipcode = null
    city = null
    province = null
    address1 = null
    address2 = null
    address_sid = null

    lat = null
    lng = null

    tel_country_code = null
    tel = null

    is_authenticated = null 

    //constructor(defaults = {}) {
    //  super(defaults);
    //  Object.assign(defaults, this);
    //}

    //constructor(
    //    organization_id,
    //    name, type, business_description,
    //    country, zipcode, city, province,
    //    address1, address2, address_sid,
    //    lat, lng, tel_country_code, tel) {
    //      if (organization_id != "" && organization_id != "/") {
    //        this.organization_id = organization_id;
    //      }
    //      if (name != "" && name != "/") {
    //        this.name = name;
    //      }
    //      if (type != "" && type != "/") {
    //        this.type = type;
    //      }
    //      if (business_description != "" && business_description != "/") {
    //        this.business_description = business_description;
    //      }
    //      if (country != "" && country != "/") {
    //        this.country = country;
    //      }
    //      if (zipcode != "" && zipcode != "/") {
    //        this.zipcode = zipcode;
    //      }
    //      if (city != "" && city != "/") {
    //        this.city = city;
    //      }
    //      if (province != "" && province != "/") {
    //        this.province = province;
    //      }
    //      if (address1 != "" && address1 != "/") {
    //        this.address1 = address1;
    //      }
    //      if (address2 != "" && address2 != "/") {
    //        this.address2 = address2;
    //      }
    //      if (address_sid != "" && address_sid != "/") {
    //        this.address_sid = address_sid;
    //      }
    //      if (tel_country_code != "" && tel_country_code != "/") {
    //        this.tel_country_code = tel_country_code;
    //      }
    //      if (tel != "" && tel != "/") {
    //        this.tel = tel;
    //      }
    //      if (lat != "" && lat != "/") {
    //        this.lat = lat;
    //      }
    //      if (lng != "" && lng != "/") {
    //        this.lng = lng;
    //      }
    //}

    /**
    * Minimum validation.
    * @param
    * @return {bool} true if valid.
    */
    validate() {

    }
}