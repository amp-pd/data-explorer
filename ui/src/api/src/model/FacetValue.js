/* eslint-disable */
/**
 * Data Explorer Service
 * API Service that reads from Elasticsearch.
 *
 * OpenAPI spec version: 0.0.1
 *
 *
 * NOTE: This class is auto generated by the swagger code generator program.
 * https://github.com/swagger-api/swagger-codegen.git
 * Do not edit the class manually.
 *
 */

import ApiClient from "../ApiClient";

/**
 * The FacetValue model module.
 * @module model/FacetValue
 * @version 0.0.1
 */
export default class FacetValue {
  /**
   * Constructs a new <code>FacetValue</code>.
   * A facet value, for example, \&quot;Male\&quot;/34.
   * @alias module:model/FacetValue
   * @class
   */

  constructor() {}

  /**
   * Constructs a <code>FacetValue</code> from a plain JavaScript object, optionally creating a new instance.
   * Copies all relevant properties from <code>data</code> to <code>obj</code> if supplied or a new instance if not.
   * @param {Object} data The plain JavaScript object bearing properties of interest.
   * @param {module:model/FacetValue} obj Optional instance to populate.
   * @return {module:model/FacetValue} The populated <code>FacetValue</code> instance.
   */
  static constructFromObject(data, obj) {
    if (data) {
      obj = obj || new FacetValue();

      if (data.hasOwnProperty("name")) {
        obj["name"] = ApiClient.convertToType(data["name"], "String");
      }
      if (data.hasOwnProperty("count")) {
        obj["count"] = ApiClient.convertToType(data["count"], "Number");
      }
    }
    return obj;
  }

  /**
   * Facet value name, for example, \"Male\".
   * @member {String} name
   */
  name = undefined;
  /**
   * Facet value count.
   * @member {Number} count
   */
  count = undefined;
}
