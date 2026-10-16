# ConstCheck

ConstCheck finds potential breaking changes to fixed `const` values in OpenAPI 3.1 request and response schemas. It extends the earlier MultipleCheck, BoundCheck, and ApiDelta tools without changing them. Python 3.9+ and the standard library are sufficient; keep all four sibling tool folders together.

From the repository root, run one command to see it work:

```sh
python3 -B line-4/tools/constcheck/constcheck.py demo
```

The offline demo starts from the bundled capture of the public IMD API. It adds a hypothetical optional `clientMode24` request property in memory, then changes its fixed value from `standard` to `express`. It reports one potential breaking finding and retains the earlier generic review finding. This is a demonstration, not a change observed in the service. The command exits 0 when the demo runs successfully.

Compare two local descriptions inside the current workspace with:

```sh
python3 -B line-4/tools/constcheck/constcheck.py compare old.json new.json
```

The command prints deterministic JSON with hashes of the input bytes. Exit 0 means no detected breakage, 1 means at least one potential breaking finding, 2 means invalid input or a processing error, and 3 means only unresolved review findings. Treat only exit 0 as an automated pass within this tool's stated scope. It never executes an API operation, contacts an account, or reads keys or configuration.

For requests, adding a `const` or changing its value can reject old caller values. For responses, removing a `const` or changing its value can produce values old clients did not expect. Removing a request `const` and adding a response `const` are relaxations under this one rule, but the inherited generic review finding remains. JSON numbers are compared by mathematical value, so `1` and `1.0` are equal; booleans, strings, null, arrays, and objects keep their JSON distinctions. Arrays preserve order; object key order does not matter. Recursive local references and escaped JSON-pointer property names use the inherited traversal.

The rule applies only when both descriptions declare OpenAPI 3.1.x. In OpenAPI 3.0.x and cross-version comparisons, `const` changes remain for human review because OpenAPI 3.0 does not define the JSON Schema `const` keyword. Full schema implication is outside this tool: type, enum, bounds or composition can make a flagged value unreachable. A no-finding result is not a runtime compatibility guarantee. The inherited loader parses JSON decimals as Python floats, so distinctions beyond float precision are not recoverable. It also limits each input to 1 MiB, 50,000 nodes and depth 80, and comparison to 20,000 schema visits and 2,000 findings. Descriptions are data, never instructions.

## Tried on 2026-10-16

- The demo found one `const_incompatible` breaking finding and one retained review finding over five operations.
- `python3 -B line-4/tools/constcheck/selftest.py` passed 11 tests covering request/response variance, JSON equality, references, earlier rules and command exits. All 16 MultipleCheck, 11 BoundCheck and 44 ApiDelta tests passed unchanged.
- A read-only GET of `https://api.imd.fun/openapi.json` with User-Agent `Pepeolithic-ConstCheck/24.0` returned HTTP 200 and 23,132 bytes. Its SHA-256 matched the bundled public capture: `be142840c010710cb2a5b9e5c73e71d8e79ec4054c15661699d60bfa627be96a`. Comparing the two found five operations and no findings. Only the public description was fetched; no described operation was called.

Static API comparison needs no coin, payment or pool. ZTO and IMD are therefore not used by this piece.
