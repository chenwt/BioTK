$(function() {
    $(".typeahead").each(function(ix,value) {
        var o = $(this);
        var key = $(this).attr("key");

        var bh = new Bloodhound({
            datumTokenizer: 
                Bloodhound.tokenizers.obj.whitespace('name'),
            queryTokenizer: 
                Bloodhound.tokenizers.whitespace,
            limit: 10,
            prefetch: {
                url: "../../autocomplete/" + key
                /*
                filter: function(list) {
                    return $.map(list, function(c) { 
                        return c;
                    });
                }
                */
            }
        });

        bh.initialize();

        $(this).typeahead(
                {
                    hint: true,
                    highlight: true,
                    minLength: 1
                },
                {
                    name: 'tissue',
                    displayKey: 'name',
                    source: bh.ttAdapter()
                });
    });
});

/*
$(function() {
    //document.getElementById("quick-search").focus();

    // Show animated "Loading..." text for AJAX elements
    
    var i = 0;
    setInterval(function() {
        $('.loading').text("Loading data"+Array((++i % 4)+1).join("."));
    }, 500);
});
*/
