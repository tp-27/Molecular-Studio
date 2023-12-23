import os
import sqlite3
import molecule
import MolDisplay

class Database():
    def __init__(self, reset=False):
        if (reset):
            if os.path.exists('molecules.db'):
                os.remove('molecules.db') 
        
        #create db connection
        self.conn = sqlite3.connect('molecules.db')

    def create_tables(self):
        #create tables - if tables already exist, leave them alone don't re-create
        self.conn.execute( """CREATE TABLE IF NOT EXISTS Elements (
                                ELEMENT_NO      INTEGER NOT NULL,
                                ELEMENT_CODE    VARCHAR(3) NOT NULL,
                                ELEMENT_NAME    VARCHAR(32) NOT NULL,
                                COLOUR1         CHAR(6) NOT NULL,
                                COLOUR2         CHAR(6) NOT NULL,
                                COLOUR3         CHAR(6) NOT NULL,
                                RADIUS          DECIMAL(3) NOT NULL,
                                PRIMARY KEY (ELEMENT_CODE) );""")

        self.conn.execute( """CREATE TABLE IF NOT EXISTS Atoms (
                                ATOM_ID         INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                                ELEMENT_CODE    VARCHAR(3) NOT NULL,
                                X               DECIMAL(7,4) NOT NULL,
                                Y               DECIMAL(7,4) NOT NULL,
                                Z               DECIMAL(7,4) NOT NULL,
                                FOREIGN KEY (ELEMENT_CODE) REFERENCES Elements );""")

        self.conn.execute( """CREATE TABLE IF NOT EXISTS Bonds (
                                BOND_ID         INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                                A1              INTEGER NOT NULL,
                                A2              INTEGER NOT NULL,
                                EPAIRS          INTEGER NOT NULL);""")
                        

        self.conn.execute( """CREATE TABLE IF NOT EXISTS Molecules (
                                MOLECULE_ID     INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                                NAME            TEXT UNIQUE NOT NULL);""")


        self.conn.execute( """CREATE TABLE IF NOT EXISTS MoleculeAtom (
                                MOLECULE_ID     INTEGER NOT NULL,
                                ATOM_ID         INTEGER NOT NULL,
                                PRIMARY KEY (MOLECULE_ID, ATOM_ID),
                                FOREIGN KEY (MOLECULE_ID) REFERENCES Molecules,
                                FOREIGN KEY (ATOM_ID) REFERENCES Atoms );""")

        self.conn.execute( """CREATE TABLE IF NOT EXISTS MoleculeBond (
                                MOLECULE_ID     INTEGER NOT NULL,
                                BOND_ID         INTEGER NOT NULL,
                                PRIMARY KEY (MOLECULE_ID, BOND_ID),
                                FOREIGN KEY (MOLECULE_ID) REFERENCES Molecules,
                                FOREIGN KEY (BOND_ID) REFERENCES Bonds );""")


    def __setitem__(self, table, values):
        valid = ( "Elements" , "Atoms" , "Bonds" , "Molecules" , "MoleculeAtom" , "MoleculeBond" )

        if (table in valid):
            if table == "Elements":
                sql = """INSERT INTO {} VALUES (?, ?, ?, ?, ?, ?, ?);""".format(table)
                self.conn.execute(sql, values)
            
            elif table == "Atoms":
                sql = """INSERT INTO {} VALUES (?, ?, ?, ?, ?);""".format(table)
                self.conn.execute(sql, values)

            elif table == "Bonds":
                sql = """INSERT INTO {} VALUES (?, ?, ?, ?);""".format(table)
                self.conn.execute(sql, values)
        
            elif table == "Molecules":
                sql = """INSERT INTO {} VALUES (?, ?);""".format(table)
                self.conn.execute(sql, values)

            elif table == "MoleculeAtom":
                sql = """INSERT INTO {} VALUES (?, ?);""".format(table)
                self.conn.execute(sql, values)

            elif table == "MoleculeBond":
                sql = """INSERT INTO {} VALUES (?, ?);""".format(table)
                self.conn.execute(sql, values)
            
            self.conn.commit()

    def add_atom(self, molname, atom):
        #add atom attributes to Atoms
        sql = """INSERT INTO Atoms (ELEMENT_CODE, X, Y, Z, ELEMENT_CODE)
                                VALUES (?, ?, ?, ?, ?);"""
        
        self.conn.execute(sql, (atom.element, atom.x, atom.y, atom.z, atom.element))
        self.conn.commit()

        #add entry to MoleculeAtom table 
        #get MOLECULE_ID
        sql = "SELECT * FROM Molecules;"
        rows = self.conn.execute(sql).fetchall()
        for id in rows:
            if id[1] == molname:
                mol_id = id[0]
                
        #get ATOM_ID (last row added)
        sql = "SELECT * FROM Atoms ORDER BY ATOM_ID DESC LIMIT 1;"
        row = self.conn.execute(sql).fetchone()
        atom_id = row[0]

        sql = """INSERT INTO MoleculeAtom (MOLECULE_ID, ATOM_ID)
                        VALUES (?, ?);"""
        
        self.conn.execute(sql,(mol_id, atom_id))
        self.conn.commit()
   
   
    def add_bond(self, molname, bond):
        #add bond attributes to Bonds
        sql = """INSERT INTO Bonds (A1, A2, EPAIRS)
                                VALUES (?, ?, ?);"""

        self.conn.execute(sql, (bond.a1, bond.a2, bond.epairs))
        self.conn.commit()

        #add entry to MoleculeBond table
        sql = "SELECT * FROM Molecules;"
        rows = self.conn.execute(sql).fetchall()
        for id in rows:
            if id[1] == molname:
                mol_id = id[0]
        
        #get BOND_ID (last row added)
        sql = "SELECT * FROM Bonds ORDER BY BOND_ID DESC LIMIT 1;"
        row = self.conn.execute(sql).fetchone()
        bond_id = row[0]

        sql = """INSERT INTO MoleculeBond (MOLECULE_ID, BOND_ID)
                        VALUES (?, ?);"""
        
        self.conn.execute(sql,(mol_id, bond_id))
        self.conn.commit()


    #SDF -> Molecule Obj -> Db
    def add_molecule(self, name, fp):
        molDisp = MolDisplay.Molecule()
        molDisp.parse(fp)

        #add entry to Molecules table
        sql = """INSERT OR REPLACE INTO Molecules (NAME)
                                VALUES (?);"""
                            
        self.conn.execute(sql, (name,)) # ',' without comma, name is a grouped expressed not a tuple 
        self.conn.commit()
 
        #add atoms and bonds 
        numAtoms = 0
        for i in range(molDisp.atom_no):
            atom = molDisp.get_atom(i)
            self.add_atom(name, atom)
            numAtoms += 1
        
        numBonds = 0
        for i in range(molDisp.bond_no):
            bond = molDisp.get_bond(i)
            self.add_bond(name, bond)
            numBonds += 1
        
    #Db -> Molecule Obj -> return
    def load_mol(self, name):
        #create MolDisplay.Molecule object
        mol = MolDisplay.Molecule()
        
        #retrieve all atoms in db assoc. with molecule, append to Molecule obj in INCREASING ATOM_ID  
        sql = """SELECT Atoms.ATOM_ID, Atoms.ELEMENT_CODE, Atoms.X, Atoms.Y, Atoms.Z, Molecules.NAME
                    FROM MoleculeAtom
                    JOIN Molecules ON MoleculeAtom.MOLECULE_ID = Molecules.MOLECULE_ID
                    JOIN Atoms ON MoleculeAtom.ATOM_ID = Atoms.ATOM_ID WHERE Molecules.NAME = ?;"""
  
        results = self.conn.execute(sql, (name,)).fetchall()
        for atom in results:
            mol.append_atom(atom[1], atom[2], atom[3], atom[4])

        #retrieve all bonds in db assoc. with molecule, append to Molecule obj in INCREASING BOND_ID 
        sql = """SELECT Bonds.BOND_ID, Bonds.A1, Bonds.A2, Bonds.EPAIRS, Molecules.NAME
            FROM MoleculeBond
            JOIN Molecules ON MoleculeBond.MOLECULE_ID = Molecules.MOLECULE_ID
            JOIN Bonds ON MoleculeBond.BOND_ID = Bonds.BOND_ID WHERE Molecules.NAME = ?;"""

        results = self.conn.execute(sql, (name,)).fetchall()
        for bond in results:
            mol.append_bond(bond[1], bond[2], bond[3])

        return mol
        
    def radius(self):
        sql = "SELECT ELEMENT_CODE, RADIUS FROM Elements;"
        code_rad = {}

        results = self.conn.execute(sql).fetchall()

        for mapping in results:
            code_rad[mapping[0]] = mapping[1]
        
        return code_rad


    def element_name(self):
        sql = "SELECT ELEMENT_CODE, ELEMENT_NAME FROM Elements;"
        code_name = {}

        results = self.conn.execute(sql).fetchall()

        for mapping in results:
            code_name[mapping[0]] = mapping[1]

        return code_name

    def radial_gradients(self):
        sql = "SELECT ELEMENT_NAME, COLOUR1, COLOUR2, COLOUR3 FROM Elements;"
        results = self.conn.execute(sql).fetchall()

        radialGradientSVG = ""
        for gradients in results:
            radialGradientSVG += """
            <radialGradient id="%s" cx="-50%%" cy="-50%%" r="220%%" fx="20%%" fy="20%%">
            <stop offset="0%%" stop-color="#%s"/> <stop offset="50%%" stop-color="#%s"/> <stop offset="100%%" stop-color="#%s"/>
            </radialGradient>""" % (gradients[0], gradients[1], gradients[2], gradients[3])
        
    
        return radialGradientSVG

if __name__ == "__main__":
    db = Database(reset=True); # or use default
    db.create_tables()
    # MolDisplay.radius = db.radius(); 
    # MolDisplay.element_name = db.element_name(); 
    # MolDisplay.header += db.radial_gradients();
    # for molecule in [ 'Water', 'Caffeine', 'Isopentanol' ]: 
    #     mol = db.load_mol( molecule );
    #     mol.sort();
    #     fp = open( molecule + ".svg", "w" );
    #     fp.write( mol.svg() ); fp.close();
    # db = Database(reset=True); db.create_tables();

    fp = open( 'water-3D-structure-CT1000292221.sdf' ); 
    db.add_molecule( 'Water', fp );
    fp = open( 'caffeine.sdf' ); 
    db.add_molecule( 'Caffeine', fp );
    fp = open( 'CID_31260.sdf' ); 
    db.add_molecule( 'Isopentanol', fp );

    # # display tables
    # print( db.conn.execute( "SELECT * FROM Elements;" ).fetchall() ); 
    # print( db.conn.execute( "SELECT * FROM Molecules;" ).fetchall() ); 
    # print( db.conn.execute( "SELECT * FROM Atoms;" ).fetchall() ); 
    # print( db.conn.execute( "SELECT * FROM Bonds;" ).fetchall() ); 
    # print( db.conn.execute( "SELECT * FROM MoleculeAtom;" ).fetchall() ); 
    # print( db.conn.execute( "SELECT * FROM MoleculeBond;" ).fetchall() );