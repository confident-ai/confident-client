# SDK generation

The Python and TypeScript SDKs are generated from the OpenAPI spec
confident-cloud publishes. Nothing under `python/confident_ai/` or
`typescript/src/` that carries an `@generated` banner is edited by hand — change
the route upstream, regenerate, and both SDKs move together.

## Running it

From `python/`:

```bash
poetry run python ../scripts/generate_sdk.py            # write
poetry run python ../scripts/generate_sdk.py --check    # verify, no writes (CI)
```

`--spec-dir` points at another checkout of confident-cloud, and
`--descriptive false` drops docstrings, JSDoc and explanatory comments. A run
classifies every file before writing any of it, so it refuses rather than
overwriting something hand-written.

## The two files you touch

**`generate_sdk.py`** is the entrypoint and the only file you run. It reads the
spec once, hands it to each renderer, and writes what comes back.

**`stateful_config.yml`** declares the stateful handles — the objects like
`client.dataset(id)` that hold a record's id so callers stop passing it to every
call. Its header is a menu of every key it accepts; a resource absent from it
still gets a normal stateless client.

## `sdkgen/`

Everything else. A file that emits SDK source is named `generate_*`:

|                                  |                                                                      |
| -------------------------------- | -------------------------------------------------------------------- |
| `generate_types.py`              | the wire types — one module per resource, and its barrel             |
| `generate_stateless_clients.py`  | the endpoint enum, the operations, and the clients that compose them |
| `generate_stateful_clients.py`   | the handles `stateful_config.yml` describes                          |
| `generate_files.py`              | where generated files go, their banner, and both formatters          |
| `constants.py`                   | everything the generator is told, as data                            |
| `errors.py`                      | the one exception the generator raises                               |

`openapi_helpers/` is what those stand on — reading the spec, and turning what
it says into SDK names, types and operations:

|                                  |                                                    |
| -------------------------------- | -------------------------------------------------- |
| `openapi_parser.py`              | reads the OpenAPI document                         |
| `openapi_to_sdk_types.py`        | turns a schema into a type both languages declare  |
| `openapi_to_sdk_operations.py`   | turns a route into a method both languages spell   |
| `openapi_to_sdk_names.py`        | turns a name in the spec into a name in the SDK    |

`custom_overlays/` holds the hand-written code folded into generated files —
see below.

## Overlays

Some things a client needs are not in the spec at all — prompt caching and
background refresh is the first of them. `custom_overlays/` states those as
exact edits against one rendered file, applied before anything is written, so
`--check`, idempotence and both formatters cover them like generated code.
`overlay.py` is what an overlay is, `run_after_generation.py` applies them all,
and one module per resource (`prompts.py`) holds the edits themselves.

Keep an overlay thin: rename a generated method out of the way and call it from
a hand-written one that lives in the SDK, where it is typed and tested like the
rest of the library. Every anchor must match the number of times it claims, so
a generator change that moves one fails the run instead of quietly dropping the
feature.

## Two conventions worth keeping

**Each renderer sits beside its twin in the other language** — `render_client`
next to `render_typescript_client`. It is the only thing that makes a difference
between the two SDKs visible in review.

**A pure refactor must leave the output byte-identical.** Run `--check` after
any change that was not meant to alter what is generated; it should report the
file count unchanged.