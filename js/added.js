document.getElementById("contact-redirect-button").addEventListener("click", function() {
    document.getElementById("redirectMessage").style.display = "block";
    setTimeout(function() {
        window.location.href = "tel:+1234567890";
    }, 2000); // Redirect after 2 seconds (adjust as needed)
});