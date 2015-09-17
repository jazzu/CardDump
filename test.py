import pyudev

context = pyudev.Context()

for device in context.list_devices(subsystem='block', DEVTYPE='partition'):
    print(device.device_node)
    p = device.find_parent('usb', 'usb_device')
    if p:
        print(p.attributes['manufacturer'], p.attributes['product'], p.device_path)
