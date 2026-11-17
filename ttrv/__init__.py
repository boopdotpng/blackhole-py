"""ttrv: a kernel language for Blackhole (docs/ttrv_spec.md).

  source --parse--> tree --expand--> flat tree --layout--> + resource map
         --codegen, once per RISC--> items --emit--> five images, listing, manifest

Five separate programs: each entry function (brisc, ncrisc, trisc0-2) and the functions it calls compile to one image.
build() is the driver: parse, expand and layout once, then codegen + emit per RISC."""

def build():
  pass
