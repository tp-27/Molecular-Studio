#include "mol.h"

/***********************************************
           mol Library 
***********************************************/
void atomset(atom *atom, char element[3], double *x, double *y, double *z) {
    if (atom != NULL) {
        for (int i = 0; i < 3; i++) {
            if (i == 2) {
                atom->element[i] = '\0';
            } else {
                atom->element[i] = element[i];
            }
        }
        atom->x = *x;
        atom->y = *y;
        atom->z = *z;
    }
}

void atomget(atom *atom, char element[3], double *x, double *y, double *z) {
    if (atom != NULL) {
        strcpy(element, atom->element);
        *x = atom->x;
        *y = atom->y;
        *z = atom->z;
    }
}

void bondset(bond *bond, unsigned short *a1, unsigned short *a2, atom **atoms, unsigned char *epairs) {
    if (bond != NULL) {
        bond->a1 = *a1;
        bond->a2 = *a2;
        bond->atoms = *atoms;
        bond->epairs = *epairs;
        compute_coords(bond);
    }
}

void bondget(bond *bond, unsigned short *a1, unsigned short *a2, atom **atoms, unsigned char *epairs) {
    if (bond != NULL) {
        *a1 = bond->a1;
        *a2 = bond->a2;
        *atoms = bond->atoms; 
        *epairs = bond->epairs;
    }
}

void compute_coords(bond *bond) {
    // Assign first atom coordinates to bond
    bond->x1 = bond->atoms[bond->a1].x; 
    bond->y1 = bond->atoms[bond->a1].y; 

    // Assign second atom coordinates to bond
    bond->x2 = bond->atoms[bond->a2].x; 
    bond->y2 = bond->atoms[bond->a2].y; 

    // Compute length - distance from a1 to a2 - len = sqrt ((x2 - x1)^2 + (y2 - y1)^2 +(z2 - z1)^2) // NO - Z value
    bond->len = sqrt( ((bond->x2 - bond->x1) * (bond->x2 - bond->x1)) +
                      ((bond->y2 - bond->y1) * (bond->y2 - bond->y1)) );

    // Compute dx, dy - difference divided by length of bond
    bond->dx = (bond->x2 - bond->x1) / bond->len;
    bond->dy = (bond->y2 - bond->y1) / bond->len;

    // Compute z - avg z value of a1 and a2
    bond->z = (bond->atoms[bond->a1].z + bond->atoms[bond->a2].z) / 2;
}

molecule *molmalloc(unsigned short atom_max, unsigned short bond_max) {
    molecule *aMolecule;

    aMolecule = malloc(sizeof(molecule));
    if (aMolecule != NULL) {
        aMolecule->atom_max = atom_max;
        aMolecule->atom_no = 0;
        aMolecule->atoms = malloc(sizeof(struct atom) * atom_max);
        aMolecule->atom_ptrs = malloc(sizeof(struct atom *) * atom_max);

        aMolecule->bond_max = bond_max;
        aMolecule->bond_no = 0;
        aMolecule->bonds = malloc(sizeof(struct bond) * bond_max);
        aMolecule->bond_ptrs = malloc(sizeof(struct bond *) * bond_max);
    }
    return aMolecule;
}

molecule *molcopy(molecule *src) {

    if (src != NULL) {
        molecule *copySrc;

        copySrc = molmalloc(src->atom_max, src->bond_max);
        if (copySrc != NULL) {
            for (int i = 0; i < src->atom_no; i++) {
                molappend_atom(copySrc, &src->atoms[i]);
            }

            for (int i = 0; i < src->bond_no; i++) {
                molappend_bond(copySrc, &src->bonds[i]);
            }
        }
        return copySrc;
    } 
    return NULL;
}

void molfree(molecule *ptr) {
    free(ptr->atoms);
    free(ptr->atom_ptrs);
    free(ptr->bonds);
    free(ptr->bond_ptrs);
    free(ptr);
}

void molappend_atom(molecule *molecule, atom *atom) {
    if (molecule->atom_no == molecule->atom_max) {
        if (molecule->atom_max == 0) {
            molecule->atom_max += 1;
        } else {
            molecule->atom_max = (molecule->atom_max * 2);
        }

        // reallocate
        molecule->atoms = realloc(molecule->atoms, sizeof(struct atom) * molecule->atom_max);
        molecule->atom_ptrs = realloc(molecule->atom_ptrs, sizeof(struct atom*) * molecule->atom_max);
    }

    if ((molecule->atoms != NULL) && (molecule->atom_ptrs != NULL)) {
        // copy data
        atomset(molecule->atoms + molecule->atom_no, atom->element, &atom->x, &atom->y, &atom->z);
        molecule->atom_no += 1;

        // re-point all atom_ptrs to new block of memory for atoms
        for (int i = 0; i < molecule->atom_no; i++) {
            molecule->atom_ptrs[i] = molecule->atoms + i; // set first empty ptr in atom_ptrs to newly appended atom
        }
    }
}

void molappend_bond(molecule *molecule, bond *bond) {
    if (molecule->bond_no == molecule->bond_max) {
        if (molecule->bond_max == 0) {
            molecule->bond_max += 1;
        } else {
            molecule->bond_max = (molecule->bond_max * 2);
        }
        // realloc
        molecule->bonds = realloc(molecule->bonds, sizeof(struct bond) * molecule->bond_max);
        molecule->bond_ptrs = realloc(molecule->bond_ptrs, sizeof(struct bond*) * molecule->bond_max);
    }

    if ((molecule->bonds != NULL) && (molecule->bond_ptrs != NULL)) {
        // copy data
        unsigned short *a1 = &(bond->a1);
        unsigned short *a2 = &(bond->a2);
        unsigned char *epairs = &(bond->epairs);
        atom **atoms = &(bond->atoms);

        bondset(molecule->bonds + molecule->bond_no, a1, a2, atoms, epairs);
        molecule->bond_no += 1;
        
        // repoint all bond_ptrs to new bonds
        for (int i = 0; i < molecule->bond_no; i++) {
            molecule->bond_ptrs[i] = molecule->bonds + i; 
        }
    }
}

void molsort(molecule *molecule) {
    /** Argument Values
     *  1. pointer to first element of array to be sorted
     *  2. number of elements in array pointer by base
     *  3. size of bytes of each element in the array
     *  4. function that compares two elements
     **/
    if (molecule != NULL) {
        if (molecule->atom_ptrs != NULL) {
             qsort(molecule->atom_ptrs, molecule->atom_no, sizeof(struct atom**), atom_comp);
        }

        if (molecule->bond_ptrs != NULL) {
            qsort(molecule->bond_ptrs, molecule->bond_no, sizeof(struct bond**), bond_comp);
        }
    }
}

void xrotation(xform_matrix xform_matrix, unsigned short deg) {
    // https://en.wikipedia.org/wiki/Rotation_matrix
    double radian;

    radian = deg * (PI / 180.000);
    xform_matrix[0][0] = 1.00;
    xform_matrix[0][1] = 0.00;
    xform_matrix[0][2] = 0.00;

    xform_matrix[1][0] = 0.00;
    xform_matrix[1][1] = cos(radian);
    xform_matrix[1][2] = -sin(radian);

    xform_matrix[2][0] = 0.00;
    xform_matrix[2][1] = sin(radian);
    xform_matrix[2][2] = cos(radian);
}

void yrotation(xform_matrix xform_matrix, unsigned short deg) {
    double radian;

    radian = deg * (PI / 180.000);
    xform_matrix[0][0] = cos(radian);
    xform_matrix[0][1] = 0.00;
    xform_matrix[0][2] = sin(radian);

    xform_matrix[1][0] = 0.00;
    xform_matrix[1][1] = 1.00;
    xform_matrix[1][2] = 0.00;

    xform_matrix[2][0] = -sin(radian);
    xform_matrix[2][1] = 0.00;
    xform_matrix[2][2] = cos(radian);
}

void zrotation(xform_matrix xform_matrix, unsigned short deg) {
    double radian;

    radian = deg * (PI / 180.000);
    xform_matrix[0][0] = cos(radian);
    xform_matrix[0][1] = -sin(radian);
    xform_matrix[0][2] = 0.00;

    xform_matrix[1][0] = sin(radian);
    xform_matrix[1][1] = cos(radian);
    xform_matrix[1][2] = 0.00;

    xform_matrix[2][0] = 0.00;
    xform_matrix[2][1] = 0.00;
    xform_matrix[2][2] = 1.00;
}

void mol_xform(molecule *molecule, xform_matrix matrix) {
    if ((molecule != NULL) && (matrix != NULL)) {
        for (int i = 0; i < molecule->atom_no; i++) {
            double x, y, z;
            x = molecule->atoms[i].x;
            y = molecule->atoms[i].y;
            z = molecule->atoms[i].z;

            // perform matrix transformation
            molecule->atom_ptrs[i]->x = (matrix[0][0] * x) +
                                        (matrix[0][1] * y) +
                                        (matrix[0][2] * z);

            molecule->atom_ptrs[i]->y = (matrix[1][0] * x) +
                                        (matrix[1][1] * y) +
                                        (matrix[1][2] * z);

            molecule->atom_ptrs[i]->z = (matrix[2][0] * x) +
                                        (matrix[2][1] * y) +
                                        (matrix[2][2] * z);
        }

        // compute coordinates for each bond in molecule
        for (int i = 0; i < molecule->bond_no; i++) {
            bond *theBond = molecule->bond_ptrs[i];
            compute_coords(theBond);
        }
        
    }
}


/***********************************************
             Helper Functions
***********************************************/

int bond_comp(const void *a, const void *b) {
    bond *bondA, *bondB;

    // Convert to atom (from void*) and derefernce address
    bondA = *(struct bond**)a;
    bondB = *(struct bond**)b;

    // Compare
    if (bondA->z < bondB->z) { // A goes before B
        return -1;
    } else if (bondA->z > bondB->z) { // A goes after B
        return 1;
    } else {
        return 0;
    }
}

int atom_comp(const void* atomA_void, const void* atomB_void) {
    atom *atomA, *atomB;

    // Convert to atom (from void*) and derefernce address
    atomA = *(struct atom**)atomA_void;
    atomB = *(struct atom**)atomB_void;

    // Compare
    if (atomA->z < atomB->z) { // A goes before B
        return -1;
    } else if (atomA->z > atomB->z) { // A goes after B
        return 1;
    } else {
        return 0;
    }
}
