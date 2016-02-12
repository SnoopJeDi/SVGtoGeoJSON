#!/usr/bin/python

import sys
import json,copy,re
from xml.etree import ElementTree as ET
import numpy as np

xscale = 0.01
yscale = 0.01

geodata = { "type": "FeatureCollection", "features": [] }
featuretemplate = {
    "type": "Feature",
    "properties": { "tags": { "name": "default room name" },
        "relations": [ { "reltags": { "height": "4", "level": "0", "type": "level" } } ],
        "meta": {}
    },
    "geometry": {
        "type": "Polygon",
        "coordinates": []
    }
}

def transformPoint(pt):
    # Inkscape uses +y up coordinates internally
    # this doesn't invert the y-axis for now, but might at some point...
    return np.add(np.multiply(pt,[1*xscale,1*yscale]),[0,0]).tolist()

def main():
    ns="http://www.w3.org/2000/svg"
    if len(sys.argv) > 1 :
        try:
            xmltree = ET.parse(sys.argv[1])
        except IOError:
            print("Error, not a valid file")
            sys.exit(1)
        except:
            print("Unknown error")
            sys.exit(1)
    else:
        print("No SVG to parse specified!")
        print("Usage: python svgRectToGeoJSON.py file.svg")
        sys.exit(1)

    shapes = []
    shapes += xmltree.getroot().findall("./{%s}g/{%s}rect"%(ns,ns)) 
    shapes += xmltree.getroot().findall("./{%s}g/{%s}path"%(ns,ns)) 

    for s in shapes:
        shapeid = s.get('id')
        if ( s.tag == '{%s}rect'%ns ): 
            x = float(s.get('x'))
            y = float(s.get('y'))
            w = float(s.get('width'))
            h = float(s.get('height'))
            pts = [ [x,y],[x+w,y],[x+w,y+h],[x,y+h],[x,y] ]

            transforms = re.findall("[a-zA-Z]+\([^\)]+\)",s.get('transform') or '')
            # reverse order because SVG transforms apply right-to-left
            transforms.reverse()
            for t in transforms:
                if not t.startswith("matrix"):
                    # don't process anything but matrix for now
                    continue
                t = t.replace('matrix(','').replace(')','')
                mat = []
                mat = [ float(n) for n in re.split("[ ,]",t) ]

                m = np.vstack([np.resize(mat,(3,2)).transpose(), [0,0,1]])
                pts = [ np.dot(m,p+[1])[0:2] for p in pts ]

            pts = [ transformPoint(p) for p in pts ]
            geomObject(pts,name=shapeid)
        # TODO: paths

    print(json.dumps(geodata, indent=3))
         
def geomObject(pts,name="default room"):
    f = copy.deepcopy(featuretemplate)
    f['geometry']['coordinates'] = [ pts ]
    f['properties']['tags']['name'] = name

    geodata['features'].append(f)

if __name__ == "__main__":
    main()

