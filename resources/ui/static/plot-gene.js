require(["jquery", "atlas"], function($, atlas) {

atlas.scatter("#chart", expressionData, 
    { xlabel: "Age (" + ageUnits +")",
      ylabel: "Expression Level (Z-Score)",
      onClick: function(e) { 
          window.open("/sample/" + e.point.id); 
      } 
    }
);

atlas.bar("#tissue-age-expression-correlation", tissueData,
    "Tissue", "Age Correlation",
    {
        ylabel: "Correlation (Pearson R)"
    });

atlas.bar("#tissue-mean-expression", tissueData,
    "Tissue", "Mean Expression",
    {
        ylabel: "Mean Expression (Z-Score)"
    });

});
