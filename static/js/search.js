document.addEventListener("DOMContentLoaded", function() {
    var sourceSearchInput = document.getElementById('sourceSearch');
    var destinationSearchInput = document.getElementById('destinationSearch');
    var suggestionsSourceContainer = document.getElementById('suggestionsSource');
    var suggestionsDestinationContainer = document.getElementById('suggestionsDestination');

    sourceSearchInput.addEventListener('input', function() {
        var searchQuery = this.value.trim();
        console.log("source input detected.");

        // Send an AJAX request to the server to get suggestions
        if (searchQuery !== '') {
            getSuggestions(searchQuery, 'source');
        } else {
            suggestionsSourceContainer.style.display = 'none';
        }
    });

    destinationSearchInput.addEventListener('input', function() {
        var searchQuery = this.value.trim();
        console.log(" destination input detected.");

        // Send an AJAX request to the server to get suggestions
        if (searchQuery !== '') {
            getSuggestions(searchQuery, 'destination');
        } else {
            suggestionsDestinationContainer.style.display = 'none';
        }
    });

    function getSuggestions(query, type) {
        $.ajax({
            url: '/get_airport_suggestions',
            method: 'POST',
            data: { searchQuery: query },
            success: function(response) {
                displaySuggestions(response, type);
                console.log("Suggestions found!");
            },
            error: function(xhr, status, error) {
                console.error('Error fetching suggestions:', error);
            }
        });
    }

    function displaySuggestions(suggestions, type) {
        var suggestionsContainer;
        if (type === 'source') {
            suggestionsContainer = suggestionsSourceContainer;
        } else if (type === 'destination') {
            suggestionsContainer = suggestionsDestinationContainer;
        }

        suggestionsContainer.innerHTML = '';
        suggestions.forEach(function(suggestion) {
            var suggestionElement = document.createElement('div');
            suggestionElement.classList.add('suggestion');
            suggestionElement.textContent = suggestion;
            suggestionElement.addEventListener('click', function() {
                if (type === 'source') {
                    sourceSearchInput.value = suggestion;
                    suggestionsSourceContainer.style.display = 'none';
                } else if (type === 'destination') {
                    destinationSearchInput.value = suggestion;
                    suggestionsDestinationContainer.style.display = 'none';
                }
            });
            suggestionsContainer.appendChild(suggestionElement);
        });

        if (suggestions.length > 0) {
            suggestionsContainer.style.display = 'block';
        } else {
            suggestionsContainer.style.display = 'none';
        }
    }

    // Close suggestions when clicking outside the search container
    document.addEventListener('click', function(event) {
        if (!event.target.matches('#sourceSearch') && !event.target.matches('#destinationSearch')) {
            suggestionsSourceContainer.style.display = 'none';
            suggestionsDestinationContainer.style.display = 'none';
        }
    });
});

// script.js

document.addEventListener("DOMContentLoaded", function() {
    const searchButton = document.getElementById("searchFlights");

    searchButton.addEventListener("click", function() {
        const source = document.getElementById("sourceSearch").value;
        const destination = document.getElementById("destinationSearch").value;
        const date = document.getElementById("return").value;

        // Send search query to Flask server
        fetch(`/search?source=${source}&destination=${destination}&date=${date}`)
            .then(response => response.json())
            .then(data => {
                // Redirect to search results page with the received data
                window.location.href = `/results?source=${source}&destination=${destination}&date=${date}`;
            })
            .catch(error => {
                console.error("Error:", error);
            });
    });
});




// document.addEventListener('DOMContentLoaded', function() {
//     // Get references to the input fields and suggestion containers
//     var sourceSearchInput = document.getElementById('sourceSearch');
//     var destinationSearchInput = document.getElementById('destinationSearch');
//     var suggestionsSourceContainer = document.getElementById('suggestionsSource');
//     var suggestionsDestinationContainer = document.getElementById('destinationSource');

//     // Log messages to verify if event listeners are triggered
//     console.log("sourceSearchInput:", sourceSearchInput);
//     console.log("destinationSearchInput:", destinationSearchInput);


//     // Attach event listeners to input fields
//     sourceSearchInput.addEventListener('input', function() {
//         var searchQuery = this.value.trim();
//         console.log("Source input detected.");

//         // Troubleshooting: Check if searchQuery is correctly obtained
//         console.log("Search query:", searchQuery);

//         // Send an AJAX request to the server to get suggestions
//         if (searchQuery !== '') {
//             getSuggestions(searchQuery, 'source');
//         } else {
//             suggestionsSourceContainer.style.display = 'none';
//         }
//     });

//     destinationSearchInput.addEventListener('input', function() {
//         var searchQuery = this.value.trim();
//         console.log("Destination input detected.");

//         // Troubleshooting: Check if searchQuery is correctly obtained
//         console.log("Search query:", searchQuery);

//         // Send an AJAX request to the server to get suggestions
//         if (searchQuery !== '') {
//             getSuggestions(searchQuery, 'destination');
//         } else {
//             suggestionsDestinationContainer.style.display = 'none';
//         }
//     });

//     // Function to retrieve suggestions from the server
//     function getSuggestions(query, type) {
//         // Placeholder for AJAX request
//     }
// });

