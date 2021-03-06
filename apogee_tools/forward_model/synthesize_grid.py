import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import apogee_tools as ap

#Get the path of apogee_tools file
FULL_PATH  = os.path.realpath(__file__)
BASE = os.path.split(os.path.split(os.path.split(FULL_PATH)[0])[0])[0]
AP_PATH = os.environ['APOGEE_DATA']


def interpolateGrid(**kwargs):

	"""
	Interpolate model grids, using polynomial coefficients obtained from training The Cannon on theoretical grids (right now only PHOENIX).
	Input list of labels, dot product with Cannon model coefficients, return set of fluxes.
	@Jessica Birky

	Input  : 'labels' : [teff, logg, fe_h]

	Output : 'interp_sp' : spectrum object of interpolated spectrum
	"""

	method = kwargs.get('interp', 'splat')
	labels = kwargs.get('labels')

	if method == 'cannon':

		resolution = kwargs.get('res', '23k') #23k or 50k
		grid       = kwargs.get('grid', 'phoenix').lower()

		#stack list into matrix
		labels  = np.array([labels])
		nlabels = labels.shape[1]

		pivots = np.load(BASE+'/libraries/%s/cannon_%s/%s_pivots.npy'%(grid.upper(), grid, resolution))
		scales = np.load(BASE+'/libraries/%s/cannon_%s/%s_scales.npy'%(grid.upper(), grid, resolution))
		coeffs = np.load(BASE+'/libraries/%s/cannon_%s/%s_coeffs.npy'%(grid.upper(), grid, resolution))
		wave   = np.load(BASE+'/libraries/%s/cannon_%s/%s_wl.npy'%(grid.upper(), grid, resolution))

		scaled_labels = [(lbl - pivots) / scales for lbl in labels]

		label_vecs = [list(_get_lvec(lbl)) for lbl in scaled_labels]
		label_vecs = np.column_stack(([1 for l in label_vecs], label_vecs))

		iflux = np.array(np.dot(coeffs, np.transpose(label_vecs)))
		iflux = np.transpose(iflux)[0]

		interp_sp  = ap.Spectrum(wave=wave, flux=iflux, params=labels)

	elif method == 'splat':

		interp_sp = ap.loadModel(teff=labels[0], logg=labels[1], z=labels[2])
		interp_sp.wave = 10**4*interp_sp.wave

	else:
		print(method, "is not valid. Choose 'splat' or 'cannon' options.")
	
	return interp_sp


def _get_lvec(labels):

    """
    Constructs a label vector for an arbitrary number of labels
    Assumes that our model is quadratic in the labels
    @Anna Ho

    Parameters
    ----------
    labels: numpy ndarray
        pivoted label values for one star

    Returns
    -------
    lvec: numpy ndarray
        label vector
    """

    nlabels = len(labels)

    # specialized to second-order model
    linear_terms = labels 
    quadratic_terms = np.outer(linear_terms, linear_terms)[np.triu_indices(nlabels)]
    lvec = np.hstack((linear_terms, quadratic_terms))

    return lvec