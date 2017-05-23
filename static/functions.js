function add(el) {
    // add a subblock:
    // insert an empty copy of a previous div
    // increment a counter in the field names (array index in the database)
    var last_div, new_div, new_div_content, level;
    last_div = $(el).prev();
    new_div = $(last_div).clone();
    level = $(new_div).attr('id');
    new_div_content = new_div.html();
    var increment = new RegExp(level+'\.([0-9]+)\.','g');
    var result;
    while ((result = increment.exec(new_div_content)) !== null) {
        new_div_content = new_div_content.replace(result[0],level+"."+String(Number(result[1])+1)+".")
    };
    new_div.html(new_div_content);
    $(new_div).find(":input").each(function() {
          this.value = ""
    });
    $(el).before(new_div)
}

function show_choices(button) {
    // show form with choices as checkboxes in the search mode
    var field = $(button).prev();
    var field_name = field.attr('name');
    var div_id = $(button).parent().attr('id');
    var div_to_show = document.getElementById(div_id+'_choose');
    $(div_to_show).find('form').attr('field_name',field_name);
    $(div_to_show).css({"background-color": "white",
                        "position": "fixed",
                        "top": "50%",
                        "left": "50%",
                        "transform": "translate(-50%,-50%)"});
    $(div_to_show).show()
}

function handle_choices(button) {
    // turn selected checkboxes into OR statements in the text field
    // overwrites previous field value
    var form = $(button).parent();
    var field_name = form.attr('field_name');
    var choices = $(form).serializeArray();
    var text_choices = '';
    for (c in choices) {
        text_choices += choices[c]['value'] + '|'
    };
    text_choices = text_choices.slice(0,-1);
    var field = document.getElementsByName(field_name);
    $(field).val('');
    $(field).val(text_choices);
    close_choices($(button).parent().next())
}

function close_choices(button) {
    // close div with checkboxes in the search mode
    var choice_div = $(button).parent();
    $(choice_div).hide();
    $(choice_div).find('form')[0].reset()
}

function show_block(button) {
    // show or hide a block or a subblock in the form
    var block, arrow;
    if ($(button).is('img')) {
        block = $(button).next();
        arrow = button
    };
    if ($(button).is('h2') || $(button).is('h3')) {
        block = $(button).next().next();
        arrow = $(button).next()
    };
    if ($(block).is(':visible')) {
        $(arrow).attr('src','/static/arrow_down.png')
    } else {
        $(arrow).attr('src','/static/arrow_up.png')
    };
    $(block).slideToggle()
    
}

function show_all() {
    // show all blocks and subblocks
    $ ('img').each(function (index, value) {
        $(this).attr('src','/static/arrow_up.png')
    });
    $("[class='block'],[class='subblock']").each(function (index, value) {
        $(this).slideDown()
    })
}

function hide_all() {
    // hide all blocks and subblocks
    $ ('img').each(function (index, value) {
        $(this).attr('src','/static/arrow_down.png')
    });
    $("[class='block'],[class='subblock']").each(function (index, value) {
        $(this).slideUp()
    })
}

function change_verb() {
    // send data to server, get a response and show it to the user on the same page
    var data = $('form').serialize();
    $.post({
        url: $(location).attr('href'),
        data: data,
        success: function () {
            $("#message").html("Изменения сохранены.")},
        error: function () {$("#message").html("Произошла ошибка. Свяжитесь с разработчиком - katgerasimenko@gmail.com.")}
   })
}