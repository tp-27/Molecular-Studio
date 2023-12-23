import molecule
import math
import molsql

header = """<svg version="1.1" width="1000" height="1000" xmlns="http://www.w3.org/2000/svg">"""
footer = """</svg>"""
offsetx = 500
offsety = 500
radius = {}
element_name = {}
svgString = ""

#create an atom class
class Atom():
    def __init__(self, c_atom):
        self.atom = c_atom #store atom class/struct as member variable
        self.z = c_atom.z #initialize z to be value in wrapped class/struct

    def svg(self):
        xCenter = (self.atom.x * 100) + offsetx
        yCenter = (self.atom.y * 100) + offsety
        
        try:
            radiusAtom = radius[self.atom.element]
        except: 
            radiusAtom = 30 #default 

        try:
            colour = element_name[self.atom.element]
        except:
            colour = 'default' #default

        return '''  <circle cx="%.2f" cy="%.2f" r="%d" fill="url(#%s)"/>\n''' % (xCenter, yCenter, radiusAtom, colour)

    #debugging method
    def __str__(self):
        return '''Element: %s, x: %f, y: %f, z: %f''' % (self.atom.element, self.atom.x,  self.atom.y,  self.atom.z)


#create a bond class
class Bond():
    def __init__(self, c_bond):
        self.bond = c_bond
        self.z = c_bond.z

    def svg(self):

        c1_x = (self.bond.x1 * 100 + offsetx) + self.bond.dy * 10.0
        c1_y = (self.bond.y1 * 100 + offsety) - self.bond.dx * 10.0

        c2_x = (self.bond.x1 * 100 + offsetx) - self.bond.dy * 10.0
        c2_y = (self.bond.y1 * 100 + offsety) + self.bond.dx * 10.0

        c3_x = (self.bond.x2 * 100 + offsetx) - self.bond.dy * 10.0
        c3_y = (self.bond.y2 * 100 + offsety) + self.bond.dx * 10.0

        c4_x = (self.bond.x2 * 100 + offsetx) + self.bond.dy * 10.0
        c4_y = (self.bond.y2 * 100 + offsety) - self.bond.dx * 10.0


        return '''  <polygon points="%.2f,%.2f %.2f,%.2f %.2f,%.2f %.2f,%.2f" fill="green"/>\n''' % (c1_x, c1_y, c2_x, c2_y, c3_x, c3_y,
        c4_x, c4_y)
        
    def __str__(self):
        return '''a1: %d, a2: %d, epairs: %d, x1: %f ,x2: %f, y1: %f, y2: %f, 
        z: %f, len: %f, dx: %f, dy: %f''' % (self.bond.a1, self.bond.a2, self.bond.epairs, self.bond.x1, self.bond.x2,
        self.bond.y1, self.bond.y2, self.bond.z, self.bond.len, self.bond.dx, self.bond.dy)

#create a molecule class
class Molecule(molecule.molecule):
    unentered = []
    
    def __str__(self):
        #print atoms
        print(self.atom_no)
        for i in range(self.atom_no):
            theAtom = self.get_atom(i)
            print('''%s: x: %f, y: %f, z: %f ''' % (theAtom.element, theAtom.x, theAtom.y, theAtom.z))

        #print bonds
        for i in range(self.bond_no):
            theBond = self.get_bond(i)
            theAtom1 = self.get_atom(theBond.a1)
            theAtom2 = self.get_atom(theBond.a2)
            print('''Bond %d: %s + %s , Epairs: %d, z: %f, len: %f, dx: %f, dy: %f''' % (i, theAtom1.element, theAtom2.element, theBond.epairs,
            theBond.z, theBond.len, theBond.dx, theBond.dy))


    def svg(self):
        atoms = []
        bonds = []
        svgList = []

        atom_no = self.atom_no 
        bond_no = self.bond_no

        #create atoms and bonds stack - largest z value on top
        for i in range(atom_no): 
            atoms.append(self.get_atom(i))

        for i in range(bond_no):
            bonds.append(self.get_bond(i))

        #create one stack with atom and bond z values sorted
        i = 0
        j = 0
        while (i < atom_no and j < bond_no):
            if (atoms[i].z > bonds[j].z):
                svgList.append(bonds[j])
                j += 1
            
            else:
                svgList.append(atoms[i])
                i += 1

        while (i < atom_no):
            svgList.append(atoms[i])
            i += 1

        while (j < bond_no):
            svgList.append(bonds[j])
            j += 1

        #append values to svg string
        svgString = header #append headerx
        for i in range(atom_no + bond_no):
            object = svgList[i]
            if (type(object) == molecule.atom):
                theAtom = Atom(object)
                theSvg = theAtom.svg()

            else:
                theBond = Bond(object)
                theSvg = theBond.svg()

            svgString += theSvg

        svgString += footer
        return svgString
            
    def parse(self, fileObj): #takes in file object, supposing file is already opened when passed to func
        contents = fileObj.readlines()
        print(len(contents))
        molecule_info = contents[3] #skip first 4 lines
        molecule_info = molecule_info.split(' ') #split row with #atoms + #bonds
        molecule_info[:] = [item for item in molecule_info if item != '']
        atom_no = int(molecule_info[0])
        bond_no = int(molecule_info[1])
        elements = []

        # parse atoms
        for i in range(atom_no):
            atom_line = contents[i + 4].split(' ')
            atom_line[:] = [item for item in atom_line if item != '']
            
            x = float(atom_line[0])
            y = float(atom_line[1])
            z = float(atom_line[2])
            element = atom_line[3]    
            elements.append(element)
            self.append_atom(element, x, y, z)
        
        #parse bonds
        for i in range(bond_no):
            bond_line = contents[i + 4 + atom_no].split(' ')
            bond_line[:] = [item for item in bond_line if item != '']

            a1 = int(bond_line[0]) - 1 
            a2 = int(bond_line[1]) - 1
            epairs = int(bond_line[2])
            self.append_bond(a1, a2, epairs)





# if __name__ == "__main__":
#     db = Database(reset=True); 
#     db.create_tables();

#     db['Elements'] = ( 1, 'H', 'Hydrogen', 'FFFFFF', '050505', '020202', 25 );
#     db['Elements'] = ( 6, 'C', 'Carbon', '808080', '010101', '000000', 40 ); 
#     db['Elements'] = ( 7, 'N', 'Nitrogen', '0000FF', '000005', '000002', 40 ); 
#     db['Elements'] = ( 8, 'O', 'Oxygen', 'FF0000', '050000', '020000', 40 );

    # display tables
        # print( db.conn.execute( "SELECT * FROM Elements;" ).fetchall() ); 
        # print( db.conn.execute( "SELECT * FROM Molecules;" ).fetchall() ); 
        # print( db.conn.execute( "SELECT * FROM Atoms;" ).fetchall() ); 
        # print( db.conn.execute( "SELECT * FROM Bonds;" ).fetchall() ); 
        # print( db.conn.execute( "SELECT * FROM MoleculeAtom;" ).fetchall() ); 
        # print( db.conn.execute( "SELECT * FROM MoleculeBond;" ).fetchall() );
 