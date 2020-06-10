# VTA pyhcl implementation of core/TensorLoad.scala
# Author: SunnyChen
# Date:   2020-06-08


from pyhcl import *
from vta.core.decode import MemDecode_Div
from vta.core.isa import *
from vta.core.tensorutil import *
from vta.shell.vme import VMEReadMaster

"""
    TensorLoad.
    
    Load 1D and 2D tensors from main memory (DRAM) to input/weight
    scratchpads (SRAM). Also, there is support for zero padding, while
    doing the load. Zero-padding works on the y and x axis, and it is
    managed by TensorPadCtrl. The TensorDataCtrl is in charge of
    handling the way tensors are stored on the scratchpads.
"""


def tensorload(tensorType: str = "none", debug: bool = False):
    tp = TensorParams(tensorType)
    mp = ShellKey().memParams

    class TensorLoad_IO(Bundle_Helper):
        def __init__(self):
            self.start = Input(Bool)
            self.done = Input(Bool)
            self.inst = Input(U.w(INST_BITS))
            self.baddr = Input(U.w(mp.addrBits))
            self.vme_rd = VMEReadMaster()
            self.tensor = TensorClient(tensorType)

    class TensorLoad(Module):
        io = mapper(TensorLoad_IO())

        sizeFactor = tp.tensorLength * tp.numMemBlock
        strideFactor = tp.tensorLength * tp.tensorWidth

        dec = MemDecode_Div(io.inst)

    return TensorLoad()