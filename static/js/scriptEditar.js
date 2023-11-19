const inputImagen = document.getElementById('imagen');
const imgPreview = document.getElementById('preview');

inputImagen.addEventListener('change', () => {
    const file = inputImagen.files[0];
    const reader = new FileReader();
    reader.addEventListener('load', () => {
        imgPreview.src = reader.result;
    });
    reader.readAsDataURL(file);
});