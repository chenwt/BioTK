if (!String.prototype.format) {
    String.prototype.format = function() {
        var args = arguments;
        return this.replace(/{(\d+)}/g, function(match, number) { 
            return typeof args[number] != 'undefined'
            ? args[number]
            : match
            ;
        });
    };
}

/*
TableTools.BUTTONS.download = {
    "sAction": "text",
    "sTag": "default",
    "sFieldBoundary": "",
    "sFieldSeperator": "\t",
    "sNewLine": "<br>",
    "sToolTip": "",
    "sButtonClass": "DTTT_button_text",
    "sButtonClassHover": "DTTT_button_text_hover",
    "sButtonText": "Download",
    "mColumns": "all",
    "bHeader": true,
    "bFooter": true,
    "sDiv": "",
    "fnMouseover": null,
    "fnMouseout": null,
    "fnClick": function( nButton, oConfig ) {
      var oParams = this.s.dt.oApi._fnAjaxParameters( this.s.dt );
    var iframe = document.createElement('iframe');
    iframe.style.height = "0px";
    iframe.style.width = "0px";
    iframe.src = oConfig.sUrl+"?"+$.param(oParams);
    document.body.appendChild( iframe );
    },
    "fnSelect": null,
    "fnComplete": null,
    "fnInit": null
};
*/ 

$(document).ready(function() {
    $("table.data-table").each(function() {
        var uuid = $(this).attr("uuid");
        $(this).dataTable({
            dom: 'lfrtipT',
            serverSide: true,
            ajax: {
                url: '/api/table/' + uuid,
                type: 'POST'
            },
            tableTools: {
                /*
                aButtons: [
                {
                    sExtends: "download",
                    sButtonText: "Download CSV",
                    sUrl: "/api/table/" + uuid + "/csv"
                }, {
                    sExtends: "download",
                    sButtonText: "Download Excel",
                    sUrl: "/api/table/" + uuid + "/xls"
                }]
                */
            }
        });
    });
    $("table").each(function() {
        var linkFormat = $(this).attr("link_format");
        if (typeof linkFormat !== 'undefined' && linkFormat !== false) {
            $("tbody", this).on("click", "tr", function() {
                var args = [];
                $('td', this).each(function() {
                    args.push($(this).html());
                });
                var link = linkFormat.format.apply(linkFormat, args);
                window.location.href = link;
            });
        }
    });
});
