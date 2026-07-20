'use strict'
/**
 * @fileoverview business/models/content.js
 * Content data model class.
 * 
 * <code>
 * 
 * usage:
 *   var editingContent = new EditingContent({
 *       _id: 'abcdefgh',
 *       ...
 *   });
 * 
 *   var editingContent = EditingContent.fromContent(content);
 
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


class EditingContent extends Content {

    _saved = null;  // bool

    constructor(
        _id, index, type,
        lat, lon,
        label, title, text,
        resource_key, image_key, language,
        organization_id,
        target, radius,
        condition, featured, importance, 
        created_member_id, latest_edit_member_id, deleted
        ) {
        super(_id, index, type,
        lat, lon,
        label, title, text,
        resource_key, image_key, language,
        organization_id,
        target, radius,
        condition, featured, importance, 
        created_member_id, latest_edit_member_id, deleted);
    }

    static fromContent(content) {
     return new EditingContent(
       (content._id != null) ? content._id : null,
       (content.index != null) ? content.index : null,
       (content.type != null) ? content.type : null,
       (content.lat != null) ? content.lat : null,
       (content.lon != null) ? content.lon : null,
       (content.label != null) ? content.label : null,
       (content.title != null) ? content.title : null,
       (content.text != null) ? content.text : null,
       (content.resource_key != null) ? content.resource_key : null,
       (content.image_key != null) ? content.image_key : null,
       (content.language != null) ? content.language : null,
       (content.organization_id != null) ? content.organization_id : null,
       (content.target != null) ? content.target : null,
       (content.radius != null) ? content.radius : null,
       (content.condition != null) ? content.condition : null,
       (content.featured != null) ? content.featured : null,
       (content.importance != null) ? content.importance : null,
       (content.created_member_id != null) ? content.created_member_id : null,
       (content.latest_edit_member_id != null) ? content.latest_edit_member_id : null,
       (content.deleted != null) ? content.deleted : null,
     )
   }

   /**
    * Check if all null.
    * @returns {bool} isEmpty - true if all properties are null
    */
   isEmpty() {
       const vals = Object.keys(this).map(key => this[key]);
       return vals.every(val => val === null)
   }

}