$(document).on('submit', 'form[data-async]', function(event) {
    var $form = $(this);
    var $target = $($form.attr('data-target'));
    $.ajax({
        type: $form.attr('method'),
        url: $form.attr('action'),
        data: $form.serialize(),
        cache: false,
        success: function(data, status) {
            $.each(data,function(key,value){
                if(key == "close"){
                    if(data['close'] === true){
                        $form.closest(".collapse").collapse("hide");
                    }
                }else if(key == "errors"){
                    $target.html(data[key]);
                }else{
                    if('data' in data[key]){
                        $(key).html(data[key]['data']);
                    }
                    if('addClass' in data[key]){
                        for(i in data[key]['addClass']){
                            $(key).addClass(data[key]['addClass'][i]);
                        }
                    }
                    if('removeClass' in data[key]){
                        for(i in data[key]['removeClass']){
                            $(key).removeClass(data[key]['removeClass'][i]);
                        }
                    }
                    if('appendTable' in data[key]){
                        $(key + ' > tbody:last-child').append(data[key]['appendTable']);
                    }
                    if('collapse' in data[key]){
                        $(key).collapse(data[key]['collapse'])
                    }
                    if('activateTooltip' in data[key]){
                        $(key + ' [data-toggle="tooltip"]').tooltip();
                    }
                }
            });
        },
        error: function (result) {
            alert(result);
        }
    });
    event.preventDefault();
});

$(document).ready(function(){
    $('[data-toggle="tooltip"]').tooltip();
});
