//mensaje que aparece abajo que dice que las contraseñas no coinciden
function validarContrasena() {
    var contrasena = document.getElementById('contrasena').value;
    var confirmarContrasena = document.getElementById('confirmarContrasena').value;
    var mensajeError = document.getElementById('mensajeError');

    if (contrasena !== confirmarContrasena) {
        mensajeError.textContent = 'Las contraseñas no coinciden.';
    } else {
        mensajeError.textContent = ''; // Borra el mensaje de error si las contraseñas coinciden.
    }
}
//Función para ver la contraseña
$(document).ready(function() {
    $("#ver_contrasena").change(function() {
        if ($("#ver_contrasena").is(":checked")) {
            $("#contrasena").attr("type", "text");
            
        } else {
            $("#contrasena").attr("type", "password");
        }
    });
});
//Función para ver la confirmacion de contraseña
$(document).ready(function() {
    $("#verConfirmarContrasena").change(function() {
        if ($("#verConfirmarContrasena").is(":checked")) {
            $("#confirmarContrasena").attr("type", "text");
            
        } else {
            $("#confirmarContrasena").attr("type", "password");
        }
    });
});


