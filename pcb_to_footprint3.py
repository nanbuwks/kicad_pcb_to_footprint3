#-------------------------------------------------------------------------------
# Name:     pcb_to_footprint3
# Purpose:  Convert a kicad_pcb to a module (footprint)
#
# Author:   Yoshimasa Kawano 
# License:  GPL v3
# fork from pcb_to_footprint # Bob Cousins # License:  GPL v3 Copyright Bob Cousins 2017
# Credits:  ignamv@github for https://github.com/ignamv/kicad_scripts/blob/master/place_footprints.py
#           Thomas Pointhuber for KicadModTree https://github.com/pointhi/kicad-footprint-generator
# Usage:
#  - Open the Python console in pcbnew
#  - copy and paste (use Paste Plus) the following lines in to the console:
#       import sys
#       sys.argv = ['pcb_to_footprint.py', 'c:\\temp2\\smart_rgb_led_at85']
#       execfile ("C:\Python_progs\pcb_to_footprint\pcb_to_footprint\pcb_to_footprint.py")
#
#    set the location of your project and pcb_to_footprint.py accordingly.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Parameters :
# set the refs of modules which will have external connections:

#connector_refs = ("P1", "P2","U1","U5","P3","BT1","U4","P4","P5","P7","P8")
connector_refs = ("P1", "P2","U1")
#connector_refs = ("IOL1", "IOH1", "AD1", "POWER1", "ICSP2", "@HOLE1", "@HOLE2", "@HOLE3", "@HOLE4")

copy_all = False
#-------------------------------------------------------------------------------




from os import sys

#sys.path.append("C:\Programs\KiCad\bin")
#sys.path.append("C:\Programs\KiCad\lib\python2.7\site-packages")
#print sys.path

import pcbnew
import shutil
import argparse
import os
import glob
#
#sys.path.append("C:\\github\\kicad-footprint-generator")
sys.path.append("kicad-footprint-generator-master")
from KicadModTree import *

def wait():
    print('\nPress any key to continue')
    raw_input()

def find_file(extension):
    filename = os.path.join(directory, project_name + '.' + extension)
    if not os.path.exists(filename):
        matches = glob.glob(os.path.join(directory, '*.' + extension))
        if not matches:
            raise IOError('File not found')
        if len(matches) > 1:
            raise IOError('Too many matches')
        return matches[0]
    return filename


def to_mm(nm):
    return nm / 1e6


parser = argparse.ArgumentParser(description="""\
Create a footprint from a pcb.
Your project needs to have a .kicad-pcb file.""")
parser.add_argument('project', nargs='?', help='Kicad project')
# parser.add_argument('--schematic', help='Input .sch file')
parser.add_argument('--pcb', help='Input .kicad_pcb file')
args = parser.parse_args()

#
if args.pcb:
    pcbfile = args.pcb
else:
    if os.path.isfile(args.project):
        # If the user passed the .pro file, extract the directory
        directory = os.path.dirname(args.project)
        project_name = os.path.basename(args.project)
        project_name = project_name[:project_name.rindex('.')]
    else:
        directory = args.project
        try:
            project_name = glob.glob(os.path.join(directory, '*.pro'))[0][:-4]
        except IndexError:
            print( "Directory %s does not have a .pro file" % directory)
            #wait()
            exit(-1)
    print('Found project ' + project_name)

    try:
        pcbfile = find_file('kicad_pcb')
    except IOError as e:
        print('Error searching for .kicad_pcb file: {}'.format(e))
        #wait()
        exit(-1)
    print('Found pcb: ' + pcbfile)



board = pcbnew.LoadBoard(pcbfile)

min_x = sys.maxsize
min_y = sys.maxsize

max_x = -sys.maxsize
max_y = -sys.maxsize

for segment in board.GetDrawings():
    if pcbnew.DRAWSEGMENT_ClassOf (segment):
        if segment.GetLayer () == 44:   ## edge cuts
            #print "edge at %s - %s" % (segment.GetStart(), segment.GetStart() )
            if segment.GetStart().x < min_x:
                min_x = segment.GetStart().x
            if segment.GetStart().y < min_y:
                min_y = segment.GetStart().y
            if segment.GetEnd().x < min_x:
                min_x = segment.GetEnd().x
            if segment.GetEnd().y < min_y:
                min_y = segment.GetEnd().y
            #
            if segment.GetStart().x > max_x:
                max_x = segment.GetStart().x
            if segment.GetStart().y > max_y:
                max_y = segment.GetStart().y
            if segment.GetEnd().x > max_x:
                max_x = segment.GetEnd().x
            if segment.GetEnd().y > max_y:
                max_y = segment.GetEnd().y
#
print("origin %d, %d" % (to_mm(min_x), to_mm(min_y)))

bbox = board.ComputeBoundingBox(True)
#print "bbox %s %s" % (bbox.GetPosition(), bbox.GetSize())


#module = board.FindModuleByReference("P1")
#print "%s %s" % (module.GetReference(), module.GetValue() )
#for pad in module.Pads():
    #pos = pad.GetPosition()
    #print "pad %s at %d,%d" % (pad.GetPadName(), pos.x - min_x, pos.y - min_y)



#
footprint_name = project_name

# init kicad footprint
kicad_mod = Footprint(os.path.basename(project_name))
kicad_mod.setDescription("Converted from " + os.path.basename(project_name))
#kicad_mod.setTags("example")

# set general values
kicad_mod.append(Text(type='reference', text='REF**', at=[0,-3], layer='F.SilkS'))
kicad_mod.append(Text(type='value', text=os.path.basename(project_name), at=[0,-1.5], layer='F.Fab'))

# create silkscreen
# kicad_mod.append(RectLine(start=[to_mm(0),to_mm(0)], end=[to_mm(max_x-min_x),to_mm(max_y-min_y)], layer='F.SilkS', width=0.15))

for segment in board.GetDrawings():
    if pcbnew.DRAWSEGMENT_ClassOf (segment):
        if segment.GetLayer () == 44:   ## edge cuts
            layer = 'F.SilkS'
        else:
            layer = ""

        if layer != "":
            if segment.GetShape() == 0:
                pos = segment.GetStart()
                start = [to_mm(pos.x-min_x), to_mm(pos.y-min_y) ]
                pos = segment.GetEnd()
                end = [to_mm(pos.x-min_x), to_mm(pos.y-min_y) ]
                kicad_mod.append(Line(start=start, end=end, layer=layer, width=0.15))
            elif segment.GetShape() == 2:
                pos = segment.GetArcStart()
                start = [to_mm(pos.x-min_x), to_mm(pos.y-min_y) ]
                pos = segment.GetArcEnd()
                end = [to_mm(pos.x-min_x), to_mm(pos.y-min_y) ]
                pos = segment.GetCenter()
                center = [to_mm(pos.x-min_x), to_mm(pos.y-min_y) ]
                kicad_mod.append(Arc(start=start, end=end, center=center, angle=segment.GetAngle()/10, layer='F.SilkS', width=0.15))

if copy_all:
    for track in board.GetTracks():
        if pcbnew.TRACK_ClassOf (track):
            if track.GetLayer () == 0:   ## 
                layer = 'F.Cu'
            elif track.GetLayer () == 31:
                layer = 'B.Cu'

            pos = track.GetStart()
            start = [to_mm(pos.x-min_x), to_mm(pos.y-min_y) ]
            pos = track.GetEnd()
            end = [to_mm(pos.x-min_x), to_mm(pos.y-min_y) ]
            kicad_mod.append(Line(start=start, end=end, layer=layer, width=to_mm(track.GetWidth())) )

        if pcbnew.VIA_ClassOf (track):
            via = track
            pos = via.GetStart()
            pos_x = to_mm(pos.x - min_x)
            pos_y = to_mm(pos.y - min_y)

            #print "via at %d,%d" % (pos_x, pos_y)
            pad_type = Pad.TYPE_THT
            layers=['*.Cu']     # tented via
            pad_shape = Pad.SHAPE_CIRCLE
            kicad_mod.append(Pad(number="~",type=pad_type, shape=pad_shape, at=[pos_x, pos_y], size=[to_mm(via.GetWidth()), to_mm(via.GetWidth())], 
                    drill=to_mm(via.GetDrill()), layers=layers) )

# create courtyard
kicad_mod.append(RectLine(start=[to_mm(0),to_mm(0)], end=[to_mm(max_x-min_x),to_mm(max_y-min_y)], 
    layer='F.CrtYd', width=0.05, offset=0.2))

# create pads
pad_number = 1
for module in board.GetModules():
    # if connectormodule.GetReference ():
    # print "%s %s" % (module.GetReference(), module.GetValue() )
    for pad in module.Pads():
        pos = pad.GetPosition()
        # print "pad %s at %d,%d" % (pad.GetPadName(), to_mm(pos.x - min_x), to_mm(pos.y - min_y))

        pos_x = to_mm(pos.x - min_x)
        pos_y = to_mm(pos.y - min_y)

        if pad.GetAttribute() == 3:
            pad_type = Pad.TYPE_NPTH
            layers=['*.Cu', '*.Mask']
        elif pad.GetAttribute() == 1:
            pad_type = Pad.TYPE_SMT
            if pad.IsOnLayer(0):
                layers=['F.Cu', 'F.Mask', 'F.Paste']
            else:
                layers=['B.Cu', 'B.Mask', 'B.Paste']
        else: # 0?
            pad_type = Pad.TYPE_THT
            layers=['*.Cu', '*.Mask']

        if pad.GetShape() == pcbnew.PAD_SHAPE_CIRCLE:
            pad_shape = Pad.SHAPE_CIRCLE
        elif pad.GetShape() == pcbnew.PAD_SHAPE_RECT:
            pad_shape = Pad.SHAPE_RECT
        elif pad.GetShape() == pcbnew.PAD_SHAPE_OVAL:
            pad_shape = Pad.SHAPE_OVAL
        else:
            pad_shape = Pad.SHAPE_CIRCLE

        if module.GetReference() in connector_refs:
            if pad_type == Pad.TYPE_NPTH:
                kicad_mod.append(Pad(number="~",type=pad_type, shape=pad_shape, at=[pos_x, pos_y], size=[to_mm(pad.GetSize().x), to_mm(pad.GetSize().y)], 
                    drill=to_mm(pad.GetDrillSize().x), layers=layers, rotation=pad.GetOrientation()/10))
            else:
                kicad_mod.append(Pad(number=pad_number, type=pad_type, shape=pad_shape, at=[pos_x, pos_y], size=[to_mm(pad.GetSize().x), to_mm(pad.GetSize().y)], 
                    drill=to_mm(pad.GetDrillSize().x), layers=layers, rotation=pad.GetOrientation()/10))
                pad_number += 1
        elif copy_all:
            kicad_mod.append(Pad(number="~",type=pad_type, shape=pad_shape, at=[pos_x, pos_y], size=[to_mm(pad.GetSize().x), to_mm(pad.GetSize().y)], 
                drill=to_mm(pad.GetDrillSize().x), layers=layers, rotation=pad.GetOrientation()/10))

    if copy_all:
        item = module.Reference()
        layer = item.GetLayerName()
        pos = item.GetPosition()
        pos_mm = [to_mm(pos.x-min_x), to_mm(pos.y-min_y) ]
        kicad_mod.append(Text(type='user', text=item.GetText(), at=pos_mm, layer=layer, rotation=(module.GetOrientation()+item.GetOrientation())/10))

        item = module.Value()
        layer = item.GetLayerName()
        pos = item.GetPosition()
        pos_mm = [to_mm(pos.x-min_x), to_mm(pos.y-min_y) ]
        kicad_mod.append(Text(type='user', text=item.GetText(), at=pos_mm, layer=layer, rotation=(module.GetOrientation()+item.GetOrientation())/10))

        for item in module.GraphicalItems():
            if item.GetLayerName().endswith ("SilkS"):
                if pcbnew.EDGE_MODULE_ClassOf (item):
                    layer = item.GetLayerName()
                    if item.GetShape() == 0:
                        pos = item.GetStart()
                        start = [to_mm(pos.x-min_x), to_mm(pos.y-min_y) ]
                        pos = item.GetEnd()
                        end = [to_mm(pos.x-min_x), to_mm(pos.y-min_y) ]
                        kicad_mod.append(Line(start=start, end=end, layer=layer, width=to_mm(item.GetWidth())))
                    elif item.GetShape() == 2:
                        pos = item.GetArcStart()
                        start = [to_mm(pos.x-min_x), to_mm(pos.y-min_y) ]
                        pos = item.GetArcEnd()
                        end = [to_mm(pos.x-min_x), to_mm(pos.y-min_y) ]
                        pos = item.GetCenter()
                        center = [to_mm(pos.x-min_x), to_mm(pos.y-min_y) ]
                        kicad_mod.append(Arc(start=start, end=end, center=center, angle=item.GetAngle()/10, layer='F.SilkS', width=to_mm(item.GetWidth())))
                elif pcbnew.TEXTE_MODULE_ClassOf(item):
                    layer = item.GetLayerName()
                    pos = item.GetPosition()
                    pos_mm = [to_mm(pos.x-min_x), to_mm(pos.y-min_y) ]
                    kicad_mod.append(Text(type='user', text=item.GetText(), at=pos_mm, layer=layer))
#

if copy_all:
    for item in board.GetDrawings():
        if item.GetLayerName().endswith ("SilkS"):
            if pcbnew.DRAWSEGMENT_ClassOf(item):
                layer = item.GetLayerName()
                if item.GetShape() == 0:
                    pos = item.GetStart()
                    start = [to_mm(pos.x-min_x), to_mm(pos.y-min_y) ]
                    pos = item.GetEnd()
                    end = [to_mm(pos.x-min_x), to_mm(pos.y-min_y) ]
                    kicad_mod.append(Line(start=start, end=end, layer=layer, width=to_mm(item.GetWidth())))
            elif pcbnew.TEXTE_PCB_ClassOf(item):
                layer = item.GetLayerName()
                pos = item.GetPosition()
                pos_mm = [to_mm(pos.x-min_x), to_mm(pos.y-min_y) ]
                kicad_mod.append(Text(type='user', text=item.GetText(), at=pos_mm, layer=layer))

       
# add model
#kicad_mod.append(Model(filename="example.3dshapes/example_footprint.wrl",at=[0,0,0],scale=[1,1,1],rotate=[0,0,0]))
                         
# output kicad model
#print(kicad_mod)

# print render tree
#print(kicad_mod.getRenderTree())
#print(kicad_mod.getCompleteRenderTree())

# write file
file_handler = KicadFileHandler(kicad_mod)
print( "writing %s" % project_name + '.kicad_mod')
file_handler.writeFile(project_name + '.kicad_mod')
