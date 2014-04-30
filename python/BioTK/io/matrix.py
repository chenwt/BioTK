def read_matrix(path_or_handle):
    X = pd.read_csv(sys.stdin, sep="\t", index_col=0)
    X.drop([c for c in X.columns 
        if X[c].dtype==np.dtype('O') or c.startswith("Unnamed")], 
        axis=1, inplace=True)
    X.dropna(axis=0, thresh=int(X.shape[1] * 0.1), inplace=True)
    X.dropna(axis=1, thresh=int(X.shape[0] * 0.1), inplace=True)
