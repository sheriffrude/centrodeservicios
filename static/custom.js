document.addEventListener('DOMContentLoaded', function () {
    // Obtener todos los enlaces en el menú de navegación principal
    var enlaces = document.querySelectorAll('.sidebar-menu .nav-link');

    // Iterar sobre cada enlace
    enlaces.forEach(function (enlace) {
        // Agregar un evento de clic a cada enlace
        enlace.addEventListener('click', function (event) {
            event.preventDefault(); // Evitar que el enlace redireccione
            cargarContenido(this); // Pasar el enlace al método cargarContenido
        });
    });
});

function cargarContenido(enlace) {
    // Obtener la URL de la que se debe cargar el contenido
    var url = enlace.getAttribute('href');

    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                // Insertar la respuesta en el contenedor especificado
                document.querySelector('.content-wrapper').innerHTML = xhr.responseText;

                // Ejecutar scripts dentro del nuevo contenido
                var scripts = document.querySelectorAll('.content-wrapper script');
                scripts.forEach(function (script) {
                    eval(script.innerHTML);
                });
            } else {
                console.error('Error al cargar el contenido:', xhr.status);
            }
        }
    };
    xhr.open('GET', url, true);
    xhr.send();
}


