document.getElementById("contact-redirect-button").addEventListener("click", function() {
    document.getElementById("redirectMessage").style.display = "block";
    setTimeout(function() {
        document.getElementById("redirectMessage").style.display = "none";
        window.location.href = "tel:+1234567890";
    }, 2000); // Hide message and redirect after 5 seconds
});
