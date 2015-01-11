import warnings

import xlrd
import pandas as pd
import numpy as np

def read_taqman(path, sheet_name=None, sheet_index=0):
    wb = xlrd.open_workbook(path)
    if sheet_name is not None:
        sheet = wb.sheet_by_name(sheet_name)
    else:
        sheet = wb.sheet_by_index(sheet_index)

    rows = []
    ix = [4]
    index = []
    header = []

    for i in range(sheet.nrows):
        if i == 0:
            blank = False
            j = 0
            for j in range(5,sheet.ncols):
                cell = sheet.cell(i,j)
                if cell.ctype == xlrd.XL_CELL_EMPTY:
                    if blank:
                        break
                    blank = True
                else:
                    v = cell.value
                    if isinstance(v, float):
                        ix.append(j)
                    blank = False
            continue

        row = [sheet.cell(i,j).value for j in ix]
        if row[0] == "Detector":
            header = row
        else:
            if not any(row):
                break
            if row[0] in index:
                continue
            index.append(row[0])
            rows.append([x if isinstance(x,float)
                else np.nan
                for x in row[1:]])

    X = pd.DataFrame(rows, columns=header[1:], index=index)
    X.index.name = header[0]
    return X
