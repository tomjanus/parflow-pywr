import numpy as np

def read_chunk(filename):
	print(filename)

	f = open(filename, "rb")

	# Read first 9 elements from the file
	a = np.fromfile(f, dtype='>i4', count = 9)

	# Number of elements in a grid
	nx = a[6]
	ny = a[7]
	nz = a[8]

	# Number of data points
	nn  = nx * ny * nz

	# Create a list
	data = [nn]
	
	# Read x, y, and z spacings for the computational grid
	d = np.fromfile(f, dtype='>f8', count = 3)
	dx = d[0]
	dy = d[1]
	dz = d[2]
	
	# Number of subgrids in the grid
	a = np.fromfile(f, dtype='>i4', count = 1)
	nsubgrid = a[0]
	
	ostride = 0
	
	for i in range(0, nsubgrid):
		a = np.fromfile(f, dtype='>i4', count = 9)
		ix = a[0]
		iy = a[1]
		iz = a[2]
	
		inx = a[3]
		iny = a[4]
		inz = a[5]
                
		inn = inx * iny * inz

		stride = ostride + inx * iny * inz
		data[ostride:stride] = np.fromfile(f,dtype='>f8',count = inn)
		ostride = stride
	
	return data;

def read(filename):
        print(filename)

        f = open(filename, "rb")

	# Read first 9 elements from the file
        a = np.fromfile(f, dtype='>i4', count = 9)

        nx = a[6]
        ny = a[7]
        nz = a[8]

	# Number of data points
        nn  = nx * ny * nz

	# Read x, y, and z spacings for the computational grid
        d = np.fromfile(f, dtype='>f8', count = 3)
        dx = d[0]
        dy = d[1]
        dz = d[2]

	# Number of subgrids in the grid
        a = np.fromfile(f, dtype='>i4', count = 1)
        nsubgrid = a[0]

        ostride = 0

	# Initialise data as numpy array of size nz,ny,nx
        data = np.ndarray(shape=(nz, ny, nx), dtype='>f8')
        data.dtype = data.dtype.newbyteorder("=")

        for s in range(0, nsubgrid):

                meta_inf = np.fromfile(f, dtype=">i4", count=9)
                ix = meta_inf[0]
                iy = meta_inf[1]
                iz = meta_inf[2]
                # print("---{0} Start Index (X,Y,Z):".format(s+1), ix, iy, iz)

                nx = meta_inf[3]
                ny = meta_inf[4]
                nz = meta_inf[5]
                nn = nx * ny * nz
                # print("---{0} Dimensions (X,Y,Z):".format(s+1), nx, ny, nz)

                rx = meta_inf[6]
                ry = meta_inf[7]
                rz = meta_inf[8]

                #for k in range(iz,iz+inz):
                #        for j in range(iy,iy+iny):
                #                for i in range(ix,ix+inx):
                #                        data[i,j,k] = np.fromfile(f,dtype='>f8',count = 1)
                data[iz : iz + nz, iy : iy + ny, ix : ix + nx] = np.fromfile(f, dtype='>f8', count=nn).reshape((nz, ny, nx))


        return data;
