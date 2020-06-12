"""
Appliancizer cooper pouring.

Adds cooper pouring to routed bords.

Usage:
  addCooperPour.py
"""

import os
from Swoop import Swoop
from docopt import docopt

def main(arguments):

  # Python program path
  pyPath = os.path.dirname(os.path.realpath(__file__)) + "/"

  board = Swoop.EagleFile.from_file(pyPath + 'ROUTED.brd');
  # print(board.signals["GND"].polygons[0].__dict__);  #__dict__

  # Get width and hegith 
  pcbHeight = 0
  pcbWidth = 0
  for wire in board.plain_elements:
    x = wire.get_x1()
    y = wire.get_y1()
    if (x != 0):
      pcbWidth = x
    if (y != 0):
      pcbHeight = y  

  # Add Top Ground Pour
  TopGNDPour = (Swoop.Polygon()
  .set_layer("Top")
  .set_isolate(0.3048)
  .set_width(0.2)
  .set_thermals(False)
  .add_vertex(
    Swoop.Vertex()
    .set_x(pcbWidth)
    .set_y(pcbHeight))
  .add_vertex(
    Swoop.Vertex()
    .set_x(0)
    .set_y(pcbHeight))
  .add_vertex(
    Swoop.Vertex()
    .set_x(0)
    .set_y(0))
  .add_vertex(
    Swoop.Vertex()
    .set_x(pcbWidth)
    .set_y(0),
  ))
  TopGNDPour.parent = board.signals["GND"]; # Add Parent
  board.signals["GND"].polygons.append(TopGNDPour);

  # Add Bottom Ground Pour
  BottomGNDPour = (Swoop.Polygon()
  .set_layer("Bottom")
  .set_isolate(0.3048)
  .set_width(0.2)
  .set_thermals(False)
  .add_vertex(
    Swoop.Vertex()
    .set_x(pcbWidth)
    .set_y(pcbHeight))
  .add_vertex(
    Swoop.Vertex()
    .set_x(0)
    .set_y(pcbHeight))
  .add_vertex(
    Swoop.Vertex()
    .set_x(0)
    .set_y(0))
  .add_vertex(
    Swoop.Vertex()
    .set_x(pcbWidth)
    .set_y(0),
  ))
  BottomGNDPour.parent = board.signals["GND"]; # Add Parent
  board.signals["GND"].polygons.append(BottomGNDPour);

  # Write final board file
  board.write(pyPath + 'ROUTED_POUR.brd');

  # <polygon width="0.2" layer="1" isolate="0.254" thermals="no">
  # <vertex x="171" y="-87"/>
  # <vertex x="0" y="-87"/>
  # <vertex x="0" y="0"/>
  # <vertex x="171" y="0"/>
  # </polygon>


if __name__ == '__main__':
    arguments = docopt(__doc__, version='Appliancizer Cooper Pouring v1.0')
    main(arguments)