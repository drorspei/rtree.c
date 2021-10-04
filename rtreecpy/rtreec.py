import ctypes
import pyarrow
import numpy as np
import os

rt = ctypes.CDLL(os.path.join(os.path.dirname(__file__), "librtreec.so"))

rt.rtree_new.argtypes = [ctypes.c_size_t, ctypes.c_int]
rt.rtree_new.restype = ctypes.c_void_p

rt.rtree_free.argtypes = [ctypes.c_size_t]
rt.rtree_free.restype = None

rt.rtree_insert.argtypes = [
    ctypes.c_void_p,
    ctypes.POINTER(ctypes.c_double),
    ctypes.POINTER(ctypes.c_int64)
]
rt.rtree_insert.restype = ctypes.c_bool

rt.rtree_delete.argtypes = [
    ctypes.c_void_p,
    ctypes.POINTER(ctypes.c_double),
    ctypes.POINTER(ctypes.c_int64)
]
rt.rtree_delete.restype = ctypes.c_bool

rtree_iter = ctypes.CFUNCTYPE(
    ctypes.c_bool,
    ctypes.POINTER(ctypes.c_double),
    ctypes.POINTER(ctypes.c_int64),
    ctypes.c_void_p
)

rt.rtree_search.argtypes = [
    ctypes.c_void_p,
    ctypes.POINTER(ctypes.c_double),
    rtree_iter,
    ctypes.c_void_p
]
rt.rtree_search.restype = ctypes.c_bool

rt.rtree_search_batch.restype = ctypes.c_bool
rt.rtree_search_batch.argtypes = [
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_double),
        ctypes.c_int64,
        ctypes.POINTER(ctypes.c_int64),
        ctypes.POINTER(ctypes.c_int64),
        ctypes.POINTER(ctypes.c_int64),
]

rt.free.argtypes = [ctypes.c_void_p]
rt.free.restype = None

class RTree:
    def __init__(self, dimensions):
        self.dimensions = dimensions
        self._handle = rt.rtree_new(8, dimensions)

    def insert(self, i, rect):
        assert rect.ndim == 1
        assert rect.shape[0] == 2 * self.dimensions

        return rt.rtree_insert(
            self._handle,
            rect.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            ctypes.pointer(ctypes.c_int64(i))
        )
    
    def delete(self, i, rect):
        assert rect.ndim == 1
        assert rect.shape[0] == 2 * self.dimensions

        return rt.rtree_delete(
            self._handle,
            rect.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            ctypes.pointer(ctypes.c_int64(i))
        )

    def search(self, rect):
        rect = np.asarray(rect)
        assert rect.ndim == 1
        assert rect.shape[0] == 2 * self.dimensions

        ret = []
        
        @rtree_iter
        def iter_(rect, item, udata):
            ret.append(item[0])
            return True
            
        rt.rtree_search(
            self._handle,
            rect.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            iter_,
            0
        )
        
        return ret

    def search_batch(self, rects):
        rects = np.asarray(rects)
        assert rects.ndim == 2
        assert rects.shape[1] == 2 * self.dimensions

        out_offsets = ctypes.pointer(ctypes.c_int64())
        out_values = ctypes.pointer(ctypes.c_int64())
        out_size = ctypes.pointer(ctypes.c_int64())

        rt.rtree_search_batch(
            self._handle,
            self.dimensions,
            rects.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            len(rects),
            out_offsets,
            out_values,
            out_size
        )

        size = out_size[0]
        offsets = np.ctypeslib.as_array(
            ctypes.cast(out_offsets[0], ctypes.POINTER(ctypes.c_int32)),
            shape=(size,)
        ).copy()

        size_values = offsets[-1]

        values = np.ctypeslib.as_array(
            ctypes.cast(out_values[0], ctypes.POINTER(ctypes.c_int64)),
            shape=(size_values,)
        ).copy()

        offsets = pyarrow.array(offsets)
        values = pyarrow.array(values)

        ret = pyarrow.ListArray.from_arrays(
            offsets, values
        )

        rt.free(out_offsets[0])
        rt.free(out_values[0])

        return ret

    def __del__(self):
        rt.rtree_free(self._handle)


def tests():
    tree = RTree(2)
    tree.insert(1729, np.r_[1., 1., 2., 2.])
    assert not tree.search(np.r_[0., 0, 0.5, 0.5])
    assert tree.search(np.r_[0., 0., 1.5, 1.5]) == [1729]
    
    print(tree.search_batch([
        [0., 0., 0.5, 0.5],
        [0., 0., 1.5, 1.5]
    ]))

    tree = RTree(3)
    a = np.random.randn(100000, 3)
    print("inserting")
    for i, aa in enumerate(a):
        tree.insert(i, np.r_[aa, aa])
    import gc
    print("searching")
    for _ in range(1000):
        for _ in range(10):
            tree.search_batch(np.c_[a-0.02, a+0.02])
        gc.collect()


if __name__ == "__main__":
    tests()
