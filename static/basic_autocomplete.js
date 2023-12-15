let search_box_value = ""
$('.basicAutoComplete').autoComplete(
  {
    minLength: 1,
    bootstrapVersion: '5',
    preventEnter: true,
  }
  );

$('.basicAutoComplete').on('change', function (evt, item) {
    let new_value = document.getElementById("id_members_to_invite").value
    arr = new_value.split(" ")
    if (arr.length > 1)
    {
      // Pop last element, as this is the query
      arr.pop()
      search_box_value = arr.join(" ")
      console.log(search_box_value)
    }
  });

$('.basicAutoComplete').on('autocomplete.select', function (evt, item) {

    let new_string = ""
    if (search_box_value == "")
    {
      new_string = item
    }
    else
    {
      new_string = search_box_value + " " + item
    }
    if (typeof item === 'string')
    {
      $('.basicAutoComplete').autoComplete('set', { value: new_string, text: new_string});
    }
    else
    {
      $('.basicAutoComplete').autoComplete('clear');
      search_box_value = ""
    }
  });
$('.dropdown-menu').css({'top': 'auto', 'left': 'auto'})