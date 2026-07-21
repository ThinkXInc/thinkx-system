'use strict'
/**
 * @fileoverview business/models/content.js
 * Content data model class.
 * 
 * <code>
 * 
 * usage:
 *   var content = Content({
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
 * ContentType Enum.
 */
const ContentType = Object.freeze({
  audio_guide: 0,
  video: 1,
  others: 99,
});


/**
 * Content Data Model.
 * @param {string} _id -
 * @param {int} index -  
 * @param {string} type -  
 * @param {float} lat -  
 * @param {float} lon -  
 * @param {string} label -
 * @param {string} title -
 * @param {string} text -  
 * @param {string} resource_key -  
 * @param {string} image_key -  
 * @param {string} language -  
 * @param {string} organization_id -  
 * @param {dictionary} condition -  
 * @param {bool} featured -  
 * @param {int} importance -  
 * @param {string} created_member_id -  
 * @param {string} latest_edit_member_id -  
 * @param {bool} deleted -  
 */
class Content {
    _id = null
    index = null  
    type = null
    lat = null
    lon = null
    label = null
    title = null
    text = null
    resource_key = null
    image_key = null
    language = null
    organization_id = null
    target = null
    radius = null
    condition = null
    featured = null
    importance = null
    created_member_id = null
    latest_edit_member_id = null
    deleted = null
 
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
            this._id = _id;
            this.index = index;
            this.type = type;
            this.lat = lat;
            this.lon = lon;
            this.label = label;
            this.title = title;
            this.text = text;
            this.resource_key = resource_key;
            this.image_key = image_key;
            this.language = language;
            this.organization_id = organization_id;
            this.target = target
            this.radius = radius
            this.condition = condition;
            this.featured = featured;
            this.importance = importance;
            this.created_member_id = created_member_id;
            this.latest_edit_member_id = latest_edit_member_id;
            this.deleted = deleted;
   }

   static initFromJson(content) {
     // MEMO: somehow unable to set like _id=content._id in request callback.
     return new Content(
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
    * Minimum validation.
    * @param
    * @return {bool} true if valid.
    */
    validate() {

    }
}