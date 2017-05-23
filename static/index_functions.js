function confirm_show(verb_id) {
    // show a confirmation div
    $('#yes').attr('value',verb_id)
    $('#confirm_menu').css({"position": "fixed",
                        "top": "50%",
                        "left": "50%",
                        "transform": "translate(-50%,-50%)"})
    $('#confirm_menu').show()
}

function delete_verb() {
    // delete a verb and reload the page a second later
    $.post({
        url: $(location).attr('href'),
        data: {"delete":$('#yes').attr('value')},
        success: function () {
            setTimeout(function () {location.reload(true)}, 1000)
        },
        error: function () {
            $('#confirm_menu').hide()
            $('#message').html("Произошла ошибка. Свяжитесь с разработчиком - katgerasimenko@gmail.com.")
        }
    })
}

$(function(){
    // quick search in the verb list (as-you-type)
    $('#search_as_you_type').keyup(function(event){
        var term = $('#search_as_you_type').val().toLowerCase();
        $('.verb').parent().hide(); // hide all
        $('.verb:contains("' + term + '")').parent().show(); // toggle based on term
    });
 });