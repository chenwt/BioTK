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

$(function() {
    $("table.data-table").each(function() {
        var uuid = $(this).attr("uuid");
        $(this).dataTable({
            dom: 'lfrtipT',
            serverSide: true,
            ajax: {
                url: '/ajax/table',
                type: 'POST',
                data: function(d) {d.uuid = uuid;}
            },
            tableTools: {
                sSwfPath: 
                    "/bower/datatables-tabletools/swf/copy_csv_xls_pdf.swf",
                aButtons: [
                {
                    sExtends: "csv",
                    sButtonText: "Download CSV"
                }]
            }
        });
    });

    $("table.data-table").each(function() {
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
