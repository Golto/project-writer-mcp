import inspect
from collections.abc import Callable
from typing import Annotated, TypeVar

from pydantic import BaseModel

from app.mcp import get_mcp


RequestModel = TypeVar("RequestModel", bound=BaseModel)
ToolResult = TypeVar("ToolResult", str, BaseModel)


def flatten_request(
    tool_function: Callable[[RequestModel], ToolResult],
    request_model: type[RequestModel],
) -> Callable[..., ToolResult]:
    """Wrap a request/response tool function into one with a flat signature.

    Tools are written against a single Pydantic request model, which keeps
    validation and documentation in one place. Exposed as is, the MCP schema
    has one nested 'request' object, and models regularly send the fields at
    the top level instead, which fails validation. This builds a wrapper
    whose parameters mirror each field of request_model (name, type,
    default, and Field metadata such as description and constraints), so the
    public schema is flat while tool_function is left untouched.

    Args:
        tool_function: The original tool, taking a single request_model instance.
        request_model: The Pydantic model describing tool_function's input.

    Returns:
        A wrapper with a flat, introspectable signature, preserving the name,
        docstring and return annotation of tool_function.
    """
    parameters: list[inspect.Parameter] = []
    annotations: dict[str, object] = {}

    for field_name, field_info in request_model.model_fields.items():
        annotation = Annotated[field_info.annotation, field_info]
        annotations[field_name] = annotation
        parameters.append(inspect.Parameter(
            name=field_name,
            kind=inspect.Parameter.KEYWORD_ONLY,
            default=inspect.Parameter.empty if field_info.is_required() else field_info.default,
            annotation=annotation,
        ))

    def flattened_tool(**arguments: object) -> ToolResult:
        return tool_function(request_model(**arguments))

    return_annotation = inspect.signature(tool_function).return_annotation
    annotations["return"] = return_annotation

    flattened_tool.__name__ = tool_function.__name__
    flattened_tool.__doc__ = tool_function.__doc__
    flattened_tool.__signature__ = inspect.Signature(
        parameters=parameters,
        return_annotation=return_annotation,
    )
    flattened_tool.__annotations__ = annotations

    return flattened_tool


def register_tool(
    tool_function: Callable[[RequestModel], ToolResult],
    request_model: type[RequestModel],
    description: str,
) -> None:
    """Register a tool on the shared FastMCP instance with a flat signature.

    The description is what the model reads to decide when and how to call
    the tool. It is passed explicitly so that the Google-style docstring of
    tool_function stays written for developers (Args, Raises...) without
    leaking into the model's context.

    Tools returning plain text are registered without structured output:
    otherwise FastMCP would send the same text twice, once as content and
    once wrapped in a JSON object.

    Args:
        tool_function: The original tool, taking a single request_model instance.
        request_model: The Pydantic model describing tool_function's input.
        description: Model-facing description of the tool.
    """
    returns_text = inspect.signature(tool_function).return_annotation is str
    get_mcp().tool(
        description=description,
        structured_output=not returns_text,
    )(flatten_request(tool_function, request_model))
