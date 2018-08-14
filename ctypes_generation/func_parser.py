from winstruct import WinStruct, WinStructType, Ptr
import dummy_wintypes
from simpleparser import *


class WinFunc(object):
    def __init__(self, return_type, name, declaration, params=()):
        self.name = name
        self.declaration = declaration
        self.return_type = return_type
        self.params = params
        #if return_type not in dummy_wintypes.names:
        #    print("Non-standard return type {0}".format(return_type))
        #for (type, name) in params:
        #    if type not in dummy_wintypes.names:
        #        print("Non-standard type {0}".format(type))

    def generate_ctypes(self):
        return self.generate_comment_ctypes() + "\n" + self.generate_prototype_ctypes() + "\n" + self.generate_paramflags_ctypes() + "\n"

    def generate_comment_ctypes(self):
        model = "#def {0}({1}):\n#    return {0}.ctypes_function({1})"
        ctypes_param = [name for type, name in self.params]
        ctypes_param_str = ", ".join(ctypes_param)
        return model.format(self.name, ctypes_param_str)

    def generate_prototype_ctypes(self):
        model = "{0} = {1}({2})"
        if isinstance(self.return_type, tuple) and self.return_type[0] == "PTR":
            ctypes_param = ["POINTER({0})".format(self.return_type[1])]
        else:
            ctypes_param = [self.return_type]
        for type, name in self.params:
            if type.upper() == "POINTER(VOID)":
                type = "PVOID"
            ctypes_param.append(type)
        #ctypes_param = [self.return_type] + [type for type, name in self.params]
        ctypes_param_str = ", ".join(ctypes_param)
        return model.format(self.name + "Prototype", self.declaration, ctypes_param_str)

    def generate_paramflags_ctypes(self):
        model =  "{0} = {1}"
        ctypes_paramflags = tuple([(1, name) for type, name in self.params])
        return model.format(self.name + "Params", ctypes_paramflags)


class WinFuncParser(Parser):

    known_io_info_type = ["__in", "__in_opt", "_In_", "_In_opt_", "_Inout_", "_Out_opt_", "_Out_", "_Reserved_", "_Inout_opt_", "__inout_opt", "__out", "__inout", "__deref_out"]
    known_declarations = {
        "WINAPI" : "WINFUNCTYPE",
        "LDAPAPI" : "CFUNCTYPE"
    }

    def assert_argument_io_info(self):
        io_info = self.assert_token_type(NameToken)
        if io_info.value not in self.known_io_info_type:
            raise ParsingError("Was expecting IO_INFO got {0} instead".format(io_info))
        return io_info

    def parse_func_arg(self, has_declaration):
        type_ptr = False
        if has_declaration:
            self.assert_argument_io_info()
        arg_type = self.assert_token_type(NameToken)
        if arg_type.value.upper() == "CONST":
            arg_type = self.assert_token_type(NameToken)

        if type(self.peek()) == StarToken:
            type_ptr = True
            self.assert_token_type(StarToken)
        arg_name = self.assert_token_type(NameToken)
        if not type(self.peek()) == CloseParenthesisToken:
            self.assert_token_type(CommaToken)
        if not type_ptr:
            return (arg_type.value, arg_name.value)
        return ("POINTER({0})".format(arg_type.value), arg_name.value)

    def assert_winapi_token(self):
        winapi = self.assert_token_type(NameToken)
        if winapi.value != "WINAPI":
            raise ParsingError("Was expecting NameToken(WINAPI) got {0} instead".format(winapi))
        return winapi

    def parse_winfunc(self):
        has_declaration = False
        declaration = "WINFUNCTYPE"
        try:
            return_type = self.assert_token_type(NameToken).value
        except StopIteration:
            raise NormalParsingTerminaison()

        if type(self.peek()) == StarToken:
            self.assert_token_type(StarToken)
            return_type = ("PTR", return_type)

        func_name = self.assert_token_type(NameToken).value
        if func_name.upper() in self.known_declarations:
            has_declaration = True
            declaration = self.known_declarations[func_name.upper()]
            func_name = self.assert_token_type(NameToken).value

        self.assert_token_type(OpenParenthesisToken)

        params = []
        while type(self.peek()) != CloseParenthesisToken:
            params.append(self.parse_func_arg(has_declaration))

        self.assert_token_type(CloseParenthesisToken)
        self.assert_token_type(SemiColonToken)
        return WinFunc(return_type, func_name, params)

    def parse(self):
        res = []
        while self.peek() is not None:
            res.append(self.parse_winfunc())
        return res




def dbg_lexer(data):
    for i in Lexer(data).token_generation():
        print i

def dbg_parser(data):
    return WinFuncParser(data).parse()

def dbg_validate(data):
    return validate_structs(Parser(data).parse())



if __name__ == "__main__":
    import sys
    data = open(sys.argv[1], 'r').read()
    funcs = generate_ctypes(data)
    print(funcs)
