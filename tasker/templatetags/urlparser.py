import re

from django.http import QueryDict
from django.template import Library, Node, TemplateSyntaxError, VariableDoesNotExist

register = Library()


class ParameterNode(Node):
    @classmethod
    def create(cls, parser, token):
        set_parameters = {}
        delete_parameters = []

        set_re = re.compile(r'(\w+)=(.+)')
        delete_re = re.compile(r'!(\w+)')

        for bit in token.split_contents()[1:]:
            match = set_re.match(bit)
            if match:
                name, value = match.groups()
                set_parameters[name] = parser.compile_filter(value)
                continue

            match = delete_re.match(bit)
            if match:
                name, = match.groups()
                delete_parameters.append(name)
                continue

            raise TemplateSyntaxError("Malformed arguments to {set,form}_parameter tag", bit)

        return cls(set_parameters, delete_parameters)

    def __init__(self, set_parameters, delete_parameters):
        self.set_parameters = set_parameters
        self.delete_parameters = delete_parameters

    def get_query(self, context):
        query = context['request'].GET.copy()
        for argname, argvalue in self.set_parameters.items():
            try:
                query[argname] = argvalue.resolve(context)
            except AttributeError:
                query[argname] = argvalue
            except VariableDoesNotExist:
                query[argname] = None

        for argname in self.delete_parameters:
            try:
                del query[argname]
            except KeyError:
                pass

        return query


class ParameterGetNode(ParameterNode):
    def render(self, context):
        return "?" + self.get_query(context).urlencode()


class ParameterFormNode(ParameterNode):
    def render(self, context):
        query = self.get_query(context)
        return "".join(["<input type=\"hidden\" name=\"{}\" value=\"{}\" />".format(name, value) for name, value in query.items()])


@register.tag
def get_parameter(parser, token):
    return ParameterGetNode.create(parser, token)


@register.tag
def form_parameter(parser, token):
    return ParameterFormNode.create(parser, token)


@register.filter(is_safe=False)
def list_without(value, arg):
    return [item for item in value if item != arg]


@register.filter(is_safe=False)
def list_with(value, arg):
    return value + [arg]
