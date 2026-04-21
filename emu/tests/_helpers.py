from emu.device import Device


def mini_device(**kw):
  return Device(tensix_x=(1,), tensix_y=(2,), **kw)
