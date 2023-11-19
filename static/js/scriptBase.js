// Obtener la hora actual del usuario
var hora = new Date().getHours();

// Obtener el elemento del DOM donde se mostrará el saludo
var saludoElement = document.getElementById('saludo');

// Definir los mensajes de saludo para cada período del día
var buenosDias = "¡Buenos días!";
var buenasTardes = "¡Buenas tardes!";
var buenasNoches = "¡Buenas noches!";

// Determinar el mensaje de saludo según la hora
var saludo;
if (hora >= 5 && hora < 12) {
    saludo = buenosDias;
} else if (hora >= 12 && hora < 18) {
    saludo = buenasTardes;
} else {
    saludo = buenasNoches;
}

// Mostrar el saludo en la página
saludoElement.textContent = saludo;