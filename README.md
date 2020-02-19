# JSON to EAGLE brd

Creates an EAGLE brd from a json file.

Requires NVSL/Swoop library.

`python3 builder.py --help`

`python3 builder.py VideoPlayer.json`

`python3 builder.py -i '{ "pcbHeight": 16, "pcbWidth": 56, "connector": { "schematicName": "connector_raspberrypi", "netsAvailabe": [ "4", "17", "27", "22", "5", "6", "13", "26", "18", "23", "24", "25", "12", "16", "19", "20", "21", "2", "3", "9", "10", "11", "8", "14", "15", "3.3V", "5V" ], "partsPosition": { "part_0": { "componentName": "J1", "componentX": 26.5, "componentY": 2.5 } } }, "modules": { "module_0": { "schematicName": "tactile_push_button_smd", "interfaces": { "iface_0": { "type": "gpio", "GPIO": "4" } }, "partsPosition": { "part_0": { "componentName": "S1", "componentX": 6.75, "componentY": 10 }, "part_1": { "componentName": "R1", "componentX": 15.6, "componentY": 10.8 } } } } }'`
