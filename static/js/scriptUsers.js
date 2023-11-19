//Funcion para mostrar la contraseña en el formulario para ingresar en la tabala usuarios
const togglePassword = document.querySelector('.toggle-password');
const passwordField = togglePassword.closest('.input-group').querySelector('input');
const showPasswordIcon = togglePassword.querySelector('.show-password-icon');

togglePassword.addEventListener('click', () => {
    if (passwordField.type === 'password') {
        passwordField.type = 'text';
        showPasswordIcon.classList.remove('fa-eye-slash');
        showPasswordIcon.classList.add('fa-eye');
    } else {
        passwordField.type = 'password';
        showPasswordIcon.classList.remove('fa-eye');
        showPasswordIcon.classList.add('fa-eye-slash');
    }
});

//Funcion para validar el correo electronico
const correoInput = document.getElementById('correo');
const correoError = document.getElementById('correo-error');

correoInput.addEventListener('input', () => {
    if (correoInput.validity.valid) {
        correoError.textContent = '';
    } else {
        mostrarErrorCorreo();
    }
});

function mostrarErrorCorreo() {
    if (correoInput.validity.valueMissing) {
        correoError.textContent = 'Debes ingresar un correo electrónico.';
    } else if (correoInput.validity.typeMismatch) {
        correoError.textContent = 'Ingresa un formato de correo electrónico válido.';
    }
};

// Obtener el elemento del mensaje de éxito
var mensajeExito = document.getElementById('mensaje-exito');

// Ocultar el mensaje después de 3000 milisegundos (3 segundos)
setTimeout(function() {
    mensajeExito.style.display = 'none';
}, 1000);

