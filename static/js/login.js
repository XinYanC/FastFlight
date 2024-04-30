document.addEventListener('DOMContentLoaded', function() {
    var radioButtons = document.querySelectorAll('.radio-select input[type="radio"]');
    var listItems = document.querySelectorAll('.social-links li');

    // Add click event listeners to list items
    listItems.forEach(function(item, index) {
        item.addEventListener('click', function() {
            var radioId = item.querySelector('a').getAttribute('data-radio');
            var radio = document.getElementById(radioId);

            // Uncheck all radio buttons
            radioButtons.forEach(function(btn) {
                btn.checked = false;
            });

            // Check the corresponding radio button
            radio.checked = true;

            // Simulate change event on the radio button
            var event = new Event('change');
            radio.dispatchEvent(event);
        });
    });

    // Add change event listeners to radio buttons
    radioButtons.forEach(function(radioButton, index) {
        radioButton.addEventListener('change', function() {
            // Uncheck all radio buttons except the selected one
            radioButtons.forEach(function(btn, i) {
                if (i !== index) {
                    btn.checked = false;
                }
            });

            // Remove 'toggled_reg' class from all list items
            listItems.forEach(function(li) {
                li.classList.remove('toggled_reg');
            });

            // Add 'toggled_reg' class to the selected list item
            listItems[index].classList.add('toggled_reg');
        });
    });
});

document.addEventListener('DOMContentLoaded', function() {
    var listItems = document.querySelectorAll('.social-links li');

    listItems.forEach(function(item) {
        item.addEventListener('click', function() {

            // Remove 'toggled_reg' class from all list items and icons
            listItems.forEach(function(li) {
                li.classList.remove('toggled_reg');
                li.querySelector('i').classList.remove('toggled_reg');
            });

            // Activate 'toggled_reg' class for clicked list item and its icon
            item.classList.add('toggled_reg');
            item.querySelector('i').classList.add('toggled_reg');

            // Uncheck all radio buttons
            document.querySelectorAll('.radio-select input[type="radio"]').forEach(function(btn) {
                btn.checked = false;
            });

            // Check the corresponding radio button
            var radioId = item.id.replace("_tog", "");
            document.getElementById(radioId).checked = true;
        });
    });
});

