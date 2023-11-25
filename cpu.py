from enum import Enum
import binascii
import struct

MAGIC_START = 0x80000000

def bitrange(ins, s, e):
  return (ins >> e) & ((1 << (s - e + 1)) - 1)

def sign_extend(x, l):
  if x >> (l-1) == 1:
    return -((1 << l) - x)
  else:
    return x

class OPS(Enum):
  JAL = 0b1101111

class InvalidMemory(Exception):
  def __init__(self, message="Invalid memory address"):
    super(InvalidMemory, self).__init__(message)

class Register:
  PC = 32
  def __init__(self, *args, **kwargs):
    self.regs = [0]*33
  def __getitem__(self, key):
    return self.regs[key]
  def __setitem__(self, key, val):
    if key == 0: return
    self.regs[key] = val & 0xffffffff
  def __repr__(self):
    return f"PC: {self.regs[32]:08x}"


class CPU:
  def __init__(self):
    self.regs = Register()
    self.regs[Register.PC] = MAGIC_START
    # 16KB at 0x80000000
    self.memory = b'\x00'*0x4000
  
  def load(self, addr, data):
    addr -= MAGIC_START
    if addr < 0 and addr >= len(self.memory): raise InvalidMemory(f"Address {addr:08x} is out of bound for {len(self.memory):08x}")
    self.memory = self.memory[:addr] + data + self.memory[addr+len(data):]
  
  def read32(self, addr):
    addr -= MAGIC_START
    if addr < 0 and addr >= len(self.memory): raise InvalidMemory(f"Address {addr:08x} is out of bound for {len(self.memory):08x}")
    return struct.unpack("<I", self.memory[addr:addr+4])[0]
  
  # TOOD: For refractoring?
  def decode(self, ins):
    raise NotImplementedError
  
  def execute(self, opcode, *args):
    raise NotImplementedError
  
  def step(self):
    print(self.regs)
    # Fetch
    ins = self.read32(self.regs[Register.PC])

    # Decode
    opcode = OPS(bitrange(ins, 6, 0))
    print(hex(ins), opcode)
    # J-type
    imm = sign_extend((bitrange(ins, 32, 31) << 20 | bitrange(ins, 19, 12) << 12 | bitrange(ins, 21, 20) << 11 | bitrange(ins, 30, 21) << 1), 21)
    rd = bitrange(ins, 11, 7)
    if opcode == OPS.JAL:
      self.regs[Register.PC] += imm
    
    print(self.regs)
  

  def coredump(self, start_addr=MAGIC_START, l=16, filename=None):
    start_addr -= MAGIC_START
    dump = [binascii.hexlify(self.memory[i:i+4][::-1]) for i in range(0,len(self.memory),4)]
    if filename is not None:
      with open(f"test-cache/{filename}") as f: f.write(b'\n'.join(dump))
    else:
      # Print core dump
      for i in range(start_addr//4, start_addr//4+l, 4):
        row = ' '.join(f"0x{chunk.decode('utf-8')}" for chunk in dump[i: i+4])
        print(f"0x{i*4+MAGIC_START:08x} {row}")

  def run(self):
    while True:
      self.step()
      break
