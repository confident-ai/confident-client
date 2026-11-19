"""Renders the stateful handles described by stateful_config.yml.

A handle holds one resource's identity, so every method it exposes is the
stateless method minus the path parameter that identity supplies. That part is
a projection of the spec: it reads the same `Method` objects
`generate_clients` builds, so a handle cannot drift from what it calls.

The YAML covers only what the spec cannot say — which operations a handle
exposes and under what names, which of them fill the handle instead of
returning, which send a body built from it, and which methods have no
operation behind them at all.
"""

import ast
import re

from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

import yaml

from .constants import (
    PYTHON_PACKAGE,
    HELPERS_MODULE,
    MEDIA_MAPPING_FIELD,
    METHOD_ORDER,
    ORGANIZATION_KEY_RESOURCES,
    PYTHON_HELPERS,
    REPO_ROOT,
    STATEFUL_CONFIG,
    TYPESCRIPT_HELPERS,
)
from .errors import (
    SpecError,
)
from .openapi_helpers.openapi_to_sdk_names import (
    camel_case,
    client_class_name,
    pascal_case,
    python_module_for,
    singular,
    snake_case,
)
from .openapi_helpers.openapi_parser import (
    Route,
    ref_name,
    split_union,
)
from .openapi_helpers.openapi_to_sdk_types import (
    Resolver,
)
from .openapi_helpers.openapi_to_sdk_names import ts_module_for
from .openapi_helpers.openapi_to_sdk_operations import (
    request_type,
    resolve_method,
)
from .generate_files import (
    render_docstring,
    render_jsdoc,
    ts_import,
    ts_key,
    typing_imports,
)


def load_stateful_config() -> Dict[str, Any]:
    resources = yaml.safe_load(STATEFUL_CONFIG.read_text()) or {}
    assert_helpers_exist(resources)
    return resources


# `export const x = ...`, `export function x(...)`, and the rest of the forms
# a hand-written helper can take. Enough to tell a name that is there from one
# that is not; it is not trying to parse TypeScript.
TS_EXPORTED = re.compile(
    r"^export\s+(?:async\s+)?(?:function|const|let|var|class)\s+"
    r"([A-Za-z_$][\w$]*)",
    re.M,
)


def python_top_level_names(path: Path) -> Set[str]:
    """Every name a hand-written Python module defines at the top level."""
    names: Set[str] = set()
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
        elif isinstance(node, ast.ClassDef):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            names.update(
                target.id
                for target in node.targets
                if isinstance(target, ast.Name)
            )
    return names


def assert_helpers_exist(resources: Dict[str, Any]) -> None:
    """Refuse to generate a handle whose helper nobody has written.

    A helper is bound onto the generated class by name, so a name with nothing
    behind it generates a module that cannot be imported. TypeScript catches
    that at build time; Python does not catch it until a caller first touches
    the handle, which is far from the YAML line that caused it.
    """
    written = {
        PYTHON_HELPERS: python_top_level_names(PYTHON_HELPERS),
        TYPESCRIPT_HELPERS: set(
            TS_EXPORTED.findall(TYPESCRIPT_HELPERS.read_text())
        ),
    }

    missing: List[str] = []
    for resource in sorted(resources):
        helpers = (resources[resource] or {}).get("helpers") or {}
        for exposed in sorted(helpers):
            function = helpers[exposed]
            for path, spelling in (
                (PYTHON_HELPERS, function),
                (TYPESCRIPT_HELPERS, camel_case(function)),
            ):
                if spelling not in written[path]:
                    missing.append(
                        f"  {resource}.{exposed} -> {spelling}\n"
                        f"      not found in {path.relative_to(REPO_ROOT)}"
                    )

    if missing:
        raise SpecError(
            f"{STATEFUL_CONFIG.name} names helpers that are not "
            "written:\n\n" + "\n".join(missing) + "\n\n"
            "A helper is hand-written in both SDKs and bound onto the "
            "generated class by name. Write it in both files, or drop the "
            "entry from the YAML."
        )


def handle_module(config: Dict[str, Any]) -> str:
    """The file a handle is generated into, named for the class it holds."""
    return f"{snake_case(config['class'])}.py"


def branches_of(name: str, schemas: Dict[str, Any]) -> List[str]:
    """The component names a union refers to, or [] when it is one shape."""
    schema = schemas.get(name)
    if schema is None:
        raise SpecError(f"the spec declares no `{name}`.")
    # A union of shapes, not a nullable one: `type: [X, "null"]` names one
    # shape that may be absent, which has branches nothing chooses between.
    if not (schema.get("anyOf") or schema.get("oneOf")):
        return []
    members, _ = split_union(schema)
    if not members:
        return []
    for member in members:
        if "$ref" not in member:
            raise SpecError(
                f"`{name}` is a union with an inline branch, which has no "
                "declared fields. Give it a $ref upstream."
            )
    return [ref_name(member["$ref"]) for member in members]


def properties_of(
    name: str, schemas: Dict[str, Any]
) -> Dict[str, Dict[str, Any]]:
    """Every field a schema can carry, across all branches of a union."""
    branches = branches_of(name, schemas)
    if not branches:
        return dict((schemas.get(name) or {}).get("properties") or {})
    fields: Dict[str, Dict[str, Any]] = {}
    for branch in branches:
        member = schemas.get(branch) or {}
        for field, value in (member.get("properties") or {}).items():
            fields.setdefault(field, value)
    return fields


def required_of(name: str, schemas: Dict[str, Any]) -> Set[str]:
    """The fields every branch of a schema requires."""
    branches = branches_of(name, schemas) or [name]
    required = [
        set((schemas.get(b) or {}).get("required") or []) for b in branches
    ]
    return set.intersection(*required) if required else set()


class Handle:
    """One resource's stateful class, assembled from the spec and the YAML."""

    # ===== Setup =====

    def __init__(
        self,
        resource: str,
        config: Dict[str, Any],
        routes: List[Route],
        home: Dict[str, str],
        acronyms: Set[str],
        schemas: Dict[str, Any],
        descriptive: bool = True,
    ) -> None:
        self.resource = resource
        self.descriptive = descriptive
        self.config = config
        self.schemas = schemas
        self.home = home
        self.name = config["class"]
        self.identity = config["identity"]
        self.takes: List[str] = (
            config.get("client_method", {}).get("takes") or []
        )
        self.client_class = client_class_name(resource, acronyms)
        self.client_module = (
            f"{python_module_for(resource)[: -len('.types')]}.client"
        )
        self.resolver = Resolver(resource, home)
        self.referenced: Set[str] = set()
        self.annotations: List[str] = []
        self.routes = {route.operation_id: route for route in routes}
        self.methods: Dict[str, Any] = {}
        self.conversions: Dict[str, Tuple[str, str]] = {}
        self.guards: Dict[str, Tuple[str, str, str]] = {}

    def route(self, operation: str) -> Route:
        if operation not in self.routes:
            raise SpecError(
                f"{self.resource}: stateful_config.yml names "
                f"`{operation}`, "
                "which the spec does not declare in this resource."
            )
        return self.routes[operation]

    def method(self, operation: str) -> Any:
        if operation not in self.methods:
            self.methods[operation] = resolve_method(
                self.route(operation), self.resolver, self.schemas
            )
        return self.methods[operation]

    def note(self, method: Any) -> None:
        self.annotations.extend(method.annotations)
        self.referenced.update(method.named_types)

    def held(self, method: Any) -> str:
        """The parameter name the identity fills on one operation."""
        for parameter in method.parameters:
            if (
                parameter.source == "path"
                and parameter.wire == self.identity["parameter"]
            ):
                return parameter.name
        raise SpecError(
            f"{method.route.operation_id}: bound to a stateful handle, but "
            f"the route does not take `{self.identity['parameter']}`."
        )

    def resolve(self, schema: Dict[str, Any], where: str) -> str:
        resolved = self.resolver.resolve(schema, where, pascal_case(where))
        self.referenced.update(resolved.deps)
        annotation = resolved.as_python(True)
        self.annotations.append(annotation)
        return annotation

    # ===== What the handle holds =====

    def aliased(self, annotation: str) -> str:
        """An annotation, with the payload type's alias in place of its name.

        A resource whose pulled shape is named after its handle — `Project`
        returning a `Project` — imports the shape as `<name>Payload`, because
        the class being defined has taken the name. Every annotation that
        mentions it has to follow, or it resolves to the half-built class.
        """
        return re.sub(rf"\b{self.name}\b", f"{self.name}Payload", annotation)

    def state_fields(self) -> List[Tuple[str, str]]:
        """Every field the handle holds.

        The pulled shape, plus whatever a save sends: a body built from state
        cannot carry a field the handle has no room for.
        """
        fields = dict(properties_of(self.name, self.schemas))
        for name, save in (self.config.get("save") or {}).items():
            sends = request_type(self.route(save["operation"]))
            arguments = {snake_case(name) for name in save.get("call_params") or []}
            for field, schema in properties_of(sends, self.schemas).items():
                if snake_case(field) not in arguments:
                    fields.setdefault(field, schema)
        return [
            (snake_case(field), self.resolve(schema, f"{self.name}.{field}"))
            for field, schema in fields.items()
        ]

    def ts_state_fields(self) -> List[Tuple[str, str]]:
        fields = dict(properties_of(self.name, self.schemas))
        for _, save in (self.config.get("save") or {}).items():
            sends = request_type(self.route(save["operation"]))
            arguments = {snake_case(name) for name in save.get("call_params") or []}
            for field, schema in properties_of(sends, self.schemas).items():
                if snake_case(field) not in arguments:
                    fields.setdefault(field, schema)
        resolved = []
        for field, schema in fields.items():
            found = self.resolver.resolve(
                schema,
                f"{self.name}.{field}",
                pascal_case(f"{self.name}.{field}"),
            )
            self.referenced.update(found.deps)
            resolved.append((field, found.as_typescript()))
        return resolved

    def load_lines(self, union: bool) -> List[str]:
        """What a load writes onto the handle: the pulled shape, no more."""
        read = "getattr(payload, {name!r}, None)" if union else "payload.{name}"
        return [
            f"        self.{snake_case(field)} = "
            + read.format(name=snake_case(field))
            for field in properties_of(self.name, self.schemas)
        ]

    def ts_load_lines(self) -> List[str]:
        return [
            f'    this.{field} = source["{field}"] as typeof this.{field};'
            for field in properties_of(self.name, self.schemas)
        ]

    # ===== Reading one shape, and turning it into another =====

    def shared_fields(self, name: str) -> List[str]:
        """The fields every branch of a schema declares."""
        branches = branches_of(name, self.schemas)
        return [
            field
            for field in properties_of(name, self.schemas)
            if all(
                field in ((self.schemas.get(b) or {}).get("properties") or {})
                for b in branches or [name]
            )
        ]

    def discriminators(
        self,
        name: str,
        shared: Sequence[str],
        arguments: Sequence[str] = (),
    ) -> Dict[str, str]:
        """Each branch of a union, and the one field that chooses it.

        Pydantic keeps only the fields of the branch a payload matches, so a
        payload carrying two branches' fields loses one silently. The branch is
        chosen here instead, by the field only it *requires*: sibling branches
        differ by many optional fields, but by exactly one required one.
        """
        chosen: Dict[str, str] = {}
        taken = {snake_case(argument) for argument in arguments}
        for branch in branches_of(name, self.schemas):
            schema = self.schemas.get(branch) or {}
            own = [
                field
                for field in schema.get("properties") or {}
                if field not in shared
                and snake_case(field) not in taken
                and field in (schema.get("required") or [])
            ]
            if len(own) != 1:
                raise SpecError(
                    f"`{branch}` has {len(own)} required fields its sibling "
                    "branches lack, so there is no one field to choose it by. "
                    "Handle this body by hand."
                )
            chosen[branch] = own[0]
        return chosen

    def component_of(
        self, owner: str, field: str, strict: bool = True
    ) -> Optional[str]:
        """The component a field names, or the one its array holds."""
        schema = properties_of(owner, self.schemas).get(field)
        if schema is None:
            raise SpecError(f"`{owner}` declares no `{field}`.")
        if schema.get("type") == "array":
            schema = schema.get("items") or {}
        if "$ref" not in schema:
            if not strict:
                return None
            raise SpecError(
                f"`{owner}.{field}` is not a reference to a component schema, "
                "so there is no declared shape to convert it to."
            )
        return ref_name(schema["$ref"])

    def field_reader(self, argument: str, carried: str) -> str:
        """How one field of a held value is read, as a format string.

        A union's branches declare different fields, so a field only one of
        them carries is absent rather than None.
        """
        if branches_of(carried, self.schemas):
            return f"getattr({argument}, {{name!r}}, None)"
        return f"{argument}.{{name}}"

    def holds_many(self, owner: str, field: str) -> bool:
        return (properties_of(owner, self.schemas).get(field) or {}).get(
            "type"
        ) == "array"

    def sent_shape(
        self, field: str, sends: str, convert: Dict[str, str]
    ) -> Optional[str]:
        """The shape a held field has to become to be sent, or None.

        Pydantic will not read one model class as another, so a field the
        handle holds as a different shape is a failure at the first push rather
        than a type error. Naming the target in the YAML rather than resolving
        it means a rename upstream fails the build instead.
        """
        declared = self.component_of(sends, field, strict=False)
        held = self.component_of(self.name, field, strict=False)
        target = convert.get(field)
        if target is not None and target != declared:
            raise SpecError(
                f"{self.resource}: `{sends}.{field}` is sent as "
                f"`{declared}`, not "
                f"`{target}` as stateful_config.yml says."
            )
        if target is None and held != declared:
            raise SpecError(
                f"{self.resource}: the handle holds `{field}` as "
                f"`{held or 'a plain value'}` but `{sends}` sends "
                f"`{declared or 'a plain value'}`. Name the sent shape under "
                f"`convert` as `{field}: {declared}`."
            )
        return target

    def converter(self, carried: str, sends: str) -> str:
        """The name of the method turning one `carried` into one `sends`.

        Registering rather than rendering keeps one method per pair of shapes,
        however many bodies ask for it.
        """
        name = f"_{snake_case(sends)}"
        self.conversions[name] = (carried, sends)
        self.referenced.update({carried, sends})
        return name

    def undeclared(self, carried: str, sends: str) -> List[str]:
        """The carried fields the sent shape cannot hold.

        Every branch of a request body is `.strict()` upstream, so a field the
        held shape carries and the sent one does not is a rejected payload,
        not an ignored key.
        """
        return sorted(
            set(properties_of(carried, self.schemas))
            - set(properties_of(sends, self.schemas))
        )

    def held_value(
        self, field: str, target: Optional[str], optional: bool
    ) -> str:
        """How one held field is read into a body.

        A field the body can omit may be unset on the handle, so its conversion
        passes None through. A required one is checked for None beforehand.
        """
        held = f"self.{snake_case(field)}"
        if target is None:
            return held
        carried = self.component_of(self.name, field)
        converter = self.converter(carried, target)
        if not self.holds_many(self.name, field):
            converted = f"self.{converter}({held})"
        else:
            item = snake_case(singular(field))
            converted = f"[self.{converter}({item}) for {item} in {held}]"
        return (
            f"None if {held} is None else {converted}"
            if optional
            else converted
        )

    def ts_held_value(
        self, field: str, target: Optional[str], optional: bool
    ) -> str:
        held = f"this.{camel_case(field)}"
        if target is None:
            return held
        carried = self.component_of(self.name, field)
        converter = camel_case(self.converter(carried, target))
        if not self.holds_many(self.name, field):
            converted = f"this.{converter}({held})"
            if not optional:
                return converted
            return f"{held} === undefined ? undefined : {converted}"
        item = camel_case(singular(field))
        access = "?." if optional else "."
        return f"{held}{access}map(({item}) => this.{converter}({item}))"

    def call_param_types(
        self, sends: str, arguments: Sequence[str]
    ) -> Dict[str, str]:
        """A save argument's type, read off the body it is sent in."""
        wanted = [snake_case(name) for name in arguments]
        found: Dict[str, str] = {}
        for field, schema in properties_of(sends, self.schemas).items():
            if snake_case(field) in wanted:
                resolved = self.resolver.resolve(
                    schema, f"{sends}.{field}", pascal_case(f"{sends}.{field}")
                )
                self.referenced.update(resolved.deps)
                annotation = resolved.as_python(True)
                self.annotations.append(annotation)
                found[snake_case(field)] = annotation
        missing = [name for name in wanted if name not in found]
        if missing:
            raise SpecError(
                f"`{sends}` declares no {', '.join(missing)}, so it cannot be "
                "sent as an argument."
            )
        return found

    def ts_call_param_types(
        self, sends: str, arguments: Sequence[str]
    ) -> Dict[str, str]:
        """A save argument's type, read off the body it is sent in."""
        found = {}
        for field, schema in properties_of(sends, self.schemas).items():
            if camel_case(field) in arguments:
                resolved = self.resolver.resolve(
                    schema, f"{sends}.{field}", pascal_case(f"{sends}.{field}")
                )
                self.referenced.update(resolved.deps)
                found[camel_case(field)] = resolved.as_typescript()
        return found

    def guard(self, argument: str, carried: str, key: str) -> str:
        """The name of the method reading an optional identity off a value."""
        name = f"_{snake_case(argument)}_{snake_case(key)}"
        self.guards[name] = (argument, carried, key)
        return name

    def refusal(self, argument: str, key: str) -> str:
        """Why a value the handle holds cannot name a row yet."""
        held = snake_case(self.name).replace("_", " ")
        return (
            f"This {argument} has no {key}, so it is not in this {held} yet. "
            "Push it first."
        )

    # ===== One method per block of the YAML =====

    def render_delegate(self, exposed: str, operation: str) -> List[str]:
        method = self.method(operation)
        self.note(method)
        held = self.held(method)
        summary, description, documented = method.prose
        documented = [entry for entry in documented if entry[0] != held]

        lines: List[str] = []
        for is_async in (False, True):
            arguments = [f"self._{self.identity['field']}()"]
            arguments += [
                p.name
                for p in method.parameters
                if not p.keyword and p.name != held
            ]
            arguments += [
                f"{p.name}={p.name}" for p in method.parameters if p.keyword
            ]
            target = f"a_{method.name}" if is_async else method.name
            lines.append("")
            lines.append(
                f"    {'async def a_' if is_async else 'def '}{exposed}"
                f"({', '.join(self.aliased(a) for a in method.signature(skip=(held,)))})"
                f" -> {self.aliased(method.returns)}:"
            )
            lines.extend(
                render_docstring(
                    summary, description, documented, " " * 8, self.descriptive
                )
            )
            lines.append(
                f"        return {'await ' if is_async else ''}"
                f"self._client.{target}({', '.join(arguments)})"
            )
        return lines

    def ts_delegate(self, exposed: str, operation: str) -> List[str]:
        method = self.method(operation)
        self.referenced.update(method.named_types)
        held = self.held(method)
        summary, description, documented = method.prose
        documented = [entry for entry in documented if entry[0] != held]
        field = camel_case(self.identity["field"])

        arguments = [f"this.{field}OrThrow()"]
        arguments += [
            p.ts_name
            for p in method.parameters
            if p.name != held and p.required
        ]
        # The handle and the client it calls gather their optionals at the
        # same threshold, so an options object passes straight through. The
        # other branches keep the two honest if that ever stops holding.
        optional = method.ts_optional(skip=(held,))
        if method.ts_takes_options() and method.ts_takes_options(skip=(held,)):
            arguments.append("options")
        elif method.ts_takes_options():
            entries = ", ".join(p.ts_name for p in optional)
            arguments.append(f"{{ {entries} }}")
        elif method.ts_takes_options(skip=(held,)):
            arguments += [f"options.{p.ts_name}" for p in optional]
        else:
            arguments += [p.ts_name for p in optional]
        lines = [""]
        lines.extend(
            render_jsdoc(
                summary, description, documented, "  ", self.descriptive
            )
        )
        lines.append(
            f"  async {camel_case(exposed)}"
            f"({', '.join(self.aliased(a) for a in method.ts_signature(skip=(held,)))})"
            f": Promise<{self.aliased(method.ts_returns)}> {{"
        )
        lines.append(
            f"    return this.client.{method.ts_name}({', '.join(arguments)});"
        )
        lines.append("  }")
        return lines

    def render_on_item(self, exposed: str, item: Dict[str, Any]) -> List[str]:
        """An operation over one item of the handle's state.

        The caller passes the item it already holds, so the item's own
        identity fills the path parameter the handle's does not, and its
        fields become the body.
        """
        method = self.method(item["operation"])
        self.note(method)
        held = self.held(method)
        argument = item["argument"]
        carried = item["type"]
        key = item["identity"]["field"]
        self.referenced.add(carried)

        if key not in properties_of(carried, self.schemas):
            raise SpecError(
                f"{self.resource}.{exposed}: `{carried}` declares no "
                f"`{key}`, so "
                "it cannot fill a path parameter."
            )
        assured = key in required_of(carried, self.schemas)
        filled = [
            p.wire
            for p in method.parameters
            if p.name != held and p.source == "path"
        ]
        if filled != [item["identity"]["parameter"]]:
            raise SpecError(
                f"{item['operation']}: an item method fills one path "
                f"parameter from `{argument}`, but besides the identity this "
                f"route takes {filled or 'none'}."
            )

        sends = request_type(self.route(item["operation"]))
        read = self.field_reader(argument, carried)

        call: List[str] = []
        for parameter in method.parameters:
            if parameter.name == held:
                call.append(f"self._{self.identity['field']}()")
            elif parameter.source == "path":
                call.append(
                    f"{argument}.{snake_case(key)}"
                    if assured
                    else f"self.{self.guard(argument, carried, key)}"
                    f"({argument})"
                )
            elif parameter.source == "union-body" and carried == sends:
                call.append(argument)
            elif parameter.source == "union-body":
                call.append(
                    f"self.{self.converter(carried, sends)}({argument})"
                )
            elif parameter.source == "body":
                value = read.format(name=parameter.name)
                call.append(
                    f"{parameter.name}={value}" if parameter.keyword else value
                )
            else:
                raise SpecError(
                    f"{item['operation']}: `{parameter.name}` is a "
                    f"{parameter.source} parameter, which neither the handle "
                    f"nor `{argument}` can fill."
                )

        summary, description, _ = method.prose
        documented = [
            (argument, (self.schemas.get(carried) or {}).get("description"))
        ]
        lines: List[str] = []
        for is_async in (False, True):
            target = f"a_{method.name}" if is_async else method.name
            lines.append("")
            lines.append(
                f"    {'async def a_' if is_async else 'def '}{exposed}"
                f"(self, {argument}: {self.aliased(carried)}) -> "
                f"{self.aliased(method.returns)}:"
            )
            lines.extend(
                render_docstring(
                    summary, description, documented, " " * 8, self.descriptive
                )
            )
            lines.append(
                f"        return {'await ' if is_async else ''}"
                f"self._client.{target}({', '.join(call)})"
            )
        return lines

    def ts_on_item(self, exposed: str, item: Dict[str, Any]) -> List[str]:
        method = self.method(item["operation"])
        self.referenced.update(method.named_types)
        held = self.held(method)
        argument = camel_case(item["argument"])
        carried = item["type"]
        key = item["identity"]["field"]
        field = camel_case(self.identity["field"])
        self.referenced.add(carried)

        sends = request_type(self.route(item["operation"]))
        union = bool(branches_of(carried, self.schemas))

        ordered = [p for p in method.parameters if p.required]
        ordered += [p for p in method.parameters if not p.required]
        call: List[str] = []
        for parameter in ordered:
            if parameter.name == held:
                call.append(f"this.{field}OrThrow()")
            elif parameter.source == "path":
                call.append(
                    f"{argument}.{camel_case(key)}"
                    if key in required_of(carried, self.schemas)
                    else f"this."
                    f"{camel_case(self.guard(argument, carried, key))}OrThrow"
                    f"({argument})"
                )
            elif parameter.source == "union-body" and carried == sends:
                call.append(argument)
            elif parameter.source == "union-body":
                call.append(
                    f"this.{camel_case(self.converter(carried, sends))}"
                    f"({argument})"
                )
            elif parameter.source == "body":
                call.append(
                    f"({argument} as unknown as Record<string, unknown>)"
                    f'["{parameter.wire}"] as {parameter.typescript}'
                    if union
                    else f"{argument}.{parameter.ts_name}"
                )
            else:
                raise SpecError(
                    f"{item['operation']}: `{parameter.name}` is a "
                    f"{parameter.source} parameter, which neither the handle "
                    f"nor `{argument}` can fill."
                )

        summary, description, _ = method.prose
        documented = [
            (argument, (self.schemas.get(carried) or {}).get("description"))
        ]
        lines = [""]
        lines.extend(
            render_jsdoc(
                summary, description, documented, "  ", self.descriptive
            )
        )
        lines.append(
            f"  async {camel_case(exposed)}({argument}: {self.aliased(carried)})"
            f": Promise<{self.aliased(method.ts_returns)}> {{"
        )
        lines.append(
            f"    return this.client.{method.ts_name}({', '.join(call)});"
        )
        lines.append("  }")
        return lines

    def render_load_one(self, exposed: str, load: Dict[str, Any]) -> List[str]:
        """A load over a single operation, which narrows by keyword alone."""
        method = self.method(load["operation"])
        self.note(method)
        held = self.held(method)
        kept = [p for p in method.parameters if p.name != held]
        if any(not p.keyword for p in kept):
            raise SpecError(
                f"{load['operation']}: a load over one operation can take "
                "no argument besides the identity and its keywords."
            )

        summary, description, documented = method.prose
        documented = [entry for entry in documented if entry[0] != held]
        signature = ["self"] + (
            ["*"] + [p.declaration() for p in kept] if kept else []
        )

        lines: List[str] = []
        for is_async in (False, True):
            target = f"a_{method.name}" if is_async else method.name
            arguments = [f"self._{self.identity['field']}()"]
            arguments += [f"{p.name}={p.name}" for p in kept]
            lines.append("")
            lines.append(
                f"    {'async def a_' if is_async else 'def '}{exposed}"
                f"({', '.join(signature)}) -> \"{self.name}\":"
            )
            lines.extend(
                render_docstring(
                    summary, description, documented, " " * 8, self.descriptive
                )
            )
            lines.append(
                f"        payload = {'await ' if is_async else ''}"
                f"self._client.{target}({', '.join(arguments)})"
            )
            lines.extend(["        self._load(payload)", "        return self"])
        return lines

    def ts_load_one(self, exposed: str, load: Dict[str, Any]) -> List[str]:
        method = self.method(load["operation"])
        self.referenced.update(method.named_types)
        held = self.held(method)
        field = camel_case(self.identity["field"])
        kept = [p for p in method.parameters if p.name != held and p.required]
        kept += [
            p for p in method.parameters if p.name != held and not p.required
        ]

        summary, description, _ = method.prose
        described = dict(method.documented)
        documented = [(p.ts_name, described.get(p.name)) for p in kept]
        options = "; ".join(p.ts_declaration() for p in kept)
        default = "" if any(p.required for p in kept) else " = {}"
        signature = f"options: {{ {options} }}{default}" if kept else ""

        lines = [""]
        lines.extend(
            render_jsdoc(
                summary, description, documented, "  ", self.descriptive
            )
        )
        lines.append(
            f"  async {camel_case(exposed)}({signature}): Promise<this> {{"
        )
        arguments = [f"this.{field}OrThrow()"]
        arguments += [f"options.{p.ts_name}" for p in kept]
        lines.append(
            f"    const payload = await this.client.{method.ts_name}"
            f"({', '.join(arguments)});"
        )
        lines.extend(["    this.load(payload);", "    return this;", "  }"])
        return lines

    def render_load(self, exposed: str, load: Dict[str, Any]) -> List[str]:
        if "by" not in load:
            return self.render_load_one(exposed, load)
        by = load["by"]
        defaults = [key for key, entry in by.items() if "default" in entry]
        if len(defaults) != 1:
            raise SpecError(
                f"{self.resource}.{exposed}: exactly one branch must carry a "
                f"`default`; {len(defaults)} do."
            )
        fallback = defaults[0]

        # Each branch's operation takes the identity plus exactly one more path
        # parameter, which is what the branch's keyword supplies.
        chosen: Dict[str, Tuple[Any, str]] = {}
        extra: Dict[str, Tuple[Any, Any]] = {}
        documented: List[Tuple[str, Optional[str]]] = []
        narrowing: List[Tuple[str, Optional[str]]] = []
        for key, entry in by.items():
            method = self.method(entry["operation"])
            self.note(method)
            held = self.held(method)
            positional = [
                p for p in method.parameters if not p.keyword and p.name != held
            ]
            if len(positional) != 1:
                raise SpecError(
                    f"{entry['operation']}: a load branch must take exactly "
                    f"one argument besides the identity; it takes "
                    f"{len(positional)}."
                )
            chosen[key] = (method, positional[0].name)
            described = dict(method.documented)
            hint = described.get(positional[0].name)
            if key == fallback:
                hint = f"{hint} Defaults to `{entry['default']}`."
            documented.append((key, hint))
            for parameter in method.parameters:
                if parameter.keyword and parameter.name not in extra:
                    extra[parameter.name] = (method, parameter)
                    narrowing.append(
                        (
                            parameter.name,
                            f"{described.get(parameter.name)} Only valid "
                            f"with `{key}`.",
                        )
                    )
        documented.extend(narrowing)

        signature = ["self", "*"]
        signature += [f"{key}: Optional[str] = None" for key in by]
        signature += [
            parameter.declaration() for _, parameter in extra.values()
        ]
        self.annotations.extend(
            parameter.annotation for _, parameter in extra.values()
        )

        keys = list(by)
        listed = ", ".join(keys)
        state = self.schemas.get(self.name) or {}
        description = " ".join(
            part
            for part in (
                state.get("description"),
                f"Pass at most one of {listed}; this object is filled in "
                "from the result.",
            )
            if part
        )

        lines: List[str] = []
        for is_async in (False, True):
            await_ = "await " if is_async else ""
            lines.append("")
            lines.append(
                f"    {'async def a_' if is_async else 'def '}{exposed}"
                f"({', '.join(signature)}) -> \"{self.name}\":"
            )
            lines.extend(
                render_docstring(
                    exposed.replace("_", " ").title(),
                    description,
                    documented,
                    " " * 8,
                    self.descriptive,
                )
            )
            lines.append(
                f"        given = [name for name, value in "
                f"({', '.join(f'({k!r}, {k})' for k in keys)},) "
                "if value is not None]"
            )
            lines.extend(
                [
                    "        if len(given) > 1:",
                    "            raise ValueError(",
                    f'                f"Provide at most one of {listed}; got '
                    "{', '.join(given)}.\"",
                    "            )",
                ]
            )
            for name, (method, _) in extra.items():
                owner = next(
                    key
                    for key, (chosen_method, _) in chosen.items()
                    if chosen_method is method
                )
                lines.extend(
                    [
                        f"        if {name} is not None and given and given "
                        f"!= [{owner!r}]:",
                        "            raise ValueError(",
                        f'                f"`{name}` narrows a {owner} lookup, '
                        'so it cannot be combined with {given[0]}."',
                        "            )",
                    ]
                )
            lines.append(
                f"        {self.identity['field']} = "
                f"self._{self.identity['field']}()"
            )
            branch = "if"
            for key in keys:
                if key == fallback:
                    continue
                method, _ = chosen[key]
                target = f"a_{method.name}" if is_async else method.name
                lines.append(f"        {branch} {key} is not None:")
                lines.append(
                    f"            payload = {await_}self._client.{target}"
                    f"({self.identity['field']}, {key})"
                )
                branch = "elif"
            method, _ = chosen[fallback]
            target = f"a_{method.name}" if is_async else method.name
            arguments = [
                self.identity["field"],
                f"{fallback} or {by[fallback]['default']!r}",
            ] + [f"{name}={name}" for name in extra]
            lines.append("        else:")
            lines.append(
                f"            payload = {await_}self._client.{target}"
                f"({', '.join(arguments)})"
            )
            lines.extend(["        self._load(payload)", "        return self"])
        return lines

    def ts_load(self, exposed: str, load: Dict[str, Any]) -> List[str]:
        if "by" not in load:
            return self.ts_load_one(exposed, load)
        by = load["by"]
        fallback = next(key for key, entry in by.items() if "default" in entry)
        field = camel_case(self.identity["field"])

        chosen: Dict[str, Any] = {}
        extra: Dict[str, Any] = {}
        documented: List[Tuple[str, Optional[str]]] = []
        narrowing: List[Tuple[str, Optional[str]]] = []
        for key, entry in by.items():
            method = self.method(entry["operation"])
            self.referenced.update(method.named_types)
            held = self.held(method)
            described = dict(method.documented)
            positional = [
                p for p in method.parameters if not p.keyword and p.name != held
            ]
            chosen[key] = method
            hint = described.get(positional[0].name)
            if key == fallback:
                hint = f"{hint} Defaults to `{entry['default']}`."
            documented.append((key, hint))
            for parameter in method.parameters:
                if parameter.keyword and parameter.ts_name not in extra:
                    extra[parameter.ts_name] = (key, parameter)
                    narrowing.append(
                        (
                            parameter.ts_name,
                            f"{described.get(parameter.name)} Only valid "
                            f"with `{key}`.",
                        )
                    )
        documented.extend(narrowing)

        keys = list(by)
        listed = ", ".join(keys)
        fields = [f"{key}?: string" for key in keys]
        fields += [
            f"{name}?: {parameter.typescript}"
            for name, (_, parameter) in extra.items()
        ]
        state = self.schemas.get(self.name) or {}
        description = " ".join(
            part
            for part in (
                state.get("description"),
                f"Pass at most one of {listed}; this object is filled in "
                "from the result.",
            )
            if part
        )

        lines = [""]
        lines.extend(
            render_jsdoc(
                exposed.title(), description, documented, "  ", self.descriptive
            )
        )
        lines.append(
            f"  async {camel_case(exposed)}(options: {{ {'; '.join(fields)} }} "
            f"= {{}}): Promise<this> {{"
        )
        listed_keys = ", ".join(f'"{key}"' for key in keys)
        lines.append(f"    const given = ([{listed_keys}] as const).filter(")
        lines.append("      (name) => options[name] !== undefined,")
        lines.append("    );")
        lines.extend(
            [
                "    if (given.length > 1) {",
                "      throw new Error(",
                f"        `Provide at most one of {listed}; got "
                '${given.join(", ")}.`,',
                "      );",
                "    }",
            ]
        )
        for name, (owner, _) in extra.items():
            lines.extend(
                [
                    f"    if (options.{name} !== undefined && given.length "
                    f'&& given[0] !== "{owner}") {{',
                    "      throw new Error(",
                    f"        `\\`{name}\\` narrows a {owner} lookup, so it "
                    "cannot be combined with ${given[0]}.`,",
                    "      );",
                    "    }",
                ]
            )
        lines.append(f"    const {field} = this.{field}OrThrow();")
        payload = f"{self.name}Payload"
        lines.append(f"    let payload: {payload};")
        branch = "if"
        for key in keys:
            if key == fallback:
                continue
            method = chosen[key]
            lines.append(f"    {branch} (options.{key} !== undefined) {{")
            lines.append(
                f"      payload = await this.client.{method.ts_name}"
                f"({field}, options.{key});"
            )
            lines.append("    }")
            branch = "else if"
        method = chosen[fallback]
        arguments = [
            field,
            f"options.{fallback} ?? {by[fallback]['default']!r}".replace(
                "'", '"'
            ),
        ] + [f"options.{name}" for name in extra]
        lines.extend(
            [
                "    else {",
                f"      payload = await this.client.{method.ts_name}"
                f"({', '.join(arguments)});",
                "    }",
                "    this.load(payload);",
                "    return this;",
                "  }",
            ]
        )
        return lines

    def render_save(self, exposed: str, save: Dict[str, Any]) -> List[str]:
        method = self.method(save["operation"])
        self.note(method)
        sends = request_type(self.route(save["operation"]))
        arguments = [snake_case(name) for name in save.get("call_params") or []]
        mapping = save.get("response_mapping") or {}
        self.referenced.add(sends)

        described = dict(method.documented)
        documented = [(name, described.get(name)) for name in arguments]
        typed = self.call_param_types(sends, arguments)
        signature = ["self"] + (
            ["*"] + [f"{name}: {typed[name]} = None" for name in arguments]
            if arguments
            else []
        )

        body_method = f"_{exposed}_body"
        whole = any(p.source == "union-body" for p in method.parameters)
        identity = f"self._{self.identity['field']}()"
        spread = [
            identity if p.source == "path" else f"body.{p.name}"
            for p in method.parameters
            if not p.keyword
        ]
        spread += [
            f"{p.name}=body.{p.name}" for p in method.parameters if p.keyword
        ]

        lines: List[str] = []
        for is_async in (False, True):
            summary, description, _ = method.prose
            target = f"a_{method.name}" if is_async else method.name
            call = ", ".join(f"{name}={name}" for name in arguments)
            lines.append("")
            lines.append(
                f"    {'async def a_' if is_async else 'def '}{exposed}"
                f"({', '.join(signature)}) -> {self.aliased(method.returns)}:"
            )
            lines.extend(
                render_docstring(
                    summary, description, documented, " " * 8, self.descriptive
                )
            )
            held = [identity for p in method.parameters if p.source == "path"]
            sent = (
                ", ".join(held + [f"self.{body_method}({call})"])
                if whole
                else ", ".join(spread)
            )
            if not whole:
                lines.append(f"        body = self.{body_method}({call})")
            lines.append(
                f"        result = {'await ' if is_async else ''}"
                f"self._client.{target}({sent})"
            )
            for field, wire in mapping.items():
                lines.append(
                    f"        self.{field} = result.{snake_case(wire)}"
                )
            lines.append("        return result")

        lines.extend(
            self.render_body(
                body_method,
                sends,
                arguments,
                signature,
                save.get("sent_as") or {},
            )
        )
        return lines

    def ts_save(self, exposed: str, save: Dict[str, Any]) -> List[str]:
        method = self.method(save["operation"])
        self.referenced.update(method.named_types)
        sends = request_type(self.route(save["operation"]))
        self.referenced.add(sends)
        arguments = [camel_case(name) for name in save.get("call_params") or []]
        mapping = save.get("response_mapping") or {}
        summary, description, _ = method.prose
        described = dict(method.documented)
        documented = [(name, described.get(name)) for name in arguments]

        convert = save.get("sent_as") or {}
        typed = self.ts_call_param_types(sends, arguments)
        options = "; ".join(f"{name}?: {typed[name]}" for name in arguments)
        signature = f"options: {{ {options} }} = {{}}" if arguments else ""

        lines = [""]
        lines.extend(
            render_jsdoc(
                summary, description, documented, "  ", self.descriptive
            )
        )
        lines.append(
            f"  async {camel_case(exposed)}({signature})"
            f": Promise<{self.aliased(method.ts_returns)}> {{"
        )
        call = ", ".join(f"options.{name}" for name in arguments)
        whole = any(p.source == "union-body" for p in method.parameters)
        ordered = [p for p in method.parameters if p.required]
        ordered += [p for p in method.parameters if not p.required]
        identity = f"this.{camel_case(self.identity['field'])}OrThrow()"
        held = [identity for p in method.parameters if p.source == "path"]
        if whole:
            sent = held + [f"this.{camel_case(exposed)}Body({call})"]
            lines.append(
                f"    const result = await this.client.{method.ts_name}("
                + ", ".join(sent)
                + ");"
            )
        else:
            lines.append(
                f"    const body = this.{camel_case(exposed)}Body({call});"
            )
            sent = [
                identity if p.source == "path" else f"body.{p.ts_name}"
                for p in ordered
            ]
            lines.append(
                f"    const result = await this.client.{method.ts_name}("
                + ", ".join(sent)
                + ");"
            )
        for handle_field, wire in mapping.items():
            lines.append(
                f"    this.{camel_case(handle_field)} = result.{wire};"
            )
        lines.extend(["    return result;", "  }"])
        lines.extend(self.ts_body(exposed, sends, arguments, convert))
        return lines

    def ts_helper(self, exposed: str, function: str) -> List[str]:
        return [
            "",
            f"  {camel_case(exposed)}(values: Record<string, unknown>) {{",
            f"    return {function}(this, values);",
            "  }",
        ]

    # ===== The methods those generate in turn =====

    def render_body(
        self,
        name: str,
        sends: str,
        arguments: Sequence[str],
        signature: Sequence[str],
        convert: Optional[Dict[str, str]] = None,
    ) -> List[str]:
        """The method that turns the handle's state into one request body."""
        branches = branches_of(sends, self.schemas)
        required = required_of(sends, self.schemas)
        shared = [
            field
            for field in properties_of(sends, self.schemas)
            if snake_case(field) not in arguments
            and field != MEDIA_MAPPING_FIELD
            and all(
                field in ((self.schemas.get(b) or {}).get("properties") or {})
                for b in branches or [sends]
            )
        ]

        lines = [
            "",
            f"    def {name}({', '.join(signature)}) -> {self.aliased(sends)}:",
        ]
        for field in shared:
            if field in required:
                lines.extend(
                    [
                        f"        if self.{snake_case(field)} is None:",
                        "            raise ValueError(",
                        f'                "Set {snake_case(field)} before '
                        f'calling {name.strip("_").replace("_body", "")}."',
                        "            )",
                    ]
                )

        convert = convert or {}
        assigned = ", ".join(
            [
                f'"{snake_case(field)}": '
                + self.held_value(
                    field,
                    self.sent_shape(field, sends, convert),
                    field not in required,
                )
                for field in shared
            ]
            + [f'"{snake_case(field)}": {field}' for field in arguments]
        )
        lines.append(f"        fields = {{{assigned}}}")

        if not branches:
            lines.append(f"        return {sends}(**fields)")
            return lines

        discriminators = self.discriminators(sends, shared, arguments)

        listed = ", ".join(
            snake_case(field) for field in discriminators.values()
        )
        lines.extend(
            [
                "        chosen = [name for name, value in ("
                + ", ".join(
                    f"({snake_case(f)!r}, self.{snake_case(f)})"
                    for f in discriminators.values()
                )
                + ",) if value is not None]",
                "        if len(chosen) != 1:",
                "            raise ValueError(",
                f'                "Set exactly one of {listed}; "',
                '                + (", ".join(chosen) if chosen else "none is set")',
                "            )",
            ]
        )
        for index, (branch, field) in enumerate(discriminators.items()):
            keyword = "if" if index == 0 else "elif"
            attribute = snake_case(field)
            if index == len(discriminators) - 1:
                lines.append(
                    f"        return {branch}({attribute}=self.{attribute}, **fields)"
                )
            else:
                lines.extend(
                    [
                        f"        {keyword} self.{attribute} is not None:",
                        f"            return {branch}"
                        f"({attribute}=self.{attribute}, **fields)",
                    ]
                )
            self.referenced.add(branch)
        return lines

    def ts_body(
        self,
        exposed: str,
        sends: str,
        arguments: Sequence[str],
        convert: Optional[Dict[str, str]] = None,
    ) -> List[str]:
        branches = branches_of(sends, self.schemas)
        required = required_of(sends, self.schemas)
        shared = [
            field
            for field in properties_of(sends, self.schemas)
            if camel_case(field) not in arguments
            and field != MEDIA_MAPPING_FIELD
            and all(
                field in ((self.schemas.get(b) or {}).get("properties") or {})
                for b in branches or [sends]
            )
        ]
        typed = self.ts_call_param_types(sends, arguments)
        parameters = ", ".join(f"{name}?: {typed[name]}" for name in arguments)

        lines = [
            "",
            f"  private {camel_case(exposed)}Body({parameters}): "
            f"{self.aliased(sends)} {{",
        ]
        for field in shared:
            if field in required:
                lines.extend(
                    [
                        f"    if (this.{field} === undefined) {{",
                        f'      throw new Error("Set {field} before calling '
                        f'{exposed}.");',
                        "    }",
                    ]
                )
        convert = convert or {}
        assigned = ", ".join(
            [
                ts_key(
                    field,
                    self.ts_held_value(
                        field,
                        self.sent_shape(field, sends, convert),
                        field not in required,
                    ),
                )
                for field in shared
            ]
            + [ts_key(name, name) for name in arguments]
        )
        lines.append(f"    const fields = {{ {assigned} }};")

        if not branches:
            lines.extend([f"    return fields as {sends};", "  }"])
            return lines

        discriminators = self.discriminators(sends, shared, arguments)

        listed = ", ".join(discriminators.values())
        lines.extend(
            [
                "    const chosen = (["
                + ", ".join(f'"{f}"' for f in discriminators.values())
                + "] as const).filter(",
                "      (name) => this[name] !== undefined,",
                "    );",
                "    if (chosen.length !== 1) {",
                "      throw new Error(",
                f"        `Set exactly one of {listed}; "
                '${chosen.length ? chosen.join(", ") : "none is set"}.`,',
                "      );",
                "    }",
            ]
        )
        for index, (branch, mark) in enumerate(discriminators.items()):
            self.referenced.add(branch)
            built = (
                f"{{ ...fields, {mark}: this.{mark} }} as unknown as {branch}"
            )
            if index == len(discriminators) - 1:
                lines.append(f"    return {built};")
            else:
                lines.extend(
                    [
                        f"    if (this.{mark} !== undefined) {{",
                        f"      return {built};",
                        "    }",
                    ]
                )
        lines.append("  }")
        return lines

    def render_conversion(
        self, name: str, carried: str, sends: str
    ) -> List[str]:
        """The method that re-reads one held shape as the shape a body sends.

        Pydantic will not read one model class as another, so the value is
        dumped and validated back rather than passed through.
        """
        argument = snake_case(carried)
        read = self.field_reader(argument, carried)

        lines = [
            "",
            f"    def {name}(self, {argument}: {self.aliased(carried)}) -> "
            f"{self.aliased(sends)}:",
            f"        fields = {argument}.model_dump(",
            '            mode="json", by_alias=True, exclude_none=True',
            "        )",
        ]
        dropped = self.undeclared(carried, sends)
        if dropped and self.descriptive:
            lines.append(
                f"        # A {carried} carries fields a {sends} has no room "
                "for."
            )
        lines.extend(
            f"        fields.pop({field!r}, None)" for field in dropped
        )

        discriminators = self.discriminators(sends, self.shared_fields(sends))
        if not discriminators:
            lines.append(f"        return {sends}(**fields)")
            return lines

        carried_fields = properties_of(carried, self.schemas)
        for branch, field in discriminators.items():
            if field not in carried_fields:
                raise SpecError(
                    f"`{branch}` is chosen by `{field}`, which `{carried}` "
                    "never declares, so nothing held could ever choose it."
                )

        listed = ", ".join(snake_case(f) for f in discriminators.values())
        lines.extend(
            [
                "        chosen = [name for name, value in ("
                + ", ".join(
                    f"({snake_case(f)!r}, {read.format(name=snake_case(f))})"
                    for f in discriminators.values()
                )
                + ",) if value is not None]",
                "        if len(chosen) != 1:",
                "            raise ValueError(",
                f'                "Set exactly one of {listed}; "',
                '                + (", ".join(chosen) if chosen else "none is set")',
                "            )",
            ]
        )
        for index, (branch, field) in enumerate(discriminators.items()):
            self.referenced.add(branch)
            if index == len(discriminators) - 1:
                lines.append(f"        return {branch}(**fields)")
            else:
                lines.extend(
                    [
                        f"        if {read.format(name=snake_case(field))} "
                        "is not None:",
                        f"            return {branch}(**fields)",
                    ]
                )
        return lines

    def ts_conversion(self, name: str, carried: str, sends: str) -> List[str]:
        argument = camel_case(carried)
        name = camel_case(name)
        lines = [
            "",
            f"  private {name}({argument}: {self.aliased(carried)}): "
            f"{self.aliased(sends)} {{",
            f"    const source = {argument} as unknown as "
            "Record<string, unknown>;",
            "    const fields = { ...source };",
        ]
        dropped = self.undeclared(carried, sends)
        if dropped and self.descriptive:
            lines.append(
                f"    // A {carried} carries fields a {sends} has no room for."
            )
        lines.extend(f'    delete fields["{field}"];' for field in dropped)

        discriminators = self.discriminators(sends, self.shared_fields(sends))
        if not discriminators:
            lines.extend([f"    return fields as unknown as {sends};", "  }"])
            return lines

        listed = ", ".join(discriminators.values())
        lines.extend(
            [
                "    const chosen = (["
                + ", ".join(f'"{f}"' for f in discriminators.values())
                + "] as const).filter(",
                "      (name) => source[name] !== undefined,",
                "    );",
                "    if (chosen.length !== 1) {",
                "      throw new Error(",
                f"        `Set exactly one of {listed}; "
                '${chosen.length ? chosen.join(", ") : "none is set"}.`,',
                "      );",
                "    }",
            ]
        )
        for index, (branch, mark) in enumerate(discriminators.items()):
            self.referenced.add(branch)
            built = f"fields as unknown as {branch}"
            if index == len(discriminators) - 1:
                lines.append(f"    return {built};")
            else:
                lines.extend(
                    [
                        f'    if (source["{mark}"] !== undefined) {{',
                        f"      return {built};",
                        "    }",
                    ]
                )
        lines.append("  }")
        return lines

    def render_guard(
        self, name: str, argument: str, carried: str, key: str
    ) -> List[str]:
        read = f"{argument}.{snake_case(key)}"
        return [
            "",
            f"    def {name}(self, {argument}: {self.aliased(carried)}) -> str:",
            f"        if {read} is None:",
            "            raise ValueError(",
            f'                "{self.refusal(argument, snake_case(key))}"',
            "            )",
            f"        return {read}",
        ]

    def ts_render_guard(
        self, name: str, argument: str, carried: str, key: str
    ) -> List[str]:
        argument = camel_case(argument)
        read = f"{argument}.{camel_case(key)}"
        return [
            "",
            f"  private {camel_case(name)}OrThrow({argument}: {self.aliased(carried)})"
            ": string {",
            f"    if ({read} === undefined) {{",
            "      throw new Error(",
            f'        "{self.refusal(argument, camel_case(key))}",',
            "      );",
            "    }",
            f"    return {read};",
            "  }",
        ]

    # ===== Assembling the class =====

    def render(self) -> str:
        config = self.config
        field = self.identity["field"]
        state = self.state_fields()
        held = {field, *(snake_case(seed) for seed in self.takes)}

        body: List[str] = []
        for exposed, operation in (config.get("delegate") or {}).items():
            body.extend(self.render_delegate(exposed, operation))
        for exposed, item in (config.get("on_item") or {}).items():
            body.extend(self.render_on_item(exposed, item))
        for exposed, load in (config.get("load") or {}).items():
            body.extend(self.render_load(exposed, load))
        for exposed, save in (config.get("save") or {}).items():
            body.extend(self.render_save(exposed, save))

        union = bool(branches_of(self.name, self.schemas))
        loaded = self.load_lines(union)
        for name, guarded in self.guards.items():
            body.extend(self.render_guard(name, *guarded))
        for name, (carried, sends) in self.conversions.items():
            body.extend(self.render_conversion(name, carried, sends))

        helpers = config.get("helpers") or {}
        for exposed, function in helpers.items():
            body.extend(
                [
                    "",
                    # Bound as-is rather than wrapped: the helper's own
                    # signature and docstring are what a caller should see.
                    f"    {exposed} = {function}",
                ]
            )

        lines: List[str] = []
        typing_names = typing_imports(self.annotations + ["Optional"])
        lines.extend([f"from typing import {', '.join(typing_names)}", ""])
        lines.append(f"from {PYTHON_PACKAGE}.api import Api")
        lines.append(f"from {self.client_module} import {self.client_class}")
        if helpers:
            lines.append(
                f"from {HELPERS_MODULE} import {', '.join(sorted(helpers.values()))}"
            )

        for owner, names in sorted(self.grouped().items()):
            renamed = [
                f"{name} as {name}Payload" if name == self.name else name
                for name in sorted(names)
            ]
            lines.append(
                f"from {python_module_for(owner)} import ({', '.join(renamed)})"
            )

        payload = f"{self.name}Payload"
        lines.extend(
            [
                "",
                "",
                f"class {self.name}:",
                *(
                    [
                        f'    """One {snake_case(self.name).replace("_", " ")} '
                        f"of your project, held by its {field}.",
                        "",
                        f"    Its methods are {self.client_class}'s, minus the",
                        f"    `{self.identity['parameter']}` that this object "
                        "supplies.",
                        '    """',
                        "",
                    ]
                    if self.descriptive
                    else []
                ),
                "    def __init__(",
                "        self,",
                "        api: Api,",
                "        *,",
                f"        {field}: Optional[str] = None,",
            ]
        )
        lines += [
            f"        {seed}: {annotation} = None,"
            for seed, annotation in state
            if seed in held and seed != field
        ]
        lines.extend(
            [
                "    ) -> None:",
                f"        self._client = {self.client_class}(api)",
                f"        self.{field}: Optional[str] = {field}",
            ]
        )
        for name, annotation in state:
            if name == field:
                continue
            value = name if name in held else "None"
            lines.append(f"        self.{name}: {annotation} = {value}")

        shown = ", ".join(
            f"{name}={{self.{name}!r}}"
            for name in [field] + sorted(held - {field})
        )
        lines.extend(
            [
                "",
                "    def __repr__(self) -> str:",
                f'        return f"{self.name}({shown})"',
            ]
        )
        lines.extend(body)

        lines.extend(["", f"    def _load(self, payload: {payload}) -> None:"])
        if union and self.descriptive:
            lines.extend(
                [
                    "        # The payload is one branch of a union, so a "
                    "field only the other",
                    "        # branch declares is absent rather than None.",
                ]
            )
        lines.extend(loaded)

        lines.extend(
            [
                "",
                f"    def _{field}(self) -> str:",
                f"        if self.{field} is None:",
                "            raise ValueError(",
                f'                "This {snake_case(self.name).replace("_", " ")} '
                f'has no {field}. Initialize it with "',
                f'                "client.{config["client_method"]["name"]}'
                f'({field}=...), or create it first."',
                "            )",
                f"        return self.{field}",
            ]
        )

        if self.resolver.promoted_objects or self.resolver.promoted_enums:
            raise SpecError(
                f"{self.resource}: a stateful field declares an inline shape, "
                "which has no generated type to name. Give it a $ref upstream."
            )
        return "\n".join(lines)

    def ts_render(self, path: str) -> str:
        config = self.config
        field = camel_case(self.identity["field"])
        takes = [camel_case(seed) for seed in self.takes]
        state = self.ts_state_fields()

        body: List[str] = []
        for exposed, operation in (config.get("delegate") or {}).items():
            body.extend(self.ts_delegate(exposed, operation))
        for exposed, item in (config.get("on_item") or {}).items():
            body.extend(self.ts_on_item(exposed, item))
        for exposed, load in (config.get("load") or {}).items():
            body.extend(self.ts_load(exposed, load))
        for exposed, save in (config.get("save") or {}).items():
            body.extend(self.ts_save(exposed, save))

        loaded = self.ts_load_lines()
        for name, guarded in self.guards.items():
            body.extend(self.ts_render_guard(name, *guarded))
        for name, (carried, sends) in self.conversions.items():
            body.extend(self.ts_conversion(name, carried, sends))
        for exposed, function in (config.get("helpers") or {}).items():
            body.extend(self.ts_helper(exposed, camel_case(function)))

        client = ts_import(path, f"{ts_module_for(self.resource)}/client.ts")
        lines = [
            f'import {{ Api }} from "{ts_import(path, "api.ts")}";',
            f'import {{ {self.client_class} }} from "{client}";',
        ]
        helpers = config.get("helpers") or {}
        if helpers:
            names = sorted(camel_case(f) for f in helpers.values())
            lines.append(
                f"import {{ {', '.join(names)} }} from "
                f'"{ts_import(path, "utils/helpers.ts")}";'
            )

        for _, names in self.resolver.external.items():
            self.referenced.update(names)
        imports: Dict[str, List[str]] = {}
        for name in sorted(self.referenced):
            target = f"{ts_module_for(self.home[name])}/types.ts"
            imports.setdefault(ts_import(path, target), []).append(name)
        for specifier in sorted(imports):
            renamed = [
                f"{name} as {name}Payload" if name == self.name else name
                for name in sorted(imports[specifier])
            ]
            lines.append(
                f"import {{ {', '.join(renamed)} }} from \"{specifier}\";"
            )

        payload = f"{self.name}Payload"
        lines.extend(
            [
                "",
                *(
                    [
                        "/**",
                        f" * One {snake_case(self.name).replace('_', ' ')} of "
                        f"your project, held by its {field}.",
                        " *",
                        f" * Its methods are {self.client_class}'s, minus the",
                        f" * `{self.identity['parameter']}` that this object "
                        "supplies.",
                        " */",
                    ]
                    if self.descriptive
                    else []
                ),
                f"export class {self.name} {{",
                f"  private readonly client: {self.client_class};",
                "",
            ]
        )
        declared = {name for name, _ in state}
        for name in [field] + takes:
            if name not in declared:
                lines.append(f"  {name}?: string;")
        for name, annotation in state:
            lines.append(f"  {name}?: {annotation};")
        lines.extend(
            [
                "",
                "  constructor(",
                "    api: Api,",
                "    options: { "
                + "; ".join(f"{name}?: string" for name in [field] + takes)
                + " } = {},",
                "  ) {",
                f"    this.client = new {self.client_class}(api);",
            ]
        )
        for name in [field] + takes:
            lines.append(f"    this.{name} = options.{name};")
        lines.append("  }")
        lines.extend(body)

        lines.extend(
            [
                "",
                f"  private load(payload: {payload}): void {{",
                *(
                    [
                        "    // The payload is one branch of a union, so a "
                        "field only the other",
                        "    // branch declares is absent rather than "
                        "undefined.",
                    ]
                    if self.descriptive and branches_of(self.name, self.schemas)
                    else []
                ),
                "    const source = payload as unknown as "
                "Record<string, unknown>;",
            ]
        )
        lines.extend(loaded)
        lines.append("  }")

        lines.extend(
            [
                "",
                f"  private {field}OrThrow(): string {{",
                f"    if (this.{field} === undefined) {{",
                "      throw new Error(",
                f'        "This {snake_case(self.name).replace("_", " ")} has '
                f'no {field}. Initialize it with " +',
                f'          "client.{config["client_method"]["name"]}({field}), or '
                'create it first.",',
                "      );",
                "    }",
                f"    return this.{field};",
                "  }",
                "}",
            ]
        )
        return "\n".join(lines)

    def grouped(self) -> Dict[str, List[str]]:
        for _, names in self.resolver.external.items():
            self.referenced.update(names)
        groups: Dict[str, List[str]] = {}
        for name in sorted(self.referenced):
            groups.setdefault(self.home[name], []).append(name)
        return groups


def render_handle(
    resource: str,
    config: Dict[str, Any],
    routes: List[Route],
    home: Dict[str, str],
    acronyms: Set[str],
    schemas: Dict[str, Any],
    descriptive: bool = True,
) -> str:
    ordered = sorted(
        routes, key=lambda route: (route.path, METHOD_ORDER.index(route.method))
    )
    return Handle(
        resource, config, ordered, home, acronyms, schemas, descriptive
    ).render()


def ts_handle_module(config: Dict[str, Any]) -> str:
    return f"{camel_case(config['class'])}.ts"


def render_typescript_handle(
    resource: str,
    config: Dict[str, Any],
    routes: List[Route],
    home: Dict[str, str],
    acronyms: Set[str],
    schemas: Dict[str, Any],
    descriptive: bool = True,
) -> str:
    ordered = sorted(
        routes, key=lambda route: (route.path, METHOD_ORDER.index(route.method))
    )
    path = f"{ts_module_for(resource)}/{ts_handle_module(config)}"
    return Handle(
        resource, config, ordered, home, acronyms, schemas, descriptive
    ).ts_render(path)


def render_typescript_stateful_clients(
    stateful: Dict[str, Any], resources: Sequence[str]
) -> str:
    """The base class opening a handle, extending the generated clients."""
    selected = [
        resource for resource in sorted(resources) if resource in stateful
    ]

    lines = [
        'import { Api, ApiKeyKind } from "../api";',
        'import { StatelessClients } from "./stateless";',
    ]
    for resource in selected:
        config = stateful[resource]
        stem = ts_handle_module(config)[: -len(".ts")]
        lines.append(
            f"import {{ {config['class']} }} from "
            f'"../{ts_module_for(resource)}/{stem}";'
        )
    lines.extend(
        ["", "export abstract class StatefulClients extends StatelessClients {"]
    )
    for resource in selected:
        config = stateful[resource]
        identity = camel_case(config["identity"]["field"])
        takes = [
            camel_case(s)
            for s in config.get("client_method", {}).get("takes") or []
        ]
        kind = (
            "ORGANIZATION"
            if resource in ORGANIZATION_KEY_RESOURCES
            else "PROJECT"
        )
        options = "; ".join(f"{name}?: string" for name in takes)
        lines.extend(
            [
                "",
                f"  {config['client_method']['name']}(",
                f"    {identity}?: string,",
            ]
            + ([f"    options: {{ {options} }} = {{}},"] if takes else [])
            + [
                f"  ): {config['class']} {{",
                f"    return new {config['class']}(this.api(ApiKeyKind.{kind}), {{",
                f"      {identity},",
                *[f"      {name}: options.{name}," for name in takes],
                "    });",
                "  }",
            ]
        )
    lines.append("}")
    return "\n".join(lines)


def render_stateful_clients(
    stateful: Dict[str, Any], resources: Sequence[str]
) -> str:
    """The mixin that opens a handle from the root client."""
    selected = [
        resource for resource in sorted(resources) if resource in stateful
    ]

    lines = [
        "from typing import TYPE_CHECKING, Optional",
        "",
        f"from {PYTHON_PACKAGE}.api import Api, ApiKeyKind",
        "",
        "if TYPE_CHECKING:",
    ]
    for resource in selected:
        config = stateful[resource]
        module = python_module_for(resource)[: -len(".types")]
        stem = handle_module(config)[: -len(".py")]
        lines.append(f"    from {module}.{stem} import {config['class']}")
    lines.extend(
        [
            "",
            "",
            "class StatefulClients:",
            "    def _api(self, key_kind: ApiKeyKind) -> Api:",
            "        raise NotImplementedError",
        ]
    )

    for resource in selected:
        config = stateful[resource]
        identity = config["identity"]
        takes = config.get("client_method", {}).get("takes") or []
        module = python_module_for(resource)[: -len(".types")]
        stem = handle_module(config)[: -len(".py")]
        kind = (
            "ORGANIZATION"
            if resource in ORGANIZATION_KEY_RESOURCES
            else "PROJECT"
        )
        opened = [identity["field"], *(snake_case(seed) for seed in takes)]
        lines.extend(
            [
                "",
                f"    def {config['client_method']['name']}(",
                "        self,",
                f"        {identity['field']}: Optional[str] = None,",
            ]
            + (["        *,"] if opened[1:] else [])
            + [f"        {seed}: Optional[str] = None," for seed in opened[1:]]
            + [
                f'    ) -> "{config["class"]}":',
                f"        from {module}.{stem} import {config['class']}",
                "",
                f"        return {config['class']}(",
                f"            self._api(ApiKeyKind.{kind}),",
            ]
            + [f"            {name}={name}," for name in opened]
            + ["        )"]
        )
    return "\n".join(lines)
