/**
 * Validación de formularios en el navegador (vanilla JS, sin librerías).
 *
 * Esto es solo una ayuda de experiencia de usuario: da feedback inmediato
 * antes de enviar el formulario. La validación real y definitiva ocurre
 * siempre en el servidor (Pydantic); nunca hay que confiar únicamente en
 * esta capa para garantizar la calidad del dato.
 *
 * Uso: añadir la clase "necesita-validacion" a cualquier <form> del
 * proyecto para activar este comportamiento (patrón estándar de
 * Bootstrap 5, aplicado aquí sin depender de su JS de formularios).
 */
(function () {
  "use strict";

  function activarValidacion(formulario) {
    formulario.addEventListener("submit", function (evento) {
      if (!formulario.checkValidity()) {
        evento.preventDefault();
        evento.stopPropagation();
      }
      formulario.classList.add("was-validated");
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    document
      .querySelectorAll("form.necesita-validacion")
      .forEach(activarValidacion);
  });
})();
