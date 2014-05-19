% setdefault("title", "GDMAP - Genomic Data Meta-Analysis Platform")
% setdefault("subtitle", "")
<html>
<head>
    <title>{{title}}</title>
    <link rel="stylesheet" type="text/css" href="/static/css/gdmap.css" />
    <link rel="stylesheet" type="text/css"
        href="/static/css/dataTables.tableTools.css" />
    <script type="text/javascript" language="javascript"
        src="//code.jquery.com/jquery-1.10.2.min.js"></script>
    <script type="text/javascript" language="javascript"
        src="//cdn.datatables.net/1.10.0/js/jquery.dataTables.min.js"></script>
    <script type="text/javascript" language="javascript"
        src="//cdn.datatables.net/tabletools/2.2.1/js/dataTables.tableTools.min.js">  
    </script>
    <script type="text/javascript" language="javascript">

$(document).ready(function() {
    $('.data-table').dataTable( {
        //dom: 'T<"clear"><"H"lf>rt<"F"ip>',
        dom: 'T<"clear">lfrtip',
        tableTools: {
            "aButtons": [
                "copy", 
                "csv", 
                {
                    "sExtends": "xls",
                    // Sets filename to page title + .xls
                    // "sFileName": "*.xls" 
                    "sFileName": "GDMAP.xls"
                }
            ],
            "sSwfPath": "/static/swf/copy_csv_xls_pdf.swf"
        }
    } );
} );

    </script>
</head>
<body>
    <div id="content">
    <div id="content-inner">
    <div id="header">
        <h2>
            <a href="/">GDMAP - Genomic Data Meta-Analysis Platform</a>
        </h2>
        <ul class="menu">
            <li><a href="/expression">Expression</a></li>
            <li><a href="/epigenomics">Epigenomics</a></li>
            <li><a href="/text">Text Mining</a></li>
            <li><a href="/about">About</a></li>
            <li><a href="/statistics">Statistics</a></li>
        </ul>
    </div>
    <br />
    <hr />
    <h3>{{subtitle}}</h3>

    {{!base}}
    </div>
    </div>
</body>
</html>
