from typing import Any
from algopy import ARC4Contract
from algopy.arc4 import abimethod , UInt64 , Struct , DynamicBytes
from algopy import BoxMap
from algopy import subroutine

# class ChunkStorage(Struct):
#     chunk1 : DynamicBytes

class HelloWorld(ARC4Contract):

    def __init__(self) -> None:
        self.MyStorage = BoxMap(UInt64 , DynamicBytes , key_prefix=b"sanyam")
