$(document).on('click', '.collapse-icon', function(){
  var target = $(this).attr('href')
  $.ajax({
      url: $(target).data('src')})
    .done(function(data) {
      $(target).append(data)
    });
});
