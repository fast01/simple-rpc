#include <Python.h>

#include <string>

#include "rpc/server.h"
#include "rpc/client.h"

using namespace rpc;

class GILHelper {
    PyGILState_STATE gil_state;
public:
    GILHelper() {
        gil_state = PyGILState_Ensure();
    }

    ~GILHelper() {
        PyGILState_Release(gil_state);
    }
};

class AsyncQueue: public RefCounted {
    Queue<i64> q_;
protected:
    ~AsyncQueue() {}
public:
    void push(i64 v) {
        q_.push(v);
    }
    i64 pop() {
        return q_.pop();
    }
};

static PyObject* _pyrpc_init_server(PyObject* self, PyObject* args) {
    GILHelper gil_helper;
    Server* svr = new Server;
    return Py_BuildValue("k", svr);
}

static PyObject* _pyrpc_fini_server(PyObject* self, PyObject* args) {
    GILHelper gil_helper;
    unsigned long u;
    if (!PyArg_ParseTuple(args, "k", &u))
        return nullptr;
    Server* svr = (Server *) u;
    delete svr;
    Py_RETURN_NONE;
}

static PyObject* _pyrpc_server_start(PyObject* self, PyObject* args) {
    GILHelper gil_helper;
    const char* addr;
    unsigned long u;
    if (!PyArg_ParseTuple(args, "ks", &u, &addr))
        return nullptr;
    Server* svr = (Server *) u;
    int ret = svr->start(addr);
    return Py_BuildValue("i", ret);
}

static PyObject* _pyrpc_server_unreg(PyObject* self, PyObject* args) {
    GILHelper gil_helper;
    unsigned long u;
    int rpc_id;
    if (!PyArg_ParseTuple(args, "ki", &u, &rpc_id))
        return nullptr;
    Server* svr = (Server *) u;
    svr->unreg(rpc_id);
    Py_RETURN_NONE;
}

static PyObject* _pyrpc_server_reg(PyObject* self, PyObject* args) {
    GILHelper gil_helper;
    unsigned long u;
    int rpc_id;
    PyObject* func;
    if (!PyArg_ParseTuple(args, "kiO", &u, &rpc_id, &func))
        return nullptr;
    Server* svr = (Server *) u;

    // incr ref_count on PyObject func
    // TODO remember this, and decr ref_count on PyObject func when shutting down server
    Py_XINCREF(func);

    int ret = svr->reg(rpc_id, [func](Request* req, ServerConnection* sconn) {
        Marshal* output_m = nullptr;
        int error_code = 0;
        {
            unsigned long u = (unsigned long) &req->m;
            GILHelper gil_helper;
            PyObject* params = Py_BuildValue("(k)", u);
            PyObject* result = PyObject_CallObject(func, params);
            if (result == nullptr) {
                // exception handling
                error_code = -1; // generic error code
                if (PyErr_ExceptionMatches(PyExc_NotImplementedError)) {
                    error_code = ENOSYS;
                }
                PyErr_Clear();
            } else {
                output_m = (Marshal *) PyInt_AsLong(result);
                Py_XDECREF(params);
                Py_XDECREF(result);
            }
        }

        sconn->begin_reply(req, error_code);
        if (output_m != nullptr) {
            *sconn << *output_m;
        }
        sconn->end_reply();

        if (output_m != nullptr) {
            delete output_m;
        }

        // cleanup as required by simple-rpc
        delete req;
        sconn->release();
    });

    return Py_BuildValue("i", ret);
}

static PyObject* _pyrpc_init_poll_mgr(PyObject* self, PyObject* args) {
    GILHelper gil_helper;
    PollMgr* poll = new PollMgr;
    return Py_BuildValue("k", poll);
}

static PyObject* _pyrpc_init_client(PyObject* self, PyObject* args) {
    GILHelper gil_helper;
    unsigned long u;
    if (!PyArg_ParseTuple(args, "k", &u))
        return nullptr;
    PollMgr* poll = (PollMgr *) u;
    Client* clnt = new Client(poll);
    return Py_BuildValue("k", clnt);
}

static PyObject* _pyrpc_fini_client(PyObject* self, PyObject* args) {
    GILHelper gil_helper;
    unsigned long u;
    if (!PyArg_ParseTuple(args, "k", &u))
        return nullptr;
    Client* clnt = (Client *) u;
    clnt->close_and_release();
    Py_RETURN_NONE;
}

static PyObject* _pyrpc_client_connect(PyObject* self, PyObject* args) {
    GILHelper gil_helper;
    const char* addr;
    unsigned long u;
    if (!PyArg_ParseTuple(args, "ks", &u, &addr))
        return nullptr;
    Client* clnt = (Client *) u;
    int ret = clnt->connect(addr);
    return Py_BuildValue("i", ret);
}

static PyObject* _pyrpc_client_sync_call(PyObject* self, PyObject* args) {
    GILHelper gil_helper;

    PyThreadState *_save;
    _save = PyEval_SaveThread();

    unsigned long u;
    int rpc_id;
    unsigned long m_id;
    if (!PyArg_ParseTuple(args, "kik", &u, &rpc_id, &m_id))
        return nullptr;

    Client* clnt = (Client *) u;
    Marshal* m = (Marshal *) m_id;

    Future* fu = clnt->begin_request(rpc_id);
    if (fu != nullptr) {
        *clnt << *m;
    }
    clnt->end_request();

    Marshal* m_rep = new Marshal;
    int error_code;
    if (fu == nullptr) {
        error_code = ENOTCONN;
    } else {
        error_code = fu->get_error_code();
        if (error_code == 0) {
            m_rep->read_from_marshal(fu->get_reply(), fu->get_reply().content_size());
        }
        fu->release();
    }

    PyEval_RestoreThread(_save);

    unsigned long m_rep_id = (unsigned long) m_rep;
    return Py_BuildValue("(ik)", error_code, m_rep_id);
}

static PyObject* _pyrpc_client_async_call(PyObject* self, PyObject* args) {
    GILHelper gil_helper;

    unsigned long u;
    unsigned long qu;
    int rpc_id;
    unsigned long m_id;
    unsigned long cb_id;
    if (!PyArg_ParseTuple(args, "kkikk", &u, &qu, &rpc_id, &m_id, &cb_id))
        return nullptr;

    Client* clnt = (Client *) u;
    Marshal* m = (Marshal *) m_id;
    AsyncQueue* q = (AsyncQueue *) qu;

    FutureAttr fu_attr;
    if (cb_id != 0) {
        q->ref_copy();
        fu_attr.callback = [cb_id, q] (Future* fu) {
            q->push(cb_id);
            q->push((i64) fu);
            q->release();
        };
    }

    Future* fu = clnt->begin_request(rpc_id, fu_attr);
    if (fu != nullptr) {
        *clnt << *m;
    }
    clnt->end_request();

    unsigned long fu_id = (unsigned long) fu;
    return Py_BuildValue("k", fu_id);
}


static PyObject* _pyrpc_init_marshal(PyObject* self, PyObject* args) {
    GILHelper gil_helper;
    Marshal* m = new Marshal;
    return Py_BuildValue("k", m);
}

static PyObject* _pyrpc_fini_marshal(PyObject* self, PyObject* args) {
    GILHelper gil_helper;
    unsigned long u;
    if (!PyArg_ParseTuple(args, "k", &u))
        return nullptr;
    Marshal* m = (Marshal *) u;
    delete m;
    Py_RETURN_NONE;
}


static PyObject* _pyrpc_marshal_size(PyObject* self, PyObject* args) {
    GILHelper gil_helper;
    unsigned long u;
    if (!PyArg_ParseTuple(args, "k", &u))
        return nullptr;
    Marshal* m = (Marshal *) u;
    return Py_BuildValue("k", m->content_size());
}

static PyObject* _pyrpc_marshal_write_i8(PyObject* self, PyObject* args) {
    GILHelper gil_helper;
    unsigned long u;
    long vl;
    if (!PyArg_ParseTuple(args, "kl", &u, &vl))
        return nullptr;
    Marshal* m = (Marshal *) u;
    rpc::i8 v = (rpc::i8) vl;
    *m << v;
    Py_RETURN_NONE;
}


static PyObject* _pyrpc_marshal_read_i8(PyObject* self, PyObject* args) {
    GILHelper gil_helper;
    unsigned long u;
    if (!PyArg_ParseTuple(args, "k", &u))
        return nullptr;
    Marshal* m = (Marshal *) u;
    rpc::i8 v;
    *m >> v;
    long vl = v;
    return Py_BuildValue("l", vl);
}

static PyObject* _pyrpc_marshal_write_i16(PyObject* self, PyObject* args) {
    GILHelper gil_helper;
    unsigned long u;
    long vl;
    if (!PyArg_ParseTuple(args, "kl", &u, &vl))
        return nullptr;
    Marshal* m = (Marshal *) u;
    rpc::i16 v = (rpc::i16) vl;
    *m << v;
    Py_RETURN_NONE;
}


static PyObject* _pyrpc_marshal_read_i16(PyObject* self, PyObject* args) {
    GILHelper gil_helper;
    unsigned long u;
    if (!PyArg_ParseTuple(args, "k", &u))
        return nullptr;
    Marshal* m = (Marshal *) u;
    rpc::i16 v;
    *m >> v;
    long vl = v;
    return Py_BuildValue("l", vl);
}

static PyObject* _pyrpc_marshal_write_i32(PyObject* self, PyObject* args) {
    GILHelper gil_helper;
    unsigned long u;
    long vl;
    if (!PyArg_ParseTuple(args, "kl", &u, &vl))
        return nullptr;
    Marshal* m = (Marshal *) u;
    rpc::i32 v = (rpc::i32) vl;
    *m << v;
    Py_RETURN_NONE;
}


static PyObject* _pyrpc_marshal_read_i32(PyObject* self, PyObject* args) {
    GILHelper gil_helper;
    unsigned long u;
    if (!PyArg_ParseTuple(args, "k", &u))
        return nullptr;
    Marshal* m = (Marshal *) u;
    rpc::i32 v;
    *m >> v;
    long vl = v;
    return Py_BuildValue("l", vl);
}

static PyObject* _pyrpc_marshal_write_i64(PyObject* self, PyObject* args) {
    GILHelper gil_helper;
    unsigned long u;
    long long vll;
    if (!PyArg_ParseTuple(args, "kL", &u, &vll))
        return nullptr;
    Marshal* m = (Marshal *) u;
    rpc::i64 v = (rpc::i64) vll;
    *m << v;
    Py_RETURN_NONE;
}


static PyObject* _pyrpc_marshal_read_i64(PyObject* self, PyObject* args) {
    GILHelper gil_helper;
    unsigned long u;
    if (!PyArg_ParseTuple(args, "k", &u))
        return nullptr;
    Marshal* m = (Marshal *) u;
    rpc::i64 v;
    *m >> v;
    long long vll = v;
    return Py_BuildValue("L", vll);
}

static PyObject* _pyrpc_marshal_write_v32(PyObject* self, PyObject* args) {
    GILHelper gil_helper;
    unsigned long u;
    long long vll;
    if (!PyArg_ParseTuple(args, "kL", &u, &vll))
        return nullptr;
    Marshal* m = (Marshal *) u;
    rpc::v32 v = vll;
    *m << v;
    Py_RETURN_NONE;
}


static PyObject* _pyrpc_marshal_read_v32(PyObject* self, PyObject* args) {
    GILHelper gil_helper;
    unsigned long u;
    if (!PyArg_ParseTuple(args, "k", &u))
        return nullptr;
    Marshal* m = (Marshal *) u;
    rpc::v32 v;
    *m >> v;
    long long vll = v.get();
    return Py_BuildValue("L", vll);
}

static PyObject* _pyrpc_marshal_write_v64(PyObject* self, PyObject* args) {
    GILHelper gil_helper;
    unsigned long u;
    long long vll;
    if (!PyArg_ParseTuple(args, "kL", &u, &vll))
        return nullptr;
    Marshal* m = (Marshal *) u;
    rpc::v64 v = vll;
    *m << v;
    Py_RETURN_NONE;
}


static PyObject* _pyrpc_marshal_read_v64(PyObject* self, PyObject* args) {
    GILHelper gil_helper;
    unsigned long u;
    if (!PyArg_ParseTuple(args, "k", &u))
        return nullptr;
    Marshal* m = (Marshal *) u;
    rpc::v64 v;
    *m >> v;
    long long vll = v.get();
    return Py_BuildValue("L", vll);
}


static PyObject* _pyrpc_marshal_write_double(PyObject* self, PyObject* args) {
    GILHelper gil_helper;
    unsigned long u;
    double dbl;
    if (!PyArg_ParseTuple(args, "kd", &u, &dbl))
        return nullptr;
    Marshal* m = (Marshal *) u;
    *m << dbl;
    Py_RETURN_NONE;
}


static PyObject* _pyrpc_marshal_read_double(PyObject* self, PyObject* args) {
    GILHelper gil_helper;
    unsigned long u;
    if (!PyArg_ParseTuple(args, "k", &u))
        return nullptr;
    Marshal* m = (Marshal *) u;
    double dbl;
    *m >> dbl;
    return Py_BuildValue("d", dbl);
}



static PyObject* _pyrpc_marshal_write_str(PyObject* self, PyObject* args) {
    GILHelper gil_helper;
    unsigned long u;
    PyObject* str_obj;
    if (!PyArg_ParseTuple(args, "kO", &u, &str_obj))
        return nullptr;
    Marshal* m = (Marshal *) u;
    std::string str(PyString_AsString(str_obj), PyString_Size(str_obj));
    *m << str;
    Py_RETURN_NONE;
}


static PyObject* _pyrpc_marshal_read_str(PyObject* self, PyObject* args) {
    GILHelper gil_helper;
    unsigned long u;
    if (!PyArg_ParseTuple(args, "k", &u))
        return nullptr;
    Marshal* m = (Marshal *) u;
    std::string str;
    *m >> str;
    PyObject* str_obj = PyString_FromStringAndSize(&str[0], str.size());
    return Py_BuildValue("O", str_obj);
}


static PyObject* _pyrpc_fini_future(PyObject* self, PyObject* args) {
    GILHelper gil_helper;
    unsigned long u;
    if (!PyArg_ParseTuple(args, "k", &u))
        return nullptr;
    Future* fu = (Future *) u;
    fu->release();
    Py_RETURN_NONE;
}

static PyObject* _pyrpc_future_wait(PyObject* self, PyObject* args) {
    GILHelper gil_helper;
    unsigned long u;
    if (!PyArg_ParseTuple(args, "k", &u))
        return nullptr;
    Future* fu = (Future *) u;

    if (!fu->ready()) {
        PyThreadState *_save;
        _save = PyEval_SaveThread();
        fu->wait();
        PyEval_RestoreThread(_save);
    }

    Py_RETURN_NONE;
}

static PyObject* _pyrpc_future_ready(PyObject* self, PyObject* args) {
    GILHelper gil_helper;
    unsigned long u;
    if (!PyArg_ParseTuple(args, "k", &u))
        return nullptr;
    Future* fu = (Future *) u;

    if (fu->ready()) {
        return Py_BuildValue("i", 1);
    } else {
        return Py_BuildValue("i", 0);
    }
}

static PyObject* _pyrpc_future_get_error_code(PyObject* self, PyObject* args) {
    GILHelper gil_helper;
    unsigned long u;
    if (!PyArg_ParseTuple(args, "k", &u))
        return nullptr;
    Future* fu = (Future *) u;

    if (!fu->ready()) {
        PyThreadState *_save;
        _save = PyEval_SaveThread();
        fu->wait();
        PyEval_RestoreThread(_save);
    }
    return Py_BuildValue("i", fu->get_error_code());
}

static PyObject* _pyrpc_future_get_reply(PyObject* self, PyObject* args) {
    GILHelper gil_helper;
    unsigned long u;
    if (!PyArg_ParseTuple(args, "k", &u))
        return nullptr;
    Future* fu = (Future *) u;

    if (!fu->ready()) {
        PyThreadState *_save;
        _save = PyEval_SaveThread();
        fu->wait();
        PyEval_RestoreThread(_save);
    }
    return Py_BuildValue("k", &fu->get_reply());
}

static PyObject* _pyrpc_init_async_queue(PyObject* self, PyObject* args) {
    GILHelper gil_helper;
    AsyncQueue* q = new AsyncQueue();
    return Py_BuildValue("k", q);
}

static PyObject* _pyrpc_fini_async_queue(PyObject* self, PyObject* args) {
    GILHelper gil_helper;
    unsigned long u;
    if (!PyArg_ParseTuple(args, "k", &u))
        return nullptr;
    AsyncQueue* q = (AsyncQueue *) u;
    q->release();
    Py_RETURN_NONE;
}

static PyObject* _pyrpc_async_queue_pop(PyObject* self, PyObject* args) {
    GILHelper gil_helper;
    unsigned long u;
    if (!PyArg_ParseTuple(args, "k", &u))
        return nullptr;
    AsyncQueue* q = (AsyncQueue *) u;
    PyThreadState *_save;
    _save = PyEval_SaveThread();
    i64 cb_id = q->pop();
    PyEval_RestoreThread(_save);
    return Py_BuildValue("l", cb_id);
}

static PyObject* _pyrpc_async_queue_push(PyObject* self, PyObject* args) {
    GILHelper gil_helper;
    unsigned long u;
    long v;
    if (!PyArg_ParseTuple(args, "kl", &u, &v))
        return nullptr;
    AsyncQueue* q = (AsyncQueue *) u;
    q->push(v);
    Py_RETURN_NONE;
}

static PyMethodDef _pyrpcMethods[] = {
    {"init_server", _pyrpc_init_server, METH_VARARGS, nullptr},
    {"fini_server", _pyrpc_fini_server, METH_VARARGS, nullptr},
    {"server_start", _pyrpc_server_start, METH_VARARGS, nullptr},
    {"server_unreg", _pyrpc_server_unreg, METH_VARARGS, nullptr},
    {"server_reg", _pyrpc_server_reg, METH_VARARGS, nullptr},

    {"init_poll_mgr", _pyrpc_init_poll_mgr, METH_VARARGS, nullptr},

    {"init_client", _pyrpc_init_client, METH_VARARGS, nullptr},
    {"fini_client", _pyrpc_fini_client, METH_VARARGS, nullptr},
    {"client_connect", _pyrpc_client_connect, METH_VARARGS, nullptr},
    {"client_sync_call", _pyrpc_client_sync_call, METH_VARARGS, nullptr},
    {"client_async_call", _pyrpc_client_async_call, METH_VARARGS, nullptr},

    {"init_marshal", _pyrpc_init_marshal, METH_VARARGS, nullptr},
    {"fini_marshal", _pyrpc_fini_marshal, METH_VARARGS, nullptr},
    {"marshal_size", _pyrpc_marshal_size, METH_VARARGS, nullptr},
    {"marshal_write_i8", _pyrpc_marshal_write_i8, METH_VARARGS, nullptr},
    {"marshal_read_i8", _pyrpc_marshal_read_i8, METH_VARARGS, nullptr},
    {"marshal_write_i16", _pyrpc_marshal_write_i16, METH_VARARGS, nullptr},
    {"marshal_read_i16", _pyrpc_marshal_read_i16, METH_VARARGS, nullptr},
    {"marshal_write_i32", _pyrpc_marshal_write_i32, METH_VARARGS, nullptr},
    {"marshal_read_i32", _pyrpc_marshal_read_i32, METH_VARARGS, nullptr},
    {"marshal_write_i64", _pyrpc_marshal_write_i64, METH_VARARGS, nullptr},
    {"marshal_read_i64", _pyrpc_marshal_read_i64, METH_VARARGS, nullptr},
    {"marshal_write_v32", _pyrpc_marshal_write_v32, METH_VARARGS, nullptr},
    {"marshal_read_v32", _pyrpc_marshal_read_v32, METH_VARARGS, nullptr},
    {"marshal_write_v64", _pyrpc_marshal_write_v64, METH_VARARGS, nullptr},
    {"marshal_read_v64", _pyrpc_marshal_read_v64, METH_VARARGS, nullptr},
    {"marshal_write_double", _pyrpc_marshal_write_double, METH_VARARGS, nullptr},
    {"marshal_read_double", _pyrpc_marshal_read_double, METH_VARARGS, nullptr},
    {"marshal_write_str", _pyrpc_marshal_write_str, METH_VARARGS, nullptr},
    {"marshal_read_str", _pyrpc_marshal_read_str, METH_VARARGS, nullptr},

    {"fini_future", _pyrpc_fini_future, METH_VARARGS, nullptr},
    {"future_wait", _pyrpc_future_wait, METH_VARARGS, nullptr},
    {"future_ready", _pyrpc_future_ready, METH_VARARGS, nullptr},
    {"future_get_error_code", _pyrpc_future_get_error_code, METH_VARARGS, nullptr},
    {"future_get_reply", _pyrpc_future_get_reply, METH_VARARGS, nullptr},

    {"init_async_queue", _pyrpc_init_async_queue, METH_VARARGS, nullptr},
    {"fini_async_queue", _pyrpc_fini_async_queue, METH_VARARGS, nullptr},
    {"async_queue_pop", _pyrpc_async_queue_pop, METH_VARARGS, nullptr},
    {"async_queue_push", _pyrpc_async_queue_push, METH_VARARGS, nullptr},

    {nullptr, nullptr, 0, nullptr}
};

PyMODINIT_FUNC init_pyrpc(void) {
    PyEval_InitThreads();
    GILHelper gil_helper;
    PyObject* m;
    m = Py_InitModule("_pyrpc", _pyrpcMethods);
    if (m == nullptr)
        return;
}
