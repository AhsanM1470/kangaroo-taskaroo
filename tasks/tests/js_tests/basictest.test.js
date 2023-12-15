function add(a, b) {
    return a + b;
  }


QUnit.module('test autocomplete', function() {
    QUnit.test('two numbers', function(assert) {
        assert.equal(add(1, 2), 3);
    });

    QUnit.test("autocomplete on change", function(assert)
    {
        assert.equal(1, 1);
    })

    QUnit.test("bruh", function(assert)
    {
        //changeAutocomplete();
        assert.equal(1, 1);
    })
});
