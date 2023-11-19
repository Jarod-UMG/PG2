// Función para abrir el menú lateral
function openNav() {
    document.getElementById("mySidenav").style.right = "0";
    document.getElementById("main").style.marginRight = "250px";
    document.getElementById("menuBtn").style.display = "none"; // Oculta el botón de menú
}

// Función para cerrar el menú lateral
function closeNav() {
    document.getElementById("mySidenav").style.right = "-250px";
    document.getElementById("main").style.marginRight = "0";
    document.getElementById("menuBtn").style.display = "block"; // Muestra el botón de menú
}

// Eventos para el botón de menú y el menú lateral
document.getElementById("menuBtn").addEventListener("click", openNav);
document.getElementById("mySidenav").addEventListener("click", closeNav);

// Evento para cerrar el menú al hacer clic en el contenido principal
document.getElementById("main").addEventListener("click", closeNav);

// Evento para cerrar el menú al hacer clic en cualquier parte de la pantalla (fuera del menú)
window.addEventListener("click", function(event) {
    if (!event.target.matches("#menuBtn") && !event.target.matches(".sidenav a")) {
        closeNav();
    }
});
//--------------
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