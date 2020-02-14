"""
Appliancizer Builder.

Builds EAGLE boards for Appliancizer.
    Module schematics must be in the current working directory.
    Internal nets must contain the string "INTERNAL" or the string "$".
    Must add "part name field to connector.partpositions"

Usage:
  builder.py [-v | --debug] JSON_FILE

Options:
  --debug    Debugging output.
  -v         Verbose output.
"""


import json


from docopt import docopt


from Swoop.Swoop import Swoop

def rebuildBoardConnections(sch, brd):
    """
    Update the signals in :code:`brd` to match the nets in :code:`sch`.  This will set up the connections, but won't draw the air wires.  You can use Eagle's :code:`ripup` command to rebuild those.

    :param sch: :class:`SchematicFile` object and source of the connection information.
    :param brd: :class:`BoardFile` destination for then connection information.
    :rtype: :code:`None`
    
    """
    #sheets/*/net.name:
    for name in Swoop.From(sch).get_sheets().get_nets().get_name():
        sig =  brd.get_signal(name)
        if sig is None:
            brd.add_signal(Swoop.Signal().
                           set_name(name).
                           set_airwireshidden(False).
                           set_class("0")) # We need to do something smarter here.
        else:
            sig.clear_contactrefs()

        for pinref in (Swoop.From(sch).
                       get_sheets().
                       get_nets().
                       with_name(name).
                       get_segments().
                       get_pinrefs()):

            if sch.get_part(pinref.part).find_device().get_package() is None:
                continue

            pads = (Swoop.From(sch).
                   get_parts().
                   with_name(pinref.get_part()).
                   find_device().
                   get_connects().
                   with_gate(pinref.gate).
                   with_pin(pinref.pin).
                   get_pads())

            assert pads is not None;
            if pads is None:
                log.warn("Can't find pads for '{}:{}.{}' on net '{}'".format(pinref.get_part(), pinref.gate, pinref.pin, name))

            for pad in pads:
                brd.get_signal(name).add_contactref(Swoop.Contactref().
                                                    set_element(pinref.get_part()).
                                                    set_pad(pad))

def propagatePartToBoard(part, brd):

    """
    Copy :code:`part` to ``brd`` by creating a new :class:`Element` and populating it accordingly.
    If the part already exists, it will be replaced.  Attributes are not displayed by default, but the display layer is set to "Document".
    
    If the library for the part is missing in the board, it will be create.  If the package is missing, it will be copied.  If it exists and the package for the part and the package in the board are not the same, raise an exception.

    .. Note::
       This function doesn't update the board's signals.  You can run :meth:`rebuildBoardConnections` to do that.

    :param part: :class:`Part` object that to propagate.
    :param brd: Destination :class`BoardFile`.
    :rtype: :code:`None`

    """
    if part.find_device().get_package() is None:
        return
    
    if part.find_package() is None:
        raise Swoop.SwoopError("Can't find package for '{}' ({}.{}.{}.{}).".format(part.get_name(), part.get_library(), part.get_deviceset(), part.get_device(), part.get_technology()))

    dst_lib = brd.get_library(part.get_library())

    if dst_lib is None:
        dst_lib = Swoop.Library().set_name(part.get_library())
        brd.add_library(dst_lib)

    #src_lib = part.find_library()
    #assert src_lib is not None, "Missing library '{}' for part '{}'".format(part.get_library(), part.get_name())
    
    dst_package = dst_lib.get_package(part.find_package().get_name())
    if dst_package is None:
        dst_package = part.find_package().clone()
        dst_lib.add_package(dst_package)
    else:
        assert dst_package.is_equal(part.find_package()), "Package from schematic is not the same as package in board"

    # Reverse-engineered logic about setting values in board files.
    if part.find_deviceset().get_uservalue():
        fallback_value = ""
    else:
        fallback_value = part.get_deviceset()+part.get_device()
    
    n =(Swoop.Element().
        set_name(part.get_name()).
        set_library(part.get_library()).
        set_package(part.
                    find_package().
                    get_name()).
        set_value(part.get_value() if part.get_value() is not None else fallback_value).
        set_x(0).
        set_y(0))

    brd.add_element(n)


def build_board_from_schematic(sch, template_brd):
    """
    Create a minimal board from a schematic file.  :code:`template_brd` is modified and returned.
    
    :param sch: the input schematic
    :param brd: a template :class:`BoardFile`
    :returns: A :class:`BoardFile` object that is consistent with the schematic.
    """

    for part in sch.get_parts():
        propagatePartToBoard(part, template_brd)

    rebuildBoardConnections(sch, template_brd)
    return template_brd


def debug_print(*args, sep=' ', end='\n', file=None):
    print(*args, sep=sep, end=end, file=file)


def main(arguments):
    debug_mode = arguments['--debug'] or arguments['-v']

    with open(arguments['JSON_FILE'], 'r') as f:
        device_spec = json.loads(f.read())
    debug_print(device_spec)

    schematic_bases = {}
    unique_schematics = {}
    renamed_nets = {}
    component_positions = {}
    device_spec['modules']['connector'] = device_spec['connector']
    for module_name, module_info in device_spec['modules'].items(): # for each module in the design, not the raspi
        debug_print(module_name, module_info)

        schematic_name = module_info['schematicName']
        if schematic_name not in schematic_bases: # get the base schematic
            schematic_bases[schematic_name] = Swoop.EagleFile.from_file(schematic_name + '.sch')
        unique_schematics[module_name] = schematic_bases[schematic_name].clone() # save a copy for the module

        renamed_nets[module_name] = set()
        # rename nets to make connections
        if 'interfaces' in module_info:
            for interface_name, interface_info in module_info['interfaces'].items(): # for each interface
                net_names = Swoop.From(unique_schematics[module_name]).get_sheets().get_nets().get_name()

                for net_name, connection in interface_info.items(): # each entry is a potential net
                    if net_name in net_names:
                        print('Connecting net:', net_name, 'to', connection)
                        # get the net
                        net = (Swoop.
                            From(unique_schematics[module_name]).
                            get_sheets().
                            get_nets().
                            with_name(net_name)
                        )[0]
                        net.set_name(connection) # rename the net
                        renamed_nets[module_name].add(connection)

        # make nets unique
        # the non-renamed nets need to be unique
        for net in Swoop.From(unique_schematics[module_name]).get_sheets().get_nets():
            debug_print('Checking if net: ' + str(net.get_name()) + ' needs to be uniquified...')

            # several options for finding internal nets
            # if net.get_name() not in renamed_nets[module_name]: # not renamed
            # if 'INTERNAL' in net.get_name():
            # if '$' in net.get_name():
            if 'INTERNAL' in net.get_name() or '$' in net.get_name():
                debug_print('It does...')
                new_name = net.get_name() + '__' + module_name
                print('Changing to name: ' + str(new_name))
                net.set_name(new_name)

        part_positions = device_spec['modules'][module_name]['partsPosition']
        for p_name, p_info in part_positions.items():
            refdes = p_info['componentName']
            p_x = p_info['componentX']
            p_y = p_info['componentY']
            unique_name = refdes.upper() + '_' + module_name.upper()
            component_positions[unique_name] = (p_x, p_y)

        # make components unique
        for part in Swoop.From(unique_schematics[module_name]).get_parts():
            print('Looking at part:', part)
            old_name = part.name
            print('Name:', old_name)
            unique_schematics[module_name].remove_part(part)
            part.name = old_name.upper() + '_' + module_name.upper()
            unique_schematics[module_name].add_part(part)



            for instance in Swoop.From(unique_schematics[module_name]).get_sheets().get_instances():
                    print(instance.part)
                    if instance.part == old_name:
                        instance.part = part.name


            for pinref in Swoop.From(unique_schematics[module_name]).get_sheets().get_nets().get_segments().get_pinrefs():
                print('pinref:', pinref)
                if pinref.part == old_name:
                    pinref.part = part.name

        print('Renamed all parts, verifying')

        for part in Swoop.From(unique_schematics[module_name]).get_parts():
            print('Looking at part:', part)
            name = part.name
            print('Name:', name)


    # concat sheets together
    first_sch = None
    # seperate the first sheets
    for module_name, schematic in unique_schematics.items(): 
        first_sch = schematic
        break

    # get the rest of the sheets
    for module_name, schematic in unique_schematics.items():
        if schematic == first_sch:
            print('Not adding first_sch')
            continue
        print(module_name, schematic)
        sheets = schematic.get_sheets()
        print(sheets)
        for sheet in sheets:
            first_sch.add_sheet(sheet)

        for part in schematic.get_parts():
            library_name = part.get_library()
            print(library_name)
            library = schematic.get_library(library_name)
            print(library)
            first_sch.add_library(library)
            first_sch.add_part(part)


    combined_sheets = first_sch.get_sheets()
    print('combined_sheets:', combined_sheets)

    # make board
    template_brd_filename = 'template.brd'
    template_brd = Swoop.EagleFile.from_file(template_brd_filename)
    board = build_board_from_schematic(first_sch, template_brd)
    for part in board.get_elements():
        if part.name in component_positions:
            part.x = component_positions[part.name][0]
            part.y = component_positions[part.name][1]


    # do board outline

    board.write('combined.brd')

    # do placement

    # do routing

    # do CAM

    # for module_name, sch in unique_schematics.items():
    #     new_name = module_name + '_test.sch'
    #     print('Writing out schematic: ', new_name)
    #     sch.write(new_name)

    sch_file_name = 'combined.sch'
    print('Writing out full schematic:', sch_file_name)
    first_sch.write(sch_file_name)


if __name__ == '__main__':
    arguments = docopt(__doc__, version='Appliancizer Builder v1.0')
    print(arguments)
    print(Swoop)
    main(arguments)






