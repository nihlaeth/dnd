// accordion collapse for non-panels
$(document).on('click', '[data-toggle=collapse][data-parent]', function(event) {
    var $dataParent = $(this).attr('data-parent');
    var $dataTarget = $(this).attr('data-target');
    $(
            '[data-toggle="collapse"][data-parent="' + 
            $dataParent + 
            '"][data-target!="' + 
            $dataTarget + 
            '"]').each(function(){

        $($(this).attr('data-target')).collapse("hide");
    });
    event.preventDefault();
});
