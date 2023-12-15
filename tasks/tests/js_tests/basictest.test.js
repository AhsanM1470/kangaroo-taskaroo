function add(a, b) {
    return a + b;
  }

QUnit.module('Autocomplete', {
    beforeEach: function() {
        setup() // Run the setup function from the autocomplete script
        search_box_value = ""
        invite_search_box_value = ""
    }});

    QUnit.test('Search_box_value should be blank if only one username', function(assert) {        
        document.getElementById("id_members_to_invite").value = "@johndoe";
        
        // Dispatch event
        let event = new Event('change');
        document.getElementById('id_members_to_invite').dispatchEvent(event);
  
        // Assert
        assert.equal(search_box_value, "", 'changeAutocomplete should not update search_box_value');
      });
      
      
      QUnit.test('updateSearchBox function should update search_box_value if more than one username to all usernames but the current one', function(assert) {

        document.getElementById("id_members_to_invite").value = "@johndoe @janed";
        
        // Dispatch event
        let event = new Event('change');
        document.getElementById('id_members_to_invite').dispatchEvent(event);
  
        // Assert
        assert.equal(search_box_value, "@johndoe", 'changeAutocomplete should update search_box_value to @johndoe');
      });
  
      QUnit.test('setAutoCompleteValue should update autoComplete input field correctly when search_box_value is empty', function(assert) {
        // Arrange
        $('.basicAutoComplete').autoComplete('clear'); // Reset autoComplete field
        document.getElementById("id_members_to_invite").value = "@joh";

        // Trigger the 'autocomplete.select' event using jQuery
        $('.basicAutoComplete').trigger('autocomplete.select', ['@johndoe']);
  
        // Assert
        assert.equal(document.getElementById('id_members_to_invite').value, "@johndoe", 'setAutoCompleteValue should update autoComplete');
      });

      QUnit.test('setAutoCompleteValue should update autoComplete input field correctly when search_box_value contains value', function(assert) {

        document.getElementById("id_members_to_invite").value = "@johndoe @janed";
        search_box_value = "@johndoe"

        // Trigger the 'autocomplete.select' event using jQuery
        $('.basicAutoComplete').trigger('autocomplete.select', ['@janedoe']);
  
        // Assert
        assert.equal(document.getElementById('id_members_to_invite').value, "@johndoe @janedoe", 'setAutoCompleteValue should update autoComplete with multiple values');
      });
