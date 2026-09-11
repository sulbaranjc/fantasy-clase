/**
 * Alta de alumnos, enviando JSON a la API (mismo patrón que clases.js,
 * catalogo_puntos.js y eventos.js: la validación real vive en el servidor).
 */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    const formulario = document.querySelector("#form-nuevo-alumno");
    if (!formulario) return;

    const alerta = document.querySelector("#alerta-nuevo-alumno");

    formulario.addEventListener("submit", async function (evento) {
      evento.preventDefault();
      if (!formulario.checkValidity()) {
        formulario.classList.add("was-validated");
        return;
      }

      const datos = Object.fromEntries(new FormData(formulario).entries());
      alerta.classList.add("d-none");

      try {
        const respuesta = await fetch(formulario.action, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(datos),
        });

        if (!respuesta.ok) {
          const error = await respuesta.json().catch(() => null);
          alerta.textContent = (error && error.detail) || "No se pudo crear el alumno.";
          alerta.classList.remove("d-none");
          return;
        }

        window.location.reload();
      } catch (e) {
        alerta.textContent = "Error de conexión con el servidor.";
        alerta.classList.remove("d-none");
      }
    });
  });
})();
