/**
 * ajv-backed SchemaValidator factory.
 *
 * Replaces the jsonschema + `_minimal_schema_check` fallback from
 * cartridge_runtime.py with a full JSON Schema 2020-12 validator.
 *
 * Usage:
 *   const validator = await makeValidatorForCartridge("cooking", schemaFiles);
 *   blackboard = new Blackboard(validator);
 *   blackboard.put("weekly_menu", data, { schema_ref: "weekly_menu.schema.json" });
 */

import Ajv2020, { type ValidateFunction } from "ajv/dist/2020.js";
import addFormats from "ajv-formats";
// Draft-07 meta-schema — several cooking/* and residential-electrical/* schemas
// declare `$schema: http://json-schema.org/draft-07/schema#`.
import draft07Meta from "ajv/dist/refs/json-schema-draft-07.json" with { type: "json" };
import type { SchemaValidator, ValidationResult } from "./types";

export interface SchemaFile {
  /** Filename under cartridges/<name>/schemas/, e.g. "weekly_menu.schema.json" */
  ref: string;
  /** Parsed JSON Schema object */
  schema: Record<string, unknown>;
}

export function makeValidatorForCartridge(
  cartridgeName: string,
  schemas: SchemaFile[],
): SchemaValidator {
  const ajv = new Ajv2020({ allErrors: false, strict: false });
  // Accept draft-07 dialect as well as 2020-12.
  if (!ajv.getSchema("http://json-schema.org/draft-07/schema#")) {
    ajv.addMetaSchema(draft07Meta as object);
  }
  addFormats(ajv as unknown as Parameters<typeof addFormats>[0]);

  // Register every schema by (a) its intrinsic $id if present, and (b) a
  // cartridge-scoped synthetic id so inter-schema $ref can target either form.
  const compiled = new Map<string, ValidateFunction>();
  for (const s of schemas) {
    const synthId = `skillos://${cartridgeName}/${s.ref}`;
    const schema = { ...s.schema };
    if (!schema.$id) schema.$id = synthId;
    ajv.addSchema(schema as object, synthId);
  }

  return (value: unknown, schemaRef: string): ValidationResult => {
    try {
      let fn = compiled.get(schemaRef);
      if (!fn) {
        const synthId = `skillos://${cartridgeName}/${schemaRef}`;
        const got = ajv.getSchema(synthId);
        if (!got) return { ok: true, message: `schema file missing: ${schemaRef}` };
        fn = got;
        compiled.set(schemaRef, fn);
      }
      const ok = fn(value);
      if (ok) return { ok: true, message: "schema ok" };
      const msg = ajv.errorsText(fn.errors, { dataVar: schemaRef });
      return { ok: false, message: `schema violation: ${msg}` };
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      return { ok: false, message: `could not validate: ${msg}` };
    }
  };
}
