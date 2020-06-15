#VTA pyhcl implementation of core/Store.scala
#Aothor:Lois799
#created on 2020/06/10
#Store.scala 与 Load.scala 较相似，我重构Store.scala是参考了原有的Load.scala和Sunny Chen重构得到的load.py
#通过对比Load.scala和load.py，及学习了部分python与部分scala语法，所得该store.py;
#可能有些遗漏，迷惑，已标注
/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

from pyhcl import *
from vta.core.isa import *
from vta.shell.parameters import *
from vta.util.ext_funcs import *
from vta.shell.vme import *

/** Store.
  *
  * Store results back to memory (DRAM) from scratchpads (SRAMs).
  * This module instantiate the TensorStore unit which is in charge
  * of storing 1D and 2D tensors to main memory.
  */
  
  #参考load.py对Load 的重构
  def store(debug:bool = False):
    p = ShellKey()
    mp= p.memParams
    
    class Inst(baseType):
      def __init__(self):
        self.inst = U.w(INST_BITS)
        
    class Store(Module):
      #Base IO
      io=IO(
        i_post=Input(Bool),
        o_post=Output(Bool),
        out_baddr=Input(U.w(mp.addrBits)),
        out = new TensorClient(tensorType = "out")
        
        /*val inst = Flipped(Decoupled(UInt(INST_BITS.W)))/*可能是不用重构的，也可能是在后面*/      
       ）
      decoupled(io, Inst(), is_fliped=True)
      
      #val vme_wr = new VMEWriteMaster //参考load.py对vme_rd = Vec(2, new VMEReadMaster)的重构方法
      VMEReadMaster_io = VMEReadMaster()
      cat_io(io, VMEReadMaster_io, 'vme_wr')
      
      #val sIdle :: sSync :: sExe :: Nil = Enum(3)
      #val state = RegInit(sIdle)
      sIdle, sSync, sExe = [U(i) for i in range(3)]
      state = RegInit(sIdle)
       
      s = semaphore(counterBits=8, counterInitValue=0)
      inst_q = queue(U.w(INST_BITS), p(CoreKey).instQueueEntries))
      
      dec=LoadDecode()
      dec.io.inst <<= inst_q.io.deq.bits
      
      tensorStore = Module(new TensorStore(tensorType = "out"))
      
      start=inst_q.io.deq.valid & Mux(dec.io.pop_next, s.io.sready, Bool(True))
      done = tensorStore.io.done
      
      #control
      with when(state == sIdle):
            with when(start):
                with when(dec.io.isSync):
                    state <<= sSync
                with elsewhen((dec.io.isInput) | (dec.io.isWeight)):
                    state <<= sExe
        with elsewhen(state == sSync):
            state <<= sIdle
        with elsewhen(state == sExe):
            with when(done):
                state <<= sIdle
            
       #insturctions
       inst_q.io.enq <> io.inst
       inst_q.io.deq.ready <<= (state == sExe & done) | (state == sSync)
       
       #store
       tensorStore.io.start <<= state == sIdle & start & dec.io.isStore
       tensorStore.io.inst <<= inst_q.io.deq.bits
       tensorStore.io.baddr <<= io.out_baddr
       io.vme_wr <> tensorStore.io.vme_wr
       tensorStore.io.tensor <> io.out

       #semaphore
       s.io.spost <<= io.i_post
       s.io.swait <<= dec.io.pop_next & (state == sIdle & start)
       io.o_post <<= dec.io.push_next & ((state == sExe & done) | (state == sSync))
       
       #debug
       with when (debug):
        #start
        with when((state == sIdle) & (start)):
           with when(dec.io.isSync):
             printf("[Store] start sync\n")
           with elsewhen(dec.io.isStore):
            printf("[Store] start\n")
        #done
        with when(state == sSync):
         printf("[Store] done sync\n")
        with when(state == sExe):
          with when(done):
           printf("[Store] done\n")

      
      
