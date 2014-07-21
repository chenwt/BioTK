import uuid

import numpy as np
import nvd3

from . import *

nvd3_attrs = ["height", "width", "x_axis_label", "y_axis_label",
        "margin_bottom", "margin_left", "margin_right", "margin_top",
        "color_category", "resize"
        ]

def jsify(obj):
    if obj is True:
        return "true"
    elif obj is False:
        return "false"
    else:
        return str(obj)

def as_scalar(obj):
    return obj if isinstance(obj, str) else np.asscalar(obj)

class Plot(Element):
    def __init__(self, data, **kwargs):
        self.extras = {}

        kwargs.setdefault("margin_left", 100)
        kwargs.setdefault("margin_bottom", 100)
        kwargs.setdefault("resize", True)
        #kwargs.setdefault("color_category", "category20c")
        #kwargs.setdefault("margin_top", 100)

        nvd3_kwargs = dict((k,v) for k,v in kwargs.items()
                if k in nvd3_attrs)
        nvd3_kwargs["name"] = "chart-" + str(uuid.uuid4()).replace("-","")
        chart_class = getattr(nvd3, self.PLOT_TYPE + "Chart")
        self.chart = chart_class(**nvd3_kwargs)
        
        self.data = data

        kwargs = dict((k,v) for k,v in kwargs.items()
                if not k in nvd3_attrs)
        if hasattr(self.data, "name"):
            kwargs.setdefault("title", self.data.name)

        self.extra("yAxis.axisLabelDistance", 20)

        super(Plot, self).__init__(**kwargs)

    def _render(self):
        if self.extras:
            self.chart.add_chart_extras("\n".join(self.extras.values()))
        self.chart.buildcontent()
        return self.chart.htmlcontent

    def extra(self, fn, *args):
        code = "chart.%s(%s);" % (fn, ", ".join(list(map(jsify, args))))
        self.extras[fn] = code

class ScatterPlot(Plot):
    PLOT_TYPE = "scatter"

    def __init__(self, data, *args, **kwargs):
        # Format: 3-column DataFrame. 
        # - Column 1: Category
        # - Column 2: x value
        # - Column 3: y value

        kwargs.setdefault("x_axis_label", data.columns[1])
        kwargs.setdefault("y_axis_label", data.columns[2])
        super(ScatterPlot, self).__init__(data, *args, **kwargs)

        data = self.data.drop_duplicates(cols=data.columns[1:])
        for key in set(data.iloc[:,0]):
            df = data.loc[data.iloc[:,0] == key,:]
            x = df.iloc[:,1].tolist()
            y = df.iloc[:,2].tolist()
            kwargs1 = {'shape': 'circle', 'size': '1'}
            self.chart.add_serie(name=key,
                    x=x,y=y,id=[as_scalar(o) for o in df.index],
                    extra={"tooltip": {"y_start": "", "y_end": " call"}},
                    **kwargs1)

        self.extra("scatter.onlyCircles", True)
        self.extra("showDistX", False)
        self.extra("showDistY", False)
        self.extra("tooltipContent", 
            """function(k,x,y,e,graph) {
                return '<p>'+e.point.id+'</p>';
            }""")
        self.extra("scatter.dispatch.on", 
                "'elementClick'", "function(e) {alert('hi')}")

class BarPlot(Plot):
    PLOT_TYPE = "discreteBar"

    def __init__(self, *args, show_values=True, **kwargs):
        super(BarPlot, self).__init__(*args, **kwargs)

        x = list(self.data.index)
        y = self.data.tolist()
        self.chart.add_serie(x=x, y=y)

        self.extra("showValues", show_values)
