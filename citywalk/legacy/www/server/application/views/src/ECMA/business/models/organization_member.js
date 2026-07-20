'use strict'
/**
 * @fileoverview business/models/organization_member.js
 * User data model class.
 * 
 * <code>
 * 
 * usage:
 *   var organization_member = OrganizationMember({
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
 * OrganzationMember Data Model.
 * @param {string} session_id - 
 * @param {string} organization_id -
 * @param {string} first_name -
 * @param {string} last_name -
 * @param {string} email -  
 * @param {string} role -  
 */
class OrganizationMember extends SessionModel {
    session_id = null
    organization_id = null
    email = null
    first_name = null
    last_name = null
    role = null

    //constructor(
    //    session_id, organization_id,
    //    first_name, last_name, email, 
    //    role) {
    //      if (session_id != "" && session_id != "/") {
    //        this.session_id = session_id;
    //      }
    //      if (organization_id != "" && organization_id != "/") {
    //        this.organization_id = organization_id;
    //      }
    //      if (first_name != "" && first_name != "/") {
    //        this.first_name = first_name;
    //      }
    //      if (last_name != "" && last_name != "/") {
    //        this.last_name = last_name;
    //      }
    //      if (email != "" && email != "/") {
    //        this.email = email;
    //      }
    //      if (role != "" && role != "/") {
    //        this.role = role;
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