function generateFooterMessage() {
    var message = "© 2023 Emlyn O'Regan. All rights reserved. Created with ChatGPT.";
    return message;
}

var footerElement = document.getElementById("footer");
var message = generateFooterMessage();
footerElement.innerHTML = "<p>" + message + "</p>";