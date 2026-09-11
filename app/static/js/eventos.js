/**
 * Alta de eventos, enviando JSON a la API (mismo patrón que clases.js y
 * catalogo_puntos.js: la validación real vive en el servidor).
 */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    const formulario = document.querySelector("#form-nuevo-evento");
    if (!formulario) return;

    const alerta = document.querySelector("#alerta-nuevo-evento");

    formulario.addEventListener("submit", async function (evento) {
      evento.preventDefault();
      if (!formulario.checkValidity()) {
        formulario.classList.add("was-validated");
        return;
      }

      const datos = Object.fromEntries(new FormData(formulario).entries());
      datos.alumno_id = Number(datos.alumno_id);
      datos.catalogo_punto_id = Number(datos.catalogo_punto_id);
      datos.jornada_id = Number(formulario.dataset.jornadaId);
      datos.nota_numerica = datos.nota_numerica ? Number(datos.nota_numerica) : null;
      if (!datos.comentario) datos.comentario = null;

      alerta.classList.add("d-none");

      try {
        const respuesta = await fetch(formulario.action, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(datos),
        });

        if (!respuesta.ok) {
          const error = await respuesta.json().catch(() => null);
          alerta.textContent = (error && error.detail) || "No se pudo registrar el evento.";
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
