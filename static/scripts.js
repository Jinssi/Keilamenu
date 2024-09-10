document.addEventListener('DOMContentLoaded', function() {
    var cookiesButton = document.getElementById('cookies-button');
    var cookiesNote = document.getElementById('cookies-note');

    cookiesButton.addEventListener('click', function() {
        cookiesNote.style.display = 'none';
    });
});