"""rvir firmware for Blackhole Tensix tiles.

Builds all 5 core firmware images using the rvir assembler, producing
the same firmware dict format that fw.boot() expects.

Usage:
    from rvir_kernels.firmware import build_all
    from extra.emu.device import Device
    from extra.emu import fw

    device = Device()
    firmware = build_all()
    fw.boot(device, firmware)
    # device is now ready for kernel dispatch
"""

from . import brisc, ncrisc, trisc0, trisc1, trisc2


def build_all():
    """Build firmware for all 5 cores.

    Returns:
        dict mapping core name to firmware dict with
        'segments' and 'text_base' keys.
    """
    return {
        'brisc':  brisc.build(),
        'ncrisc': ncrisc.build(),
        'trisc0': trisc0.build(),
        'trisc1': trisc1.build(),
        'trisc2': trisc2.build(),
    }
