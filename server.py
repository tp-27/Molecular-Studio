import sys
import MolDisplay
import molecule
import molsql
import io
import json
import urllib
import cgi
from http.server import HTTPServer, BaseHTTPRequestHandler

pages = ["/index.html", "/upload.html", "/edit.html", "/select.html", "/display.html"]
styles = ["/style.css", "/upload.css", "/edit.css", "/select.css", "/display.css"]

class MyHandler( BaseHTTPRequestHandler ):
    db = molsql.Database(reset=True)
    db.create_tables()
    # db['Elements'] = ( 1, 'H', 'Hydrogen', 'FFFFFF', '050505', '020202', 25 );
    # db['Elements'] = ( 6, 'C', 'Carbon', '808080', '010101', '000000', 40 ); 
    # db['Elements'] = ( 7, 'N', 'Nitrogen', '0000FF', '000005', '000002', 40 ); 
    # db['Elements'] = ( 8, 'O', 'Oxygen', 'FF0000', '050000', '020000', 40 );

    def do_GET(self):
        if self.path == "/":
            self.response_headers("text/html")
            self.end_headers()
            content = open("./html/index.html", "r").read()
            self.wfile.write(bytes( content, "UTF-8" ))

        elif self.path in pages:
            self.response_headers("text/html")
            self.end_headers()
            content = Resources().getHTML(self.path)
            self.wfile.write(bytes( content, "UTF-8" ))

        elif self.path in styles:
            self.response_headers("text/css")
            self.end_headers()
            content = Resources().getCSS(self.path)
            self.wfile.write(bytes( content, "UTF-8" ))
      

        elif self.path == "/index.js":
            self.response_headers("text/javascript")
            self.end_headers()
            content = Resources().getJS(self.path)
            self.wfile.write(bytes( content, "UTF-8" ))

        elif self.path == "/display-mol": 
          content_length = int(self.headers['content-length'])
          postdata = self.rfile.read(content_length).decode("UTF-8")
          data = urllib.parse.parse_qs(postdata) #returns selected molecule

          print(data["molecule"][0].split(" ")[0])
          mol = data["molecule"][0].split(" ")[0]

          # MolDisplay.radius = self.db.radius()
          # MolDisplay.element_name = self.db.element_name()
          # MolDisplay.header += self.db.radial_gradients()
          # mol = self.db.load_mol( postdata )
          # mol.sort()
          # svg_file = mol.svg()   

          svg_file = "Hello"
          self.response_headers("text/plain")
          self.send_header("Content-length", len(svg_file))
          self.end_headers()
          self.wfile.write( bytes( svg_file, "UTF-8") )

        elif self.path == "/molecules":
            molecules = self.db.conn.execute("SELECT NAME FROM Molecules;").fetchall() #sends back a tuple, must send as string
            molDict = []
            for mol in molecules:
              temp = {}
              name = mol[0]
              theMol = self.db.load_mol(name)
              atoms = theMol.atom_no
              bonds = theMol.bond_no

              temp["name"] = name
              temp["atoms"] = atoms
              temp["bonds"] = bonds
              molDict.append(temp)
            
            molJson = json.dumps(molDict)
            self.response_headers("text/html")
            self.end_headers()
            self.wfile.write( bytes( molJson, "UTF-8") )

        elif self.path == "/elements":
            elements = self.db.conn.execute("SELECT * FROM Elements").fetchall()
            elementDict = []
            for element in elements:
              num = element[0]
              code = element[1]
              name = element[2]
              col1 = element[3]
              col2 = element[4]
              col3 = element[5]
              radius = element[6]

              temp = {}
              temp["number"] = num
              temp["code"] = code
              temp["name"] = name
              temp["col1"] = col1
              temp["col2"] = col2
              temp["col3"] = col3
              temp["radius"] = radius
              elementDict.append(temp)
            
            molJson = json.dumps(elementDict)
              

            self.response_headers("text/html")
            self.end_headers()
            self.wfile.write( bytes( molJson, "UTF-8") )


        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write( bytes("404: not found", "UTF-8"))

    def do_POST(self):
      if self.path == "/upload.html":
        content_length = int(self.headers['content-length'])
        postdata = self.rfile.read(content_length).decode("UTF-8")
        data = urllib.parse.parse_qs(postdata)
        message = ""
        

        try:
          molname = data["molecule"][0]
          sdf = data["sdf"][0]
          bytesIO = io.BytesIO(bytes(sdf, "UTF-8"))
          textIO = io.TextIOWrapper(bytesIO)
          self.db.add_molecule(molname, textIO) 
          message = "Successfully uploaded SDF file"
        
        except:
          message = "Invalid file contents. Please upload a valid file"
      
        self.response_headers("text/plain")
        self.send_header("Content-length", len(message))
        self.end_headers()
        self.wfile.write( bytes( message, "UTF-8") )
    
  
      elif self.path == "/add-element":
        content_length = int(self.headers['content-length'])
        postdata = self.rfile.read(content_length).decode("UTF-8")
        data = urllib.parse.parse_qs(postdata) #returns dictonary of values

        duplicate = 0
        elements =  self.db.conn.execute( "SELECT ELEMENT_CODE FROM Elements;" ).fetchall()
        for element in elements:
          print(element[0])
          print(data['code'][0])
          if element[0] == data['code'][0]:
            duplicate = 1
            break

        if duplicate != 1:
          self.db['Elements'] = (data['number'][0], data['code'][0], data['name'][0], data['colour1'][0], data['colour2'][0], data['colour3'][0], data['radius'][0]) # (number, code, name, col1, col2, col3, radius)
          msg = ""

        else:
          msg = "An element with the same element code already exists. Please delete it before adding another entry."

        self.response_headers("text/plain")
        self.send_header("Content-length", len(msg))
        self.end_headers()
        self.wfile.write( bytes( msg, "UTF-8") )

      elif self.path == "/delete-element":
        content_length = int(self.headers['content-length'])
        postdata = self.rfile.read(content_length).decode("UTF-8")
        data = urllib.parse.parse_qs(postdata) #returns element code

        sql = "DELETE FROM Elements WHERE ELEMENT_CODE = (?);"
        self.db.conn.execute(sql, (data['element'][0],))
        self.db.conn.commit()   
        print(self.db.conn.execute( "SELECT * FROM Elements;").fetchall())

        msg = "Data Received"
        self.response_headers("text/plain")
        self.send_header("Content-length", len(msg))
        self.end_headers()
        self.wfile.write( bytes( msg, "UTF-8") )

      elif self.path == "/selected-mol":
        content_length = int(self.headers['content-length'])
        postdata = self.rfile.read(content_length).decode("UTF-8")
        data = urllib.parse.parse_qs(postdata) #returns selected molecule

        print(data["molecule"][0].split(" ")[0])
        molname = data["molecule"][0].split(" ")[0]

        MolDisplay.radius = self.db.radius()
        MolDisplay.element_name = self.db.element_name()
        MolDisplay.header += self.db.radial_gradients()
        
        MolDisplay.header +=  """
            <radialGradient id="default" cx="-50%" cy="-50%" r="220%" fx="20%" fy="20%">
            <stop offset="0%" stop-color="#FFABCD"/> <stop offset="50%" stop-color="#000005"/> <stop offset="100%%" stop-color="#020000"/>
            </radialGradient>"""
        #finds all of the elements that don't have an entry into the Elements table
          # results = self.db.conn.execute( "SELECT ELEMENT_CODE FROM Elements;" ).fetchall() 
          # notFound = []
          # allElements = []

          # for result in results:
          #     allElements.append(result[0])

          # print("All elements:")
          # print(allElements)

          # for element in elements:
          #     if element not in allElements:
          #         notFound.append(element)

          # print("Not found: ")
          # print(notFound)
        #finds all of the elements that don't have an entry into the Elements table

        mol = self.db.load_mol( molname )
        print(mol.unentered)
        mol.sort()
        svg_file = mol.svg()   
        print(svg_file)
      
        msg = "Data Received"
        self.response_headers("text/plain")
        self.send_header("Content-length", len(svg_file))
        self.end_headers()
        self.wfile.write( bytes( svg_file, "UTF-8") )

      elif self.path == "/change-angle":
        content_length = int(self.headers['content-length'])
        postdata = self.rfile.read(content_length).decode("UTF-8")
        data = urllib.parse.parse_qs(postdata) #returns degree + axis
        deg = int(data['degrees'][0])
        axis = data['axis'][0]
        molname = data["molecule"][0].split(" ")[0]

        molDisp = MolDisplay.Molecule()
        molDisp = self.db.load_mol( molname )
        if axis == "x":
           mx = molecule.mx_wrapper(deg, 0, 0)

        elif axis == "y":
           mx = molecule.mx_wrapper(0, deg, 0)

        elif axis == "z":
           mx = molecule.mx_wrapper(0, 0, deg)

        molDisp.xform(mx.xform_matrix)
        rotated = molDisp.svg()

        self.response_headers("text/plain")
        self.send_header("Content-length", len(rotated))
        self.end_headers()
        self.wfile.write( bytes( rotated, "UTF-8") )

      else:
        self.send_response(404)
        self.end_headers()
        self.wfile.write(bytes("404: not found", "UTF-8"))

    def response_headers(self, content):
      self.send_response( 200 ) # OK
      self.send_header( "Content-type", content)


class Resources ():
    def getHTML(self, name):
      url = "./html" + name
      f = open(url, "r")
      contents = f.read()
      f.close()
      return contents

    def getCSS(self, name):
      url = "./css" + name
      f = open(url, "r")
      contents = f.read()
      f.close()
      return contents

    def getJS(self, name):
      url = "." + name
      f = open(url, "r")
      contents = f.read()
      f.close()
      return contents

httpd = HTTPServer(('localhost', int(sys.argv[1])), MyHandler) #use port 57980
httpd.serve_forever()
