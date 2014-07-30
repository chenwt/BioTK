$(function() {
    document.getElementById("quick-search").focus();

    // Show animated "Loading..." text for AJAX elements
    var i = 0;
    setInterval(function() {
        $('.loading').text("Loading data"+Array((++i % 4)+1).join("."));
    }, 500);
});
