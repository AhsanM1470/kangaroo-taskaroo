var search_box_value = ""
var invite_search_box_value = ""

function setup()
{
  
  $('.basicAutoComplete').autoComplete(
    {
      minLength: 1,
      bootstrapVersion: '5',
      preventEnter: true,
    }
    );
  
  $('.basicAutoComplete').on('change', function updateSearchBox(){
  
      let new_value = document.getElementById("id_members_to_invite").value
      arr = new_value.split(" ")
      if (arr.length > 1)
      {
        // Pop last element, as this is the query
        arr.pop()
        search_box_value = arr.join(" ")
      }
    });
  
  $('.basicAutoComplete').on('autocomplete.select', function setAutocompleteValue (evt, item) {

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
        console.log(new_string)
        $('.basicAutoComplete').autoComplete('set', { value: new_string, text: new_string});
      }
      else
      {
        $('.basicAutoComplete').autoComplete('clear');
        search_box_value = ""
      }
    });
  
    $('.basicAutoCompleteInvite').autoComplete(
      {
        minLength: 1,
        bootstrapVersion: '5',
        preventEnter: true,
      }
      );
    
    $('.basicAutoCompleteInvite').on('change', function (evt, item,) {
        let new_value = document.getElementById("id_users_to_invite").value
        console.log(new_value)
        arr = new_value.split(" ")
        if (arr.length > 1)
        {
          // Pop last element, as this is the query
          arr.pop()
          invite_search_box_value = arr.join(" ")
          console.log(invite_search_box_value)
        }
      });
    
    
      
    $('.basicAutoCompleteInvite').on('autocomplete.select', function (evt, item) {
    
        let new_string = ""
        if (invite_search_box_value == "")
        {
          new_string = item
        }
        else
        {
          new_string = invite_search_box_value + " " + item
        }
        if (typeof item === 'string')
        {
          $('.basicAutoCompleteInvite').autoComplete('set', { value: new_string, text: new_string});
        }
        else
        {
          $('.basicAutoCompleteInvite').autoComplete('clear');
          invite_search_box_value = ""
        }
      });
  
  $('.dropdown-menu').css({'top': 'auto', 'left': 'auto'})
}
