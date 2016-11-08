#This file contains just enough logic to get data from the
#sketchnet svg files as points-on-paths

#info
#http://www.johndcook.com/blog/2009/12/21/bezier-basics/
#https://www.w3.org/TR/SVG/paths.html

#USAGE:
## If filename is one of the SVG files from sketchnet and you run
#   data = readSketchnet.read(filename)
##then data2 will be a list of numpy arrays giving strokes
##of the character.

import xml.etree.ElementTree as ET
import numpy as np
import re

ns = {"i":"http://www.w3.org/2000/svg"}

#parses a file to produce a big list of all the path data
def fileToData(filename):
    num=r"(\d+(\.\d+)?)"
    straight="M{0} {0} L{0} {0} ".format(num)
    curve = "M{0} {0} (C{0} {0} {0} {0} {0} {0} )+".format(num)
    curvepiece = "C{0} {0} {0} {0} {0} {0} ".format(num)

    r = ET.parse(filename)
    g = r.find("i:g",ns).find("i:g",ns)
    svgTexts=[p.attrib["d"] for p in g.findall("i:path",ns)]

    out = []
    for text in svgTexts:
        m=re.match(straight, text)
        if m:
            g = m.groups()
            points = ((float(g[0]),float(g[2])),(float(g[4]),float(g[6])))
            out.append(points)
        else:
            m=re.match(curve, text)
            if(m):
                g = m.groups()
                startpt = (float(g[0]),float(g[2]))
                curvedata = []
                for p in re.finditer(curvepiece, text):
                    g= p.groups()
                    vals = ((float(g[0]),float(g[2])),
                            (float(g[4]),float(g[6])),
                            (float(g[8]),float(g[10])))
                    curvedata.append(vals)
                #print (text,"\n", startpt,curvedata)
                out.append(("C",startpt,curvedata)) #C just for convenience
            else:
                raise RuntimeError("Unexpected path string: "+text)
    return out


def prepareCoeffs():
    t=np.arange(0.1,1,0.1)
    ot = 1-t
    out = np.vstack([ot*ot*ot,3*ot*ot*t,3*ot*t*t,t*t*t])
    return out.T
coeffs = prepareCoeffs() #9x4

#takes the data from a file and returns a list of strokes,
#each one being an Nx2 numpy array.
#This means expanding the bezier curves
def dataToStrokePoints(data):
    out = []
    for stroke in data:
        if len(stroke)==2: #straight line
            x = np.array(stroke)
        else:
            x=[stroke[1]]
            for i in stroke[2]:
                if False: # show all control points
                    for pt in range(3):
                        x.append(i[pt])
                else:
                    controlPts=np.vstack([x[-1],i[0],i[1],i[2]]) # 4x2
                    x.append(np.dot(coeffs,controlPts)) #9x2
                    x.append(i[2])
        out.append(np.vstack(x))
    return out

def read(filename):
    return dataToStrokePoints(fileToData(filename))
