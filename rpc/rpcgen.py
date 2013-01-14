#!/usr/bin/env python

import sys
import os
sys.path += os.path.abspath(os.path.join(os.path.split(__file__)[0], "..")),


# Begin -- grammar generated by Yapps
import sys, re
from yapps import runtime

class RpcDefScanner(runtime.Scanner):
    patterns = [
        ('"raw"', re.compile('raw')),
        ('"fast"', re.compile('fast')),
        ('"\\)"', re.compile('\\)')),
        ('";"', re.compile(';')),
        ('"\\("', re.compile('\\(')),
        ('"service"', re.compile('service')),
        ("','", re.compile(',')),
        ('"map"', re.compile('map')),
        ('"deque"', re.compile('deque')),
        ('"set"', re.compile('set')),
        ('"list"', re.compile('list')),
        ('">"', re.compile('>')),
        ('"<"', re.compile('<')),
        ('"vector"', re.compile('vector')),
        ('"string"', re.compile('string')),
        ('"i64"', re.compile('i64')),
        ('"i32"', re.compile('i32')),
        ('"}"', re.compile('}')),
        ('"{"', re.compile('{')),
        ('"struct"', re.compile('struct')),
        ('"namespace"', re.compile('namespace')),
        ('\\s+', re.compile('\\s+')),
        ('//[^\\n]+', re.compile('//[^\\n]+')),
        ('EOF', re.compile('$')),
        ('IDENTIFIER', re.compile('[$a-zA-Z0-9_][$a-zA-Z0-9_]*')),
    ]
    def __init__(self, str,*args,**kw):
        runtime.Scanner.__init__(self,None,{'\\s+':None,'//[^\\n]+':None,},str,*args,**kw)

class RpcDef(runtime.Parser):
    Context = runtime.Context
    def rpc_def(self, _parent=None):
        _context = self.Context(_parent, self._scanner, 'rpc_def', [])
        namespace = None
        if self._peek('"namespace"', 'EOF', '"struct"', '"service"', context=_context) == '"namespace"':
            ns_decl = self.ns_decl(_context)
            namespace = ns_decl
        def_list = self.def_list(_context)
        EOF = self._scan('EOF', context=_context)
        return namespace, def_list

    def ns_decl(self, _parent=None):
        _context = self.Context(_parent, self._scanner, 'ns_decl', [])
        self._scan('"namespace"', context=_context)
        IDENTIFIER = self._scan('IDENTIFIER', context=_context)
        return IDENTIFIER

    def def_list(self, _parent=None):
        _context = self.Context(_parent, self._scanner, 'def_list', [])
        struct_def_list = []; service_def_list = []
        while self._peek('"struct"', '"service"', 'EOF', context=_context) != 'EOF':
            _token = self._peek('"struct"', '"service"', context=_context)
            if _token == '"struct"':
                struct_def = self.struct_def(_context)
                struct_def_list += struct_def,
            else: # == '"service"'
                service_def = self.service_def(_context)
                service_def_list += service_def,
        return  struct_def_list, service_def_list

    def struct_def(self, _parent=None):
        _context = self.Context(_parent, self._scanner, 'struct_def', [])
        self._scan('"struct"', context=_context)
        IDENTIFIER = self._scan('IDENTIFIER', context=_context)
        self._scan('"{"', context=_context)
        field_list = self.field_list(_context)
        self._scan('"}"', context=_context)
        return IDENTIFIER, field_list

    def field_list(self, _parent=None):
        _context = self.Context(_parent, self._scanner, 'field_list', [])
        field_list = []
        while 1:
            field_def = self.field_def(_context)
            field_list += field_def,
            if self._peek('"i32"', '"i64"', 'IDENTIFIER', '"string"', '"vector"', '"list"', '"set"', '"deque"', '"map"', '"}"', context=_context) not in ['"i32"', '"i64"', 'IDENTIFIER', '"string"', '"vector"', '"list"', '"set"', '"deque"', '"map"']: break
        return field_list

    def field_def(self, _parent=None):
        _context = self.Context(_parent, self._scanner, 'field_def', [])
        type_info = self.type_info(_context)
        IDENTIFIER = self._scan('IDENTIFIER', context=_context)
        return type_info, IDENTIFIER

    def type_info(self, _parent=None):
        _context = self.Context(_parent, self._scanner, 'type_info', [])
        _token = self._peek('"i32"', '"i64"', 'IDENTIFIER', '"string"', '"vector"', '"list"', '"set"', '"deque"', '"map"', context=_context)
        if _token == '"string"':
            string_type = self.string_type(_context)
            return string_type
        elif _token == '"vector"':
            vector_type = self.vector_type(_context)
            return vector_type
        elif _token == '"list"':
            list_type = self.list_type(_context)
            return list_type
        elif _token == '"set"':
            set_type = self.set_type(_context)
            return set_type
        elif _token == '"deque"':
            deque_type = self.deque_type(_context)
            return deque_type
        elif _token == '"map"':
            map_type = self.map_type(_context)
            return map_type
        elif _token == '"i32"':
            self._scan('"i32"', context=_context)
            return "rpc::i32"
        elif _token == '"i64"':
            self._scan('"i64"', context=_context)
            return "rpc::i64"
        else: # == 'IDENTIFIER'
            IDENTIFIER = self._scan('IDENTIFIER', context=_context)
            return IDENTIFIER

    def string_type(self, _parent=None):
        _context = self.Context(_parent, self._scanner, 'string_type', [])
        self._scan('"string"', context=_context)
        return "std::string"

    def vector_type(self, _parent=None):
        _context = self.Context(_parent, self._scanner, 'vector_type', [])
        self._scan('"vector"', context=_context)
        self._scan('"<"', context=_context)
        type_info = self.type_info(_context)
        self._scan('">"', context=_context)
        return "std::vector<%s >" % type_info

    def list_type(self, _parent=None):
        _context = self.Context(_parent, self._scanner, 'list_type', [])
        self._scan('"list"', context=_context)
        self._scan('"<"', context=_context)
        type_info = self.type_info(_context)
        self._scan('">"', context=_context)
        return "std::list<%s >" % type_info

    def set_type(self, _parent=None):
        _context = self.Context(_parent, self._scanner, 'set_type', [])
        self._scan('"set"', context=_context)
        self._scan('"<"', context=_context)
        type_info = self.type_info(_context)
        self._scan('">"', context=_context)
        return "std::set<%s >" % type_info

    def deque_type(self, _parent=None):
        _context = self.Context(_parent, self._scanner, 'deque_type', [])
        self._scan('"deque"', context=_context)
        self._scan('"<"', context=_context)
        type_info = self.type_info(_context)
        self._scan('">"', context=_context)
        return "std::deque<%s >" % type_info

    def map_type(self, _parent=None):
        _context = self.Context(_parent, self._scanner, 'map_type', [])
        key_type = None; value_type = None
        self._scan('"map"', context=_context)
        self._scan('"<"', context=_context)
        type_info = self.type_info(_context)
        key_type = type_info
        self._scan("','", context=_context)
        type_info = self.type_info(_context)
        value_type = type_info
        self._scan('">"', context=_context)
        return "std::map<%s, %s >" % (key_type, value_type)

    def service_def(self, _parent=None):
        _context = self.Context(_parent, self._scanner, 'service_def', [])
        self._scan('"service"', context=_context)
        IDENTIFIER = self._scan('IDENTIFIER', context=_context)
        self._scan('"{"', context=_context)
        func_list = self.func_list(_context)
        self._scan('"}"', context=_context)
        return IDENTIFIER, func_list

    def func_list(self, _parent=None):
        _context = self.Context(_parent, self._scanner, 'func_list', [])
        func_list = []
        while 1:
            func_def = self.func_def(_context)
            func_list += func_def,
            if self._peek('IDENTIFIER', '"fast"', '"raw"', '"}"', context=_context) not in ['IDENTIFIER', '"fast"', '"raw"']: break
        return func_list

    def func_def(self, _parent=None):
        _context = self.Context(_parent, self._scanner, 'func_def', [])
        in_args = None; out_args = None; f_attr = None
        if self._peek('IDENTIFIER', '"fast"', '"raw"', context=_context) != 'IDENTIFIER':
            func_attr = self.func_attr(_context)
            f_attr = func_attr
        IDENTIFIER = self._scan('IDENTIFIER', context=_context)
        self._scan('"\\("', context=_context)
        arg_list = self.arg_list(_context)
        in_args = arg_list
        if self._peek('";"', '"\\)"', context=_context) == '";"':
            self._scan('";"', context=_context)
            arg_list = self.arg_list(_context)
            out_args = arg_list
        self._scan('"\\)"', context=_context)
        return IDENTIFIER, f_attr, in_args, out_args

    def func_attr(self, _parent=None):
        _context = self.Context(_parent, self._scanner, 'func_attr', [])
        _token = self._peek('"fast"', '"raw"', context=_context)
        if _token == '"fast"':
            self._scan('"fast"', context=_context)
            return "fast"
        else: # == '"raw"'
            self._scan('"raw"', context=_context)
            return "raw"

    def arg_list(self, _parent=None):
        _context = self.Context(_parent, self._scanner, 'arg_list', [])
        _token = self._peek('"i32"', '"i64"', 'IDENTIFIER', '"string"', '"vector"', '"list"', '"set"', '"deque"', '"map"', '";"', '"\\)"', context=_context)
        if _token in ['";"', '"\\)"']:
            a_list = []
        else:
            func_arg = self.func_arg(_context)
            a_list = [func_arg, ]
            while self._peek("','", '";"', '"\\)"', context=_context) == "','":
                self._scan("','", context=_context)
                func_arg = self.func_arg(_context)
                a_list += func_arg,
            return a_list

    def func_arg(self, _parent=None):
        _context = self.Context(_parent, self._scanner, 'func_arg', [])
        ident = None
        type_info = self.type_info(_context)
        if self._peek('IDENTIFIER', "','", '";"', '"\\)"', context=_context) == 'IDENTIFIER':
            IDENTIFIER = self._scan('IDENTIFIER', context=_context)
            ident = IDENTIFIER
        return type_info, ident


def parse(rule, text):
    P = RpcDef(RpcDefScanner(text))
    return runtime.wrap_error_reporter(P, rule)

# End -- grammar generated by Yapps



g_rpc_counter = 0x1001;

def space(n):
    return " " * n

def write_ln(f, line="\n", indent=0):
    if line == "":
        return
    f.write(space(indent))
    f.write(line)
    if not line.endswith("\n"):
        f.write('\n')

def gen_struct_def(struct_def, h):
    name, fields = struct_def
    write_ln(h, "struct %s {" % name)
    for field in fields:
        write_ln(h, "%s %s;" % (field[0], field[1]), 4)
    write_ln(h, "};")
    write_ln(h)
    write_ln(h, "inline rpc::Marshal& operator << (rpc::Marshal& m, const %s& o) {" % name)
    for field in fields:
        write_ln(h, "m << o.%s;" % field[1], 4)
    write_ln(h, "return m;", 4);
    write_ln(h, "}")
    write_ln(h)
    write_ln(h, "inline rpc::Marshal& operator >> (rpc::Marshal& m, %s& o) {" % name)
    for field in fields:
        write_ln(h, "m >> o.%s;" % field[1], 4)
    write_ln(h, "return m;", 4);
    write_ln(h, "}")
    write_ln(h)

def gen_struct_def_list(struct_def_list, h):
    for struct_def in struct_def_list:
        gen_struct_def(struct_def, h)

def gen_service_def(service_def, h):
    global g_rpc_counter

    svc_name, members = service_def
    write_ln(h, "class %sService: public rpc::Service {" % svc_name)
    write_ln(h, "public:")
    write_ln(h, "enum {", 4)
    for member in members:
        func_name = member[0]
        write_ln(h, func_name.upper() + ' = ' + hex(g_rpc_counter) + ',', 8)
        g_rpc_counter += 1
    write_ln(h, "};", 4)
    write_ln(h)
    write_ln(h, "void reg_to(rpc::Server* svr) {", 4)
    for member in members:
        func_name, func_attr = member[0], member[1]
        if func_attr == "raw":
            write_ln(h, "svr->reg(%s, this, &%sService::%s);" % (func_name.upper(), svc_name, func_name) , 8)
        else:
            write_ln(h, "svr->reg(%s, this, &%sService::__%s__wrapped__);" % (func_name.upper(), svc_name, func_name) , 8)
    write_ln(h, "}", 4)

    write_ln(h)
    write_ln(h, "private:")

    for member in members:
        func_name, func_attr, in_args, out_args = member[0], member[1], member[2], member[3]
        func_args = []
        if func_attr == "raw":
            continue
        write_ln(h, "void __%s__wrapped__(rpc::Request* req, rpc::ServerConnection* sconn) {" % func_name, 4)
        in_count = 0
        out_count = 0
        if func_attr == "fast":
            call_args = []
            for in_arg in in_args:
                write_ln(h, "%s in_%d;" % (in_arg[0], in_count), 8)
                write_ln(h, "req->m >> in_%d;" % in_count, 8)
                call_args += "in_%d" % in_count,
                in_count += 1
            for out_arg in out_args:
                write_ln(h, "%s out_%d;" % (out_arg[0], out_count), 8)
                call_args += "&out_%d" % out_count,
                out_count += 1

            write_ln(h, "this->%s(%s);" % (func_name, ", ".join(call_args)), 8)
            write_ln(h, "sconn->begin_reply(req);", 8)
            for i in range(out_count):
                write_ln(h, "*sconn << out_%d;" % i, 8)
            write_ln(h, "sconn->end_reply();", 8)
            write_ln(h, "delete req;", 8)
            write_ln(h, "sconn->release();", 8)
        else:
            write_ln(h, "class R: public rpc::Runnable {", 8)
            write_ln(h, "%sService* thiz_;" % svc_name, 12)
            write_ln(h, "rpc::Request* req_;", 12)
            write_ln(h, "rpc::ServerConnection* sconn_;", 12)
            write_ln(h, "public:", 8)
            write_ln(h, "R(%sService* thiz, rpc::Request* r, rpc::ServerConnection* sc): thiz_(thiz), req_(r), sconn_(sc) {}" % svc_name, 12)
            write_ln(h, "void run() {", 12)
            call_args = []
            for in_arg in in_args:
                write_ln(h, "%s in_%d;" % (in_arg[0], in_count), 16)
                write_ln(h, "req_->m >> in_%d;" % in_count, 16)
                call_args += "in_%d" % in_count,
                in_count += 1
            for out_arg in out_args:
                write_ln(h, "%s out_%d;" % (out_arg[0], out_count), 16)
                call_args += "&out_%d" % out_count,
                out_count += 1

            write_ln(h, "thiz_->%s(%s);" % (func_name, ", ".join(call_args)), 16)
            write_ln(h, "sconn_->begin_reply(req_);", 16)
            for i in range(out_count):
                write_ln(h, "*sconn_ << out_%d;" % i, 16)
            write_ln(h, "sconn_->end_reply();", 16)
            write_ln(h, "delete req_;", 16)
            write_ln(h, "sconn_->release();", 16)
            write_ln(h, "}", 12)
            write_ln(h, "};", 8)
            write_ln(h, "sconn->run_async(new R(this, req, sconn));", 8)
        write_ln(h, "", 8)
        write_ln(h, "}", 4)
        write_ln(h)

    write_ln(h, "public:")
    write_ln(h, "// these member functions need to be implemented by user", 4)
    for member in members:
        func_name, func_attr, in_args, out_args = member[0], member[1], member[2], member[3]
        func_args = []
        if func_attr == "raw":
            write_ln(h, "// NOTE: remember to reply req, delete req, and sconn->release(); use sconn->run_async for heavy job", 4)
            write_ln(h, "void %s(rpc::Request* req, rpc::ServerConnection* sconn);" % func_name, 4)
            continue

        if in_args != None:
            for in_arg in in_args:
                func_arg = "const %s&" % in_arg[0]
                if in_arg[1] != None:
                    func_arg += " %s" % in_arg[1]
                func_args += func_arg,
        if out_args != None:
            for out_arg in out_args:
                func_arg = "%s*" % out_arg[0]
                if out_arg[1] != None:
                    func_arg += " %s" % out_arg[1]
                func_args += func_arg,
        write_ln(h, "void %s(%s);" % (func_name, ", ".join(func_args)), 4)


    write_ln(h)
    write_ln(h, "}; // class %sService" % svc_name)
    write_ln(h)

    write_ln(h, "class %sProxy {" % svc_name)
    write_ln(h, "rpc::Client* cl_;", 4)
    write_ln(h, "public:")
    write_ln(h, "%sProxy(rpc::Client* cl): cl_(cl) {}" % svc_name, 4)

    for member in members:

        func_name, func_attr, in_args, out_args = member[0], member[1], member[2], member[3]
        if func_attr == "raw":
            continue

        write_ln(h)
        func_args = []
        async_args = []
        in_count = 0
        out_count = 0
        if in_args != None:
            for in_arg in in_args:
                func_arg = "const %s&" % in_arg[0]
                if in_arg[1] != None:
                    func_arg += " %s" % in_arg[1]
                else:
                    func_arg += " in_%d" % in_count
                func_args += func_arg,
                async_args += func_arg,
                in_count += 1
        if out_args != None:
            for out_arg in out_args:
                func_arg = "%s*" % out_arg[0]
                if out_arg[1] != None:
                    func_arg += " %s" % out_arg[1]
                else:
                    func_arg += " out_%d" % out_count
                func_args += func_arg,
                out_count += 1
        write_ln(h, "rpc::i32 %s(%s) {" % (func_name, ", ".join(func_args)), 4)
        call_args = []
        in_count = 0
        if in_args != None:
            for in_arg in in_args:
                if in_arg[1] != None:
                    call_args += "%s" % in_arg[1],
                else:
                    call_args += "in_%d" % in_count,
                in_count += 1
        write_ln(h, "rpc::Future* fu = async_%s(%s);" % (func_name, ", ".join(call_args)), 8)
        write_ln(h, "if (fu == NULL) {", 8)
        write_ln(h, "return ENOTCONN;", 12)
        write_ln(h, "}", 8)
        write_ln(h, "rpc::i32 __ret__ = fu->get_error_code();", 8)
        write_ln(h, "if (__ret__ == 0) {", 8)
        out_count = 0
        if out_args != None:
            for out_arg in out_args:
                if out_arg[1] != None:
                    write_ln(h, "fu->get_reply() >> *%s;" % out_arg[1], 12)
                else:
                    write_ln(h, "fu->get_reply() >> *out_%d;" % out_count, 12)
                out_count += 1
        write_ln(h, "}", 8)
        write_ln(h, "fu->release();", 8)
        write_ln(h, "return __ret__;", 8)
        write_ln(h, "}", 4)
        write_ln(h)

        write_ln(h, "rpc::Future* async_%s(%s) {" % (func_name, ", ".join(async_args)), 4)
        write_ln(h, "rpc::Future* fu = cl_->begin_request();", 8)
        write_ln(h, "rpc::i32 rpc_id = %sService::%s;" % (svc_name, func_name.upper()), 8)
        write_ln(h, "*cl_ << rpc_id;", 8)
        in_count = 0
        if in_args != None:
            for in_arg in in_args:
                if in_arg[1] != None:
                    write_ln(h, "*cl_ << %s;" % in_arg[1], 8)
                else:
                    write_ln(h, "*cl_ << in_%d;" % in_count, 8)
                in_count += 1
        write_ln(h, "cl_->end_request();", 8)
        write_ln(h, "return fu;", 8)
        write_ln(h, "}", 4)

    write_ln(h)

    for member in members:
        func_name, func_attr = member[0], member[1]
        if func_attr == "raw":
            write_ln(h, "// raw rpc '%s' not included" % func_name, 4)

    write_ln(h)
    write_ln(h, "}; // class %sProxy" % svc_name)
    write_ln(h)



def gen_service_def_list(service_def_list, h):
    for service_def in service_def_list:
        gen_service_def(service_def, h)

def gen_rpc_def(rpc_def, h):
    ns, rpc_def_body = rpc_def
    struct_def_list, service_def_list = rpc_def_body
    if ns != None:
        write_ln(h, "namespace %s {" % ns)
        write_ln(h)
        gen_struct_def_list(struct_def_list, h)
        gen_service_def_list(service_def_list, h)
        write_ln(h, "} // namespace %s" % ns)
    else:
        gen_struct_def_list(struct_def_list, h)
        gen_service_def_list(service_def_list, h)


def expand_str(template, vals, prefix='', postfix='', sep=', '):
    if len(vals) > 0:
        return prefix + sep.join([template % v for v in vals]) + postfix
    else:
        return ""

def range2(v):
    return zip(range(v), range(v))


def rpc_gen(rpc_fpath):
    f = open(rpc_fpath)
    rpc_def = parse("rpc_def", f.read())
    f.close()
    h_fpath = os.path.splitext(rpc_fpath)[0] + '.h'
    h = open(h_fpath, 'w')

    write_ln(h, "// this file is automatically generated from '%s'" % os.path.split(rpc_fpath)[1])
    write_ln(h, "// make sure you have included server.h and marshal.h before including this file")
    write_ln(h)
    write_ln(h, "#pragma once")
    write_ln(h)
    write_ln(h, "#include <errno.h>")
    write_ln(h)

    gen_rpc_def(rpc_def, h)
    h.close()


if __name__ == "__main__":
    rpc_gen(sys.argv[1])
