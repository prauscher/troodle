import re

from django.http import QueryDict
from django.template import Library, Node, TemplateSyntaxError

register = Library()


class ParameterGetNode(Node):
    def __init__(self, kwargs):
        self.kwargs = kwargs

    def render(self, context):
        query = context['request'].GET.copy()
        for argname, argvalue in self.kwargs.items():
            try:
                query[argname] = argvalue.resolve(context)
            except AttributeError:
                query[argname] = argvalue
            except VariableDoesNotExist:
                query[argname] = None

        return "?" + query.urlencode()


@register.tag
def get_parameter(parser, token):
    bits = token.split_contents()[1:]

    kwargs = {}

    kwarg_re = re.compile(r'(\w+)=(.+)')
    for bit in bits:
        match = kwarg_re.match(bit)
        if not match:
            raise TemplateSyntaxError("Malformed arguments to get_parameter tag", bit)
        name, value = match.groups()
        kwargs[name] = parser.compile_filter(value)

    return ParameterGetNode(kwargs)


class ParameterFormNode(Node):
    def __init__(self, kwargs):
        self.kwargs = kwargs

    def render(self, context):
        query = context['request'].GET.copy()
        for argname, argvalue in self.kwargs.items():
            try:
                query[argname] = argvalue.resolve(context)
            except AttributeError:
                query[argname] = argvalue
            except VariableDoesNotExist:
                query[argname] = None

        return "".join(["<input type=\"hidden\" name=\"{}\" value=\"{}\" />".format(name, value) for name, value in query.items()])


@register.tag
def form_parameter(parser, token):
    bits = token.split_contents()[1:]

    kwargs = {}

    kwarg_re = re.compile(r'(\w+)=(.+)')
    for bit in bits:
        match = kwarg_re.match(bit)
        if not match:
            raise TemplateSyntaxError("Malformed arguments to form_parameter tag", bit)
        name, value = match.groups()
        kwargs[name] = parser.compile_filter(value)

    return ParameterFormNode(kwargs)


@register.filter(is_safe=False)
def list_without(value, arg):
    return [item for item in value if item != arg]


@register.filter(is_safe=False)
def list_with(value, arg):
    return value + [arg]
