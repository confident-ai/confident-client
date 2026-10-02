"""The SDK reference: what confident-landing renders the SDK docs from.

confident-landing cannot re-derive this from the spec. A stateful handle is
declared in stateful_config.yml, an overlay rewrites a method after it is
rendered, and a few methods are written by hand — so what a caller can call is
only fully known here, at the end of a run. This publishes it: every
documented resource's modules, methods and parameters in both languages, with
the wire types they name, carrying the spec's own descriptions and examples so
the docs need no second input.

Names and signatures come from `read_sdk_code`, because the code that ships is
what a caller sees. The spec supplies what the code cannot say: which
operation a method calls, what a field means, and the example a caller can
copy.

The two halves are named apart. A `_read_*` or `_..._of` function takes a fact
out of one of those inputs; a `_describe_*` function turns what they gave into
one entry of the published document. `build_reference` runs the second over
every documented resource.
"""

import datetime

import yaml

from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from .constants import (
    PYTHON_PACKAGE,
    TS_PACKAGE,
    CANONICAL_SPEC_LOCATION,
    DOCUMENTED_RESOURCES,
    MERGED_SPEC,
    ORGANIZATION_KEY_RESOURCES,
    PYTHON_API_MODULE,
    PYTHON_HELPERS,
    RESOURCE_MODULES,
)
from .errors import SpecError
from .generate_stateless_clients import (
    flatten_groups,
    group_class,
    group_module,
    resource_groups,
    ts_group_module,
)
from .generate_stateful_clients import handle_module, properties_of
from .generate_files import banner
from .generate_types import declare, sort_by_dependency
from .openapi_helpers.openapi_parser import Route, schemas_reached
from .openapi_helpers.openapi_to_sdk_names import (
    camel_case,
    client_class_name,
    enum_member_name,
    python_module_for,
    snake_case,
    ts_module_for,
)
from .openapi_helpers.openapi_to_sdk_operations import (
    Method,
    parameters_in,
    resolve_method,
)
from .openapi_helpers.openapi_to_sdk_types import Resolver
from .read_sdk_code import (
    RenderedClass,
    RenderedMethod,
    RenderedParameter,
    python_classes,
    python_constants,
    python_functions,
    typescript_classes,
)

# The blocks of stateful_config.yml that expose a method backed by a route.
_HANDLE_BLOCKS = ("delegate", "on_item", "load", "save")


# ===== Reading the SDK's own prose =====


def _unwrap_paragraphs(lines: Sequence[str]) -> str:
    """Wrapped docstring lines, back as the paragraphs they were written as."""
    blocks: List[List[str]] = [[]]
    for line in lines:
        if line.strip():
            blocks[-1].append(line.strip())
        elif blocks[-1]:
            blocks.append([])
    return "\n\n".join(" ".join(block) for block in blocks if block).strip()


def _read_docstring(
    doc: Optional[str],
) -> Tuple[str, Optional[str], Dict[str, str]]:
    """A docstring's summary, description, and text per argument.

    Read from the docstring rather than the spec, so an overlaid method
    documents what the overlay made it do.
    """
    if not doc:
        return "", None, {}

    lines = doc.split("\n")
    summary = lines[0].strip()
    rest = lines[1:]

    argument_start = next(
        (index for index, line in enumerate(rest) if line.strip() == "Args:"),
        len(rest),
    )
    description = _unwrap_paragraphs(rest[:argument_start]) or None

    arguments: Dict[str, List[str]] = {}
    current: Optional[str] = None
    for line in rest[argument_start + 1 :]:
        stripped = line.strip()
        if not stripped:
            continue
        name, separator, text = stripped.partition(": ")
        # An entry opens a name; anything more indented continues the last one.
        if separator and " " not in name and not line.startswith(" " * 12):
            current = name
            arguments[current] = [text]
        elif current:
            arguments[current].append(stripped)
    return (
        summary,
        description,
        {name: " ".join(text) for name, text in arguments.items()},
    )


# ===== Reading what the spec says about a value =====


def _schemas_referenced(schema: Dict[str, Any]) -> List[str]:
    """The component names a property can resolve to, in declaration order."""
    found: List[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, list):
            for item in node:
                walk(item)
            return
        if not isinstance(node, dict):
            return
        reference = node.get("$ref")
        if isinstance(reference, str) and reference.startswith(
            "#/components/schemas/"
        ):
            name = reference.rsplit("/", 1)[-1]
            if name not in found:
                found.append(name)
        for value in node.values():
            walk(value)

    walk(schema)
    return found


def _as_json_value(value: Any) -> Any:
    """An example as JSON carries it: a YAML date back as the string it was."""
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _as_json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_as_json_value(item) for item in value]
    return value


def _example_of(node: Dict[str, Any]) -> Any:
    """A value's example. A parameter carries its own, a property nests it."""
    if "example" in node:
        return _as_json_value(node["example"])
    return _as_json_value((node.get("schema") or {}).get("example"))


def _spec_node_per_argument(
    method: Method, schemas: Dict[str, Any]
) -> Dict[str, Dict[str, Any]]:
    """The spec node behind each of a method's arguments, by Python name.

    Only the spec says what a caller should put in an argument, so this is
    where an example comes from.
    """
    nodes: Dict[str, Dict[str, Any]] = {}
    by_wire = {
        parameter.wire: parameter
        for parameter in method.parameters
        if parameter.source in ("path", "query")
    }
    for location in ("path", "query"):
        for declared in parameters_in(method.route, location):
            parameter = by_wire.get(declared["name"])
            if parameter is not None:
                nodes[parameter.name] = declared

    if method.sends:
        # Across every branch, so a union body's fields are not left out.
        properties = properties_of(method.sends, schemas)
        for parameter in method.parameters:
            if parameter.source == "body" and parameter.wire in properties:
                nodes[parameter.name] = properties[parameter.wire]
            elif parameter.source == "union-body":
                nodes[parameter.name] = schemas.get(method.sends) or {}
        # A handle names a body field as an argument of its own, which the
        # operation declares no parameter for.
        for wire, declared in properties.items():
            nodes.setdefault(snake_case(wire), declared)
    return nodes


# ===== Describing one method, in both languages =====


def _describe_operation(route: Route) -> Dict[str, Any]:
    return {
        "id": route.operation_id,
        "method": route.method.upper(),
        "path": route.path,
    }


def _typescript_twin(
    rendered: RenderedClass, name: str
) -> Optional[RenderedMethod]:
    """A TypeScript method under the name its Python twin implies.

    The trailing underscore is how a name that collides with a TypeScript
    keyword is spelled.
    """
    return rendered.methods.get(camel_case(name)) or rendered.methods.get(
        f"{camel_case(name)}_"
    )


def _describe_parameter(
    parameter: RenderedParameter,
    typescript: Optional[RenderedParameter],
    method: Optional[Method],
    node: Optional[Dict[str, Any]],
    documented: Dict[str, str],
) -> Dict[str, Any]:
    declared = next(
        (
            candidate
            for candidate in (method.parameters if method else ())
            if candidate.name == parameter.name
        ),
        None,
    )
    entry: Dict[str, Any] = {
        "python": parameter.name,
        "typescript": typescript.name if typescript else None,
        "wire": declared.wire if declared else None,
        "in": declared.source if declared else None,
        "type": {
            "python": parameter.annotation,
            "typescript": typescript.annotation if typescript else None,
        },
        "required": parameter.required,
        "keyword": parameter.keyword,
        "default": parameter.default,
        # The docstring describes the argument as the method takes it; the
        # spec fills in what it omits.
        "description": documented.get(parameter.name)
        or (node or {}).get("description"),
        "example": _example_of(node) if node else None,
        "references": _schemas_referenced(node) if node else [],
    }
    # Walking a union body finds its branches, not the schema the argument is
    # typed as, which is the one a caller looks up.
    if declared is not None and declared.source == "union-body":
        entry["references"] = [declared.wire] + [
            name for name in entry["references"] if name != declared.wire
        ]
    return entry


def _describe_method(
    name: str,
    rendered: RenderedMethod,
    asynchronous: Optional[RenderedMethod],
    typescript: Optional[RenderedMethod],
    method: Optional[Method],
    schemas: Dict[str, Any],
    drop: Sequence[str] = (),
) -> Dict[str, Any]:
    summary, description, documented = _read_docstring(rendered.doc)
    if not summary and typescript is not None:
        summary, description, documented = _read_docstring(typescript.doc)
    nodes = _spec_node_per_argument(method, schemas) if method else {}

    ts_parameters = {}
    if typescript is not None:
        ts_parameters = {
            parameter.name: parameter
            for parameter in typescript.parameters
            if parameter.name not in drop
        }

    parameters = [
        _describe_parameter(
            parameter,
            ts_parameters.get(camel_case(parameter.name))
            or ts_parameters.get(f"{camel_case(parameter.name)}_"),
            method,
            nodes.get(parameter.name),
            documented,
        )
        for parameter in rendered.parameters
        if parameter.name not in drop
    ]

    # Python orders arguments by position then keyword, TypeScript by
    # requiredness, so neither order can be inferred from the other.
    order = {
        "python": [parameter["python"] for parameter in parameters],
        "typescript": [
            parameter.name
            for parameter in (typescript.parameters if typescript else ())
            if parameter.name not in drop
        ],
    }

    returns = (
        method.returns.replace("Optional[", "").rstrip("]") if method else None
    )
    entry: Dict[str, Any] = {
        "name": {
            "python": name,
            "pythonAsync": asynchronous.name if asynchronous else None,
            "typescript": typescript.name if typescript else None,
        },
        "summary": summary,
        "description": description,
        # Every route the method can call, default first.
        "operations": (
            [_describe_operation(method.route)] if method is not None else []
        ),
        "returns": {
            "python": rendered.returns,
            "typescript": typescript.returns if typescript else None,
            "type": returns,
        },
        "body": method.sends if method else None,
        "parameters": parameters,
        "order": order,
    }
    return entry


# ===== Describing one resource =====


def _api_key_kind(resource: str) -> str:
    return (
        "organization" if resource in ORGANIZATION_KEY_RESOURCES else "project"
    )


def _describe_modules(
    resource: str,
    routes: List[Route],
    resolver: Resolver,
    schemas: Dict[str, Any],
    acronyms: Set[str],
    source: "_RenderedSource",
) -> List[Dict[str, Any]]:
    """One entry per operations module the resource generates."""
    python_root = f"python/{PYTHON_PACKAGE}/{RESOURCE_MODULES.get(resource, resource).replace('-', '_')}"
    typescript_root = f"typescript/src/{ts_module_for(resource)}"
    groups = flatten_groups(resource_groups(routes))
    single = len(groups) == 1

    entries: List[Dict[str, Any]] = []
    for segments, group_routes in groups:
        class_name = (
            client_class_name(
                RESOURCE_MODULES.get(resource, resource), acronyms
            )
            if single
            else group_class(resource, segments, acronyms)
        )
        python_file = "client.py" if single else group_module(segments)
        typescript_file = "client.ts" if single else ts_group_module(segments)
        python_class = source.python_class(
            f"{python_root}/{python_file}", class_name
        )
        typescript_class = source.typescript_class(
            f"{typescript_root}/{typescript_file}", class_name
        )

        methods = {
            method.name: method
            for method in (
                resolve_method(route, resolver, schemas)
                for route in group_routes
            )
        }
        entries.append(
            {
                "segments": list(segments),
                "python": {
                    "module": f"{python_root}/{python_file}",
                    "class": class_name,
                },
                "typescript": {
                    "module": f"{typescript_root}/{typescript_file}",
                    "class": class_name,
                },
                "methods": [
                    _describe_method(
                        name,
                        rendered,
                        python_class.methods.get(f"a_{name}"),
                        _typescript_twin(typescript_class, name),
                        methods.get(name),
                        schemas,
                    )
                    for name, rendered in python_class.methods.items()
                    if not name.startswith("a_")
                ],
            }
        )
    return entries


def _exclusive_keywords(config: Dict[str, Any]) -> Dict[str, List[str]]:
    """Each method's arguments a caller may pass only one of, default first.

    A `load` that chooses between routes takes one keyword per route, and the
    method rejects a call carrying more than one. Nothing about the arguments
    themselves says so, so the constraint is published rather than left for a
    reader — or a generated example — to discover by raising.
    """
    found: Dict[str, List[str]] = {}
    for exposed, declared in (config.get("load") or {}).items():
        choices = declared.get("by")
        if not choices:
            continue
        keywords = sorted(
            choices, key=lambda name: "default" not in choices[name]
        )
        found[exposed] = keywords
    return found


def _routes_per_handle_method(config: Dict[str, Any]) -> Dict[str, List[str]]:
    """Each method the YAML exposes, against the operations behind it.

    A method the caller chooses a route for leads with the one its default
    keyword selects, which is the call a reader writes first.
    """
    found: Dict[str, List[str]] = {}
    for block in _HANDLE_BLOCKS:
        for exposed, declared in (config.get(block) or {}).items():
            if isinstance(declared, str):
                found[exposed] = [declared]
            elif "by" in declared:
                choices = list(declared["by"].values())
                choices.sort(key=lambda choice: "default" not in choice)
                found[exposed] = [choice["operation"] for choice in choices]
            else:
                found[exposed] = [declared["operation"]]
    return found


def _path_parameters_of(routes: List[Route]) -> Dict[str, Dict[str, Any]]:
    """Every path parameter the resource declares, by the name it fills."""
    declared: Dict[str, Dict[str, Any]] = {}
    for route in routes:
        for parameter in parameters_in(route, "path"):
            declared.setdefault(parameter["name"], parameter)
    return declared


def _describe_handle_properties(
    config: Dict[str, Any],
    python_class: RenderedClass,
    typescript_class: RenderedClass,
    schemas: Dict[str, Any],
    routes: List[Route],
) -> List[Dict[str, Any]]:
    """What the handle holds, which is what a caller sets before saving it."""
    declared = properties_of(config["class"], schemas)
    typescript = dict(typescript_class.fields)
    # The identity is a path parameter rather than a field of the loaded
    # shape, so the routes are where it is documented.
    paths = _path_parameters_of(routes)

    entries = []
    for name, annotation in python_class.fields:
        wire = next(
            (
                field
                for field in declared
                if camel_case(field) == camel_case(name)
            ),
            None,
        )
        node = declared.get(wire) if wire else paths.get(camel_case(name))
        entries.append(
            {
                "python": name,
                "typescript": (
                    camel_case(name) if camel_case(name) in typescript else None
                ),
                "wire": wire,
                "type": {
                    "python": annotation,
                    "typescript": typescript.get(camel_case(name)),
                },
                "description": (node or {}).get("description"),
                "example": _example_of(node) if node else None,
                "references": _schemas_referenced(node) if node else [],
            }
        )
    return entries


def _describe_handle(
    resource: str,
    config: Dict[str, Any],
    routes: List[Route],
    resolver: Resolver,
    schemas: Dict[str, Any],
    source: "_RenderedSource",
) -> Dict[str, Any]:
    python_root = f"python/{PYTHON_PACKAGE}/{RESOURCE_MODULES.get(resource, resource).replace('-', '_')}"
    typescript_root = f"typescript/src/{ts_module_for(resource)}"
    python_file = f"{python_root}/{handle_module(config)}"
    typescript_file = f"{typescript_root}/{camel_case(config['class'])}.ts"
    python_class = source.python_class(python_file, config["class"])
    typescript_class = source.typescript_class(typescript_file, config["class"])

    by_operation = {route.operation_id: route for route in routes}
    index = _routes_per_handle_method(config)
    exclusive = _exclusive_keywords(config)
    helpers = config.get("helpers") or {}

    methods: List[Dict[str, Any]] = []
    for name, rendered in python_class.methods.items():
        if name.startswith("a_") or name not in index:
            continue
        entry = _describe_method(
            name,
            rendered,
            python_class.methods.get(f"a_{name}"),
            _typescript_twin(typescript_class, name),
            resolve_method(by_operation[index[name][0]], resolver, schemas),
            schemas,
        )
        entry["operations"] = [
            _describe_operation(by_operation[operation])
            for operation in index[name]
        ]
        if name in exclusive:
            entry["chooseOneOf"] = exclusive[name]
        methods.append(entry)

    for exposed, function in helpers.items():
        rendered = source.python_helpers.get(function)
        if rendered is None:
            raise SpecError(
                f"{resource}: `{function}` is bound as `{exposed}` but "
                f"{PYTHON_HELPERS.name} declares no such function."
            )
        # Python binds the bare function, whose first argument is the handle
        # a caller passes as the receiver; TypeScript declares a wrapper that
        # already reads as the method.
        methods.append(
            _describe_method(
                exposed,
                rendered,
                None,
                _typescript_twin(typescript_class, exposed),
                None,
                schemas,
                drop=(
                    [rendered.parameters[0].name] if rendered.parameters else []
                ),
            )
        )

    opening = source.python_class(
        f"python/{PYTHON_PACKAGE}/clients/stateful.py", "StatefulClients"
    ).methods[config["client_method"]["name"]]
    ts_opening = source.typescript_class(
        "typescript/src/clients/stateful.ts", "StatefulClients"
    ).methods[camel_case(config["client_method"]["name"])]

    return {
        "class": config["class"],
        "python": {"module": python_file, "class": config["class"]},
        "typescript": {"module": typescript_file, "class": config["class"]},
        # What a caller opens the handle by instead of the id.
        "opensWith": list(config["client_method"].get("takes") or []),
        # The id the handle supplies. A method whose route names this
        # parameter cannot run without it, however the handle was opened.
        "identity": {
            "python": config["identity"]["field"],
            "typescript": camel_case(config["identity"]["field"]),
            "parameter": config["identity"]["parameter"],
        },
        # The methods that fill the handle. A method with no operation behind
        # it reads what one of these left on the object.
        "loads": list(config.get("load") or {}),
        "open": _describe_method(
            config["client_method"]["name"],
            opening,
            None,
            ts_opening,
            None,
            schemas,
        ),
        "properties": _describe_handle_properties(
            config, python_class, typescript_class, schemas, routes
        ),
        "methods": methods,
    }


# ===== Describing the wire types those methods name =====


def _import_location(resource: str, name: str) -> Dict[str, Dict[str, str]]:
    """Where a caller imports the type from, as they would write it.

    The barrel each resource publishes, not the module the type is declared
    in. Generated code imports the module directly to keep the barrel out of
    its own import cycle; a caller has no such problem, and
    `<package>.datasets` is the import the package exists to offer.
    """
    return {
        "python": {
            "module": python_module_for(resource)[: -len(".types")],
            "name": name,
        },
        "typescript": {
            "module": f"{TS_PACKAGE}/{ts_module_for(resource)}",
            "name": name,
        },
    }


def _describe_types(
    reachable: Dict[str, Set[str]],
    home: Dict[str, str],
    schemas: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Every schema the documented resources reach, in dependency order.

    Grouped and declared one resource at a time, exactly as `render_wire_types`
    does it. Declaring them together instead would leave a shape the resolver
    promotes out of an inline definition with no resource to attribute it to,
    and the import published for it would name a module that never declares it.
    """
    owned: Dict[str, Dict[str, Any]] = {}
    for name in sorted(home):
        owned.setdefault(home[name], {})[name] = schemas[name]

    wanted = {name for names in reachable.values() for name in names}

    entries: List[Dict[str, Any]] = []
    for resource in sorted(owned):
        if not wanted & set(owned[resource]):
            continue
        module = declare(resource, owned[resource], home)
        sort_by_dependency(module)
        entries.extend(
            _describe_module_types(module, resource, schemas, wanted)
        )
    return sorted(entries, key=lambda entry: entry["name"])


def _describe_module_types(
    module: Any,
    resource: str,
    schemas: Dict[str, Any],
    wanted: Set[str],
) -> List[Dict[str, Any]]:
    """One module's declarations, minus what no documented method reaches.

    A promoted shape is named by nothing in the spec, so it is kept whenever
    its module is: the only thing that reaches it is a type declared beside it.
    """

    def keep(name: str) -> bool:
        return name in wanted or name not in schemas

    def import_location(name: str) -> Dict[str, Dict[str, str]]:
        return _import_location(resource, name)

    entries: List[Dict[str, Any]] = []
    for enum in module.enums:
        if not keep(enum.name):
            continue
        schema = schemas.get(enum.name) or {}
        entries.append(
            {
                "name": enum.name,
                "kind": "enum",
                "description": schema.get("description"),
                **import_location(enum.name),
                "members": [
                    {"name": enum_member_name(value), "value": value}
                    for value in enum.values
                ],
                "references": [],
            }
        )

    for declaration in module.declarations:
        if not keep(declaration.name):
            continue
        schema = schemas.get(declaration.name) or {}
        # From the spec rather than the resolver's dependencies, which cover
        # only the module being declared: a type another module owns is an
        # import there, not a dependency.
        entry: Dict[str, Any] = {
            "name": declaration.name,
            "description": schema.get("description"),
            "example": _example_of(schema),
            **import_location(declaration.name),
            "references": _schemas_referenced(schema),
        }
        if hasattr(declaration, "fields"):
            properties = schema.get("properties") or {}
            entry["kind"] = "object"
            entry["fields"] = [
                {
                    "wire": field.name,
                    "python": field.python_name,
                    "typescript": field.name,
                    "type": {
                        "python": field.type.as_python(field.optional),
                        "typescript": field.type.as_typescript(),
                    },
                    "required": not field.optional,
                    "description": (properties.get(field.name) or {}).get(
                        "description"
                    ),
                    "example": _example_of(properties.get(field.name) or {}),
                    "references": _schemas_referenced(
                        properties.get(field.name) or {}
                    ),
                }
                for field in declaration.fields
            ]
        else:
            entry["kind"] = "union"
            entry["branches"] = _schemas_referenced(schema)
            entry["type"] = {
                "python": declaration.type.as_python(False),
                "typescript": declaration.type.as_typescript(),
            }
        entries.append(entry)

    return entries


# ===== The source this run rendered =====


class _RenderedSource:
    """The rendered text of this run, parsed once per file it is asked for."""

    def __init__(self, outputs: Dict[str, str]) -> None:
        self._outputs = outputs
        self._python: Dict[str, Dict[str, RenderedClass]] = {}
        self._typescript: Dict[str, Dict[str, RenderedClass]] = {}
        self.python_helpers = python_functions(PYTHON_HELPERS.read_text())
        self.constants = python_constants(PYTHON_API_MODULE.read_text())

    def _text(self, path: str) -> str:
        if path not in self._outputs:
            raise SpecError(
                f"the SDK reference expects `{path}`, which this run did "
                "not render. Update DOCUMENTED_RESOURCES or sdkgen/"
                "generate_sdk_reference.py to match the tree the generator "
                "writes."
            )
        return self._outputs[path]

    def python_class(self, path: str, name: str) -> RenderedClass:
        if path not in self._python:
            self._python[path] = python_classes(self._text(path))
        return self._declared(self._python[path], path, name)

    def typescript_class(self, path: str, name: str) -> RenderedClass:
        if path not in self._typescript:
            self._typescript[path] = typescript_classes(self._text(path))
        return self._declared(self._typescript[path], path, name)

    @staticmethod
    def _declared(
        classes: Dict[str, RenderedClass], path: str, name: str
    ) -> RenderedClass:
        if name not in classes:
            raise SpecError(
                f"`{path}` declares no class `{name}`, which the SDK "
                "reference expects. The generator's output moved; update "
                "sdkgen/generate_sdk_reference.py."
            )
        return classes[name]


# ===== One run =====


def build_reference(
    outputs: List[Tuple[Any, str]],
    generating: Dict[str, List[Route]],
    home: Dict[str, str],
    components: Dict[str, Any],
    stateful: Dict[str, Any],
    acronyms: Set[str],
    repo_root: Any,
) -> str:
    """The reference for this run, as the YAML it is published as."""
    schemas = components.get("schemas") or {}
    source = _RenderedSource(
        {str(path.relative_to(repo_root)): content for path, content in outputs}
    )

    documented = sorted(
        set(generating) & DOCUMENTED_RESOURCES
        if DOCUMENTED_RESOURCES
        else set(generating)
    )
    undocumented = sorted(DOCUMENTED_RESOURCES - set(generating))
    if undocumented:
        raise SpecError(
            "DOCUMENTED_RESOURCES names "
            f"`{undocumented[0]}`, which this run does not generate."
        )

    resources: List[Dict[str, Any]] = []
    reachable: Dict[str, Set[str]] = {}
    for resource in documented:
        routes = generating[resource]
        resolver = Resolver(resource, home)
        module = RESOURCE_MODULES.get(resource, resource).replace("-", "_")
        entry: Dict[str, Any] = {
            "name": resource,
            "keyKind": _api_key_kind(resource),
            "client": {
                "python": f"client.{module}",
                "typescript": f"client.{camel_case(ts_module_for(resource))}",
            },
            "modules": _describe_modules(
                resource, routes, resolver, schemas, acronyms, source
            ),
            "handle": None,
        }
        if resource in stateful:
            entry["handle"] = _describe_handle(
                resource, stateful[resource], routes, resolver, schemas, source
            )
        resources.append(entry)
        reachable[resource] = schemas_reached(
            [route.nodes for route in routes], components
        )

    reference = {
        # The spellings the spec's own type names use, so a consumer can
        # title-case a name without a second list to keep in step.
        "acronyms": sorted(acronyms),
        "keyKinds": {
            "organization": {
                "envVar": source.constants["CONFIDENT_ORG_API_KEY_ENV_VAR"],
                "argument": {"python": "api_key", "typescript": "apiKey"},
            },
            "project": {
                "envVar": source.constants["CONFIDENT_PROJ_API_KEY_ENV_VAR"],
                "argument": {
                    "python": "project_api_key",
                    "typescript": "projectApiKey",
                },
            },
        },
        "resources": resources,
        "types": _describe_types(reachable, home, schemas),
    }
    banner_lines = banner("#", f"{CANONICAL_SPEC_LOCATION}/{MERGED_SPEC}")
    return "\n".join(banner_lines) + yaml.safe_dump(
        reference, sort_keys=False, allow_unicode=True, width=79
    )
