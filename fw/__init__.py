from fw.brisc import build as build_brisc
from fw.ncrisc import build as build_ncrisc
from fw.trisc import build_trisc0, build_trisc1, build_trisc2

def build_all():
  return {
    "brisc": build_brisc(),
    "ncrisc": build_ncrisc(),
    "trisc0": build_trisc0(),
    "trisc1": build_trisc1(),
    "trisc2": build_trisc2(),
  }
