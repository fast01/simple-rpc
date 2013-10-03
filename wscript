APPNAME="simple-rpc"
VERSION="0.1"

import os
import sys
from waflib import Logs

# use clang++ as default compiler (for c++11 support on mac)
if sys.platform == 'darwin' and not os.environ.has_key("CXX"):
    os.environ["CXX"] = "clang++"

def options(opt):
    opt.load("compiler_cxx")

def configure(conf):
    conf.load("compiler_cxx")
    _enable_cxx11(conf)
    _enable_debug(conf)
    conf.env.LIB_PTHREAD = 'pthread'
    conf.env.INCLUDES_BASE = os.path.join(os.getcwd(), "../base-utils")
    conf.env.LIBPATH_BASE = os.path.join(os.getcwd(), "../base-utils/build")
    conf.env.LIB_BASE = 'base'

def build(bld):
    _depend("rpc/rpcgen.py", "rpc/rpcgen.g", "pylib/yapps/main.py rpc/rpcgen.g ; chmod a+x rpc/rpcgen.py")
    _depend("logservice/log_service.h", "logservice/log_service.rpc", "bin/rpcgen.py logservice/log_service.rpc")
    _depend("test/demo_service.h", "test/demo_service.rpc", "rpc/rpcgen.py test/demo_service.rpc")

    bld.stlib(source=bld.path.ant_glob("rpc/*.cc"), target="simplerpc", includes="rpc", use="PTHREAD BASE")
    bld.stlib(
        source=bld.path.ant_glob("logservice/*.cc", excl="logservice/log_server.cc"),
        target="logservice",
        includes=". logservice simple-rpc",
        use="PTHREAD BASE")

    def _prog(source, target, includes=".", use="simplerpc PTHREAD BASE"):
        bld.program(source=source, target=target, includes=includes, use=use)

    _prog("test/demo_client.cc", "demo_client")
    _prog("test/demo_server.cc test/demo_service.cc", "demo_server")
    _prog("test/perftest.cc", "perftest")
    _prog("test/marshal_test.cc", "marshal_test")
    _prog("test/counter_bench.cc", "counter_bench")
    _prog("test/threadpool_bench.cc", "threadpool_bench")
    _prog("test/synctest.cc test/demo_service.cc", "synctest")

    _prog("logservice/log_server.cc", "log_server", use="logservice simplerpc PTHREAD")
    _prog("test/log_client.cc", "log_client", use="logservice simplerpc PTHREAD")

#
# waf helper functions
#

def _enable_cxx11(conf):
    Logs.pprint("PINK", "C++11 features enabled")
    if sys.platform == "darwin":
        conf.env.append_value("CXXFLAGS", "-stdlib=libc++")
        conf.env.append_value("LINKFLAGS", "-stdlib=libc++")
    conf.env.append_value("CXXFLAGS", "-std=c++11")

def _enable_debug(conf):
    if os.getenv("DEBUG") in ["true", "1"]:
        Logs.pprint("PINK", "Debug support enabled")
        conf.env.append_value("CXXFLAGS", "-Wall -pthread -ggdb".split())
    else:
        conf.env.append_value("CXXFLAGS", "-Wall -pthread -O3 -ggdb -fno-omit-frame-pointer -DNDEBUG".split())

def _run_cmd(cmd):
    Logs.pprint('PINK', cmd)
    os.system(cmd)

def _depend(target, source, action):
    if source != None and os.path.exists(source) == False:
        Logs.pprint('RED', "'%s' not found!" % source)
        exit(1)
    if os.path.exists(target) == False or os.stat(target).st_mtime < os.stat(source).st_mtime:
        _run_cmd(action)
